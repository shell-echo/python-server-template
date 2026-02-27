from typing import Any
from typing import Protocol
from typing import cast

import IPython

import package


class _EmbedFunc(Protocol):
    def __call__(self, *, header: str = "", compile_flags: Any | None = None, **kwargs: Any) -> None: ...


@package.command.command(name="shell", help="Start interactive Python shell")
def command() -> None:
    embed = cast(_EmbedFunc, getattr(IPython, "embed"))
    embed(using="asyncio")
