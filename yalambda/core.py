import inspect
import dataclass_factory
import json
import base64
from dataclasses import dataclass, field
from typing import (
    Any, Awaitable, Callable, Coroutine,
    Dict, List, Protocol, TypeVar, TypedDict, Union, final
)

from .async_utils import before_first_call


class Context(Protocol):
    function_name: str
    function_version: str
    memory_limit_in_mb: int
    request_id: str
    token: Any

    def get_remaining_time_in_millis(self) -> float: ...


@final
class Identity(TypedDict):
    sourceIp: str
    userAgent: str


@final
class RequestContext(TypedDict):
    identity: Identity
    httpMethod: str
    requestId: str
    requestTime: str  # CLF
    requestTimeEpoch: int


@final
class Event(TypedDict):
    httpMethod: str
    headers: Dict[str, str]
    multiValueHeaders: Dict[str, List[str]]
    queryStringParameters: Dict[str, str]
    multiValueQueryStringParameters: Dict[str, List[str]]
    requestContext: RequestContext
    body: str
    isBase64Encoded: bool


@dataclass
class YaRequest:
    http_method: str
    headers: Dict[str, List[str]]
    query_params: Dict[str, List[str]]
    ctx: Context
    request_ctx: RequestContext
    body: Union[str, bytes]

    @staticmethod
    def build(event: Event, ctx: Context) -> "YaRequest":
        if event["isBase64Encoded"]:
            body = base64.b64decode(event["body"])
        else:
            body = event["body"]

        return YaRequest(
            http_method=event["httpMethod"],
            headers=event["multiValueHeaders"],
            query_params=event["multiValueQueryStringParameters"],
            ctx=ctx,
            request_ctx=event["requestContext"],
            body=body
        )


@dataclass
class YaResponse:
    status_code: int
    body: Union[bytes, str, Dict[str, Any], List[Any]]
    headers: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.body, str):
            self._is_b64_encoded = False
        elif isinstance(self.body, bytes):
            self.body = base64.b64encode(self.body).decode("ascii")
            self._is_b64_encoded = True
        elif isinstance(self.body, (list, dict)):
            self.body = json.dumps(self.body)
            self._is_b64_encoded = False
        else:
            raise TypeError(
                "Expected body to be str, bytes, dict or list, got {!r}".format(type(self.body))
            )

    def to_json(self) -> Dict[str, Any]:
        return {
            "statusCode": self.status_code,
            "multiValueHeaders": self.headers,
            "body": self.body,
            "isBase64Encoded": self._is_b64_encoded,
        }


T = TypeVar("T")

_RawHandler = Callable[[Event, Context], Coroutine[Any, Any, Dict[str, Any]]]
_YaHandler = Union[
    Callable[[YaRequest], Awaitable[YaResponse]],
    Callable[[T], Awaitable[YaResponse]],
    Callable[[T, YaRequest], Awaitable[YaResponse]],
]

_Init =  Callable[[], Awaitable[Any]]


async def _default_init():
    return None


def _parse_request(
    request: YaRequest,
    handler: Callable,
    df: dataclass_factory.Factory
):
    signature = inspect.signature(handler)
    params = list(signature.parameters.values())

    if len(params) not in (1, 2):
        raise AssertionError("Handler should have 1 or 2 parameters, got {}".format(len(params)))

    for param in params:
        if param.annotation in (param.empty, YaRequest):
            yield request
        else:
            body_json = json.loads(request.body)
            yield df.load(body_json, param.annotation)


_default_factory = dataclass_factory.Factory(debug_path=True)


def function(
    init: _Init = _default_init,
    df: dataclass_factory.Factory = _default_factory,
) -> Callable[[_YaHandler[T]], _RawHandler]:
    def _decorator(ya_handler: _YaHandler[T]) -> _RawHandler:
        @before_first_call(init)
        async def handler(event: Event, context: Context) -> Dict[str, Any]:
            req = YaRequest.build(event, context)
            try:
                args = list(_parse_request(req, ya_handler, df))
            except (ValueError, TypeError) as e:
                resp = YaResponse(400, "\n".join(map(str, e.args)))
            else:
                resp = await ya_handler(*args)
            return resp.to_json()
        return handler
    return _decorator
