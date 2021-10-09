import base64
from datetime import datetime
import time
import sys
import importlib
from dataclasses import dataclass
from collections import defaultdict
from typing import Any, Dict, List, NoReturn, Tuple

from multidict import CIMultiDict

try:
    from aiohttp import web
except ImportError:
    sys.stderr.write("You need to install the `aiohttp` package to run this\n")
    sys.exit(1)

from yalambda.core import _RawHandler, Context, Event


if len(sys.argv) != 2:
    sys.stderr.write("Usage: python -m yalambda <your.module.name>\n")
    sys.exit(1)

module_name = sys.argv[1]


# try:
module = importlib.import_module(module_name)
# except ImportError:
#     sys.stderr.write("Cannot find module {}\n".format(module_name))
#     sys.exit(1)


entrypoint: _RawHandler = module.handler  # type: ignore


@dataclass
class FakeContext(Context):
    function_name: str
    function_version: str
    memory_limit_in_mb: int
    request_id: str
    time_limit: float

    def __post_init__(self):
        self._start_time = time.time()

    @property
    def token(self) -> Any:
        raise NotImplementedError("`token` isn't supported in the fake yet")

    def get_remaining_time_in_millis(self) -> float:
        return 1000 * (time.time() - self._start_time)


def format_clf_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%d/%b/%Y:%I:%M:%S %z")


_SingleAndMultiValued = Tuple[
    Dict[str, str],
    Dict[str, List[str]]
]


class App:
    def __init__(self, handler: _RawHandler):
        self.handler = handler
        self._counter = 0

    def _request_id(self) -> str:
        return "{:08x}".format(self._counter)

    @staticmethod
    def _get_headers(request: web.Request) -> _SingleAndMultiValued:
        headers: Dict[str, List[str]] = defaultdict(list)
        for name, value in request.headers.items():
            headers[name].append(value)
        singles = {name: values[0] for name, values in headers.items() if len(values) == 1}
        return singles, headers

    @staticmethod
    def _get_query_params(request: web.Request) -> _SingleAndMultiValued:
        params: Dict[str, List[str]] = defaultdict(list)
        for name, value in request.query.items():
            params[name].append(value)
        singles = {name: values[0] for name, values in params.items() if len(values) == 1}
        return singles, params

    def _prepare_context(self) -> Context:
        return FakeContext(
            function_name="fake-function",
            function_version="abcdef42",
            memory_limit_in_mb=128,
            request_id=self._request_id(),
            time_limit=5.0
        )

    async def _prepare_event(self, request: web.Request) -> Event:
        single_headers, headers = self._get_headers(request)
        single_params, params = self._get_query_params(request)

        raw_body = await request.read()
        try:
            body = raw_body.decode("utf-8")
            is_base64 = False
        except UnicodeDecodeError:
            body = base64.b64encode(raw_body).decode("ascii")
            is_base64 = True

        return {
            "httpMethod": request.method.upper(),
            "headers": single_headers,
            "multiValueHeaders": headers,
            "queryStringParameters": single_params,
            "multiValueQueryStringParameters": params,
            "body": body,
            "isBase64Encoded": is_base64,
            "requestContext": {
                "identity": {
                    "sourceIp": "127.0.0.1",
                    "userAgent": "Yalambda",
                },
                "httpMethod": request.method.upper(),
                "requestId": str(self._counter),
                "requestTime": format_clf_timestamp(time.time()),
                "requestTimeEpoch": int(time.time()),
            },
        }

    async def execute_request(self, request: web.Request) -> web.Response:
        self._counter += 1
        ctx = self._prepare_context()
        event = await self._prepare_event(request)
        response = await self.handler(event, ctx)

        if response["isBase64Encoded"]:
            body = base64.b64decode(response["body"])
        else:
            body = str(response["body"])

        headers = CIMultiDict(response["multiValueHeaders"].items())

        return web.Response(
            body=body,
            status=response["statusCode"],
            headers=headers
        )

    def run(self) -> NoReturn:
        app = web.Application()
        app.router.add_route("*", r"/{path:.*}", self.execute_request)
        web.run_app(app, port=55710)
        assert False


App(entrypoint).run()