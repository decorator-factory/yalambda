import json
from abc import ABC, abstractmethod
from typing import Callable,  Iterable, Tuple, Union

from dataclass_factory.factory import Factory

from .core import YaRequest, YaResponse, _YaHandler, run, _default_factory, _default_init, _Init, function


class When(ABC):
    @abstractmethod
    async def execute(self, req: YaRequest, df: Factory) -> Tuple[bool, YaResponse]:
        """
        If the condition matches, returns (True, response)
        If the condition matches, returns (False, response_with_reason)
        """

    def __or__(self, other: "When") -> "When":
        return WhenOr([self, other])


class Always(When):
    def __init__(self, ya_handler: _YaHandler):
        self.ya_handler = ya_handler

    async def execute(self, req: YaRequest, df: Factory) -> Tuple[bool, YaResponse]:
        return True, await run(self.ya_handler, req, df)


class WhenPredicate(When):
    def __init__(self, pred: Callable[[YaRequest], bool], then: When, name: str):
        self.pred = pred
        self.then = then
        self.name = name

    async def execute(self, req: YaRequest, df: Factory) -> Tuple[bool, YaResponse]:
        if not self.pred(req):
            return False, YaResponse(400, {"expected": self.name})

        return await self.then.execute(req, df)


class WhenMethodIs(When):
    def __init__(self, method: str, then: When):
        self.method = method
        self.then = then

    async def execute(self, req: YaRequest, df: Factory) -> Tuple[bool, YaResponse]:
        if req.http_method.upper() != self.method.upper():
            return False, YaResponse(
                405,
                {
                    "expected": {"method": self.method.upper()},
                    "got": {"method": req.http_method.upper()},
                }
            )
        return await self.then.execute(req, df)


class WhenHeaderIs(When):
    def __init__(self, header: str, value: str, then: When):
        self.header = header
        self.value = value
        self.then = then

    async def execute(self, req: YaRequest, df: Factory) -> Tuple[bool, YaResponse]:
        values = req.headers.getall(self.header.lower(), [])
        if self.value not in values:
            return False, YaResponse(
                400,
                {"expected": {"header": self.header.lower(), "value": self.value}, "got": values}
            )
        return await self.then.execute(req, df)


class WhenOr(When):
    def __init__(self, options: Iterable[When]):
        self.options = list(options)

    async def execute(self, req: YaRequest, df: Factory) -> Tuple[bool, YaResponse]:
        failures = []
        for option in self.options:
            ok, resp = await option.execute(req, df)
            if ok:
                return True, resp
            failures.append(resp.body)

        return False, YaResponse(400, failures)


Fn = Union[_YaHandler, When]


def _whenify(fn: Fn) -> When:
    if isinstance(fn, When):
        return fn
    return Always(fn)


def header_is(header: str, value: str, handler: Fn) -> When:
    return WhenHeaderIs(header, value, _whenify(handler))


def method_is(method: str, handler: Fn) -> When:
    return WhenMethodIs(method, _whenify(handler))


def condition(pred: Callable[[YaRequest], bool], name: str, handler: Fn) -> When:
    return WhenPredicate(pred, _whenify(handler), name)


def dispatch(
    *rules: When,
    init: _Init = _default_init,
    df: Factory = _default_factory,
    on_fail: Callable[[YaResponse], YaResponse] = lambda resp: resp,
):
    when = WhenOr(rules)

    @function(init)
    async def handler(req: YaRequest) -> YaResponse:
        ok, resp = await when.execute(req, df)
        if not ok:
            return on_fail(resp)
        return resp

    return handler
