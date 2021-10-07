import asyncio
from functools import wraps
from typing import Awaitable, Callable, TypeVar, Union


Fn = TypeVar("Fn", bound=Callable[..., Awaitable])


def before_first_call(init: Callable[[], Awaitable]) -> Callable[[Fn], Fn]:
    def _decorator(fn: Fn) -> Fn:
        initialized: Union[bool, asyncio.Event] = False
        # If another call happens while `init()` is still running, we want to
        # wait for it and not start a new coroutine

        @wraps(fn)
        async def _new_fn(*args, **kwargs):
            nonlocal initialized
            if initialized is False:
                e = initialized = asyncio.Event()
                await init()
                e.set()
                initialized = True
            elif initialized is True:
                pass
            else:
                await initialized.wait()

            return await fn(*args, **kwargs)
        return _new_fn  # type: ignore
    return _decorator
