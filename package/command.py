import asyncio
import functools
import inspect
from collections.abc import Callable
from collections.abc import Coroutine
from typing import Any
from typing import TypeVar
from typing import cast
from typing import overload

from click import ClickException as CommandException
from click import Command
from click import Context as CommandContext
from click import Option as CommandOption
from click import Path as CommandPath
from click import argument
from click import command as click_command
from click import echo
from click import get_current_context
from click import group
from click import option
from click import pass_context

CommandFunc = Callable[..., Any]
AsyncCommandFunc = Callable[..., Coroutine[Any, Any, Any]]
CmdType = TypeVar("CmdType", bound=Command)


@overload
def command(name: CommandFunc) -> Command: ...


@overload
def command(name: str | None, cls: type[CmdType], **attrs: Any) -> Callable[[CommandFunc], CmdType]: ...


@overload
def command(name: None = None, *, cls: type[CmdType], **attrs: Any) -> Callable[[CommandFunc], CmdType]: ...


@overload
def command(name: str | None = ..., cls: None = None, **attrs: Any) -> Callable[[CommandFunc], Command]: ...


def command(
    name: str | CommandFunc | None = None,
    cls: type[CmdType] | None = None,
    **attrs: Any,
) -> Command | Callable[[CommandFunc], Command | CmdType]:
    def run(callback: CommandFunc | AsyncCommandFunc) -> CommandFunc:
        if not inspect.iscoroutinefunction(callback):
            return cast(CommandFunc, callback)

        async_callback = cast(AsyncCommandFunc, callback)

        @functools.wraps(async_callback)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                pass
            else:
                raise RuntimeError("Async click command cannot run inside an active event loop.")

            return asyncio.run(async_callback(*args, **kwargs))

        return wrapper

    callback: CommandFunc | None = None

    if callable(name):
        callback = name
        name = None
        assert cls is None, "Use 'command(cls=cls)(callable)' to specify a class."
        assert not attrs, "Use 'command(**kwargs)(callable)' to provide arguments."

    if cls is None:
        cls = cast(type[CmdType], Command)

    decorator = click_command(name=name, cls=cls, **attrs)

    def wrapped(func: CommandFunc | AsyncCommandFunc) -> Command | CmdType:
        return decorator(run(func))

    if callback is not None:
        return wrapped(callback)

    return wrapped


__all__ = [
    "CommandException",
    "argument",
    "command",
    "echo",
    "group",
    "option",
    "CommandContext",
    "get_current_context",
    "CommandOption",
    "CommandPath",
    "pass_context",
]
