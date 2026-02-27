import importlib
import inspect
from collections.abc import Awaitable
from collections.abc import Callable
from types import ModuleType
from typing import Any
from typing import cast

import click

import package
from package.command import CommandException

SyncScriptFunc = Callable[[], Any]
AsyncScriptFunc = Callable[[], Awaitable[Any]]
ScriptFunc = SyncScriptFunc | AsyncScriptFunc


def unwrap_decorators(func: Any) -> Any:
    return inspect.unwrap(func)


@package.command.command(
    name="script",
    help="Run a function from a Python module under the script package. Supports both sync and async functions.",
)
@package.command.option(
    "-m",
    "--module",
    type=click.STRING,
    required=True,
    help="Module path under script.",
)
@package.command.argument("function_name", type=click.STRING, required=False, metavar="FUNCTION_NAME")
async def command(module: str, function_name: str | None) -> None:
    if not module.startswith("script.") and module != "script":
        module = "script." + module

    try:
        import_module: ModuleType = importlib.import_module(module)
    except Exception as exc:
        raise CommandException(f"Failed to import module '{module}': {exc}") from exc

    func_map: dict[str, ScriptFunc] = {}
    for name, obj in inspect.getmembers(import_module):
        if name.startswith("__") or name.endswith("__"):
            continue
        if not inspect.isfunction(obj):
            continue

        origin_func = unwrap_decorators(func=obj)
        if inspect.getmodule(origin_func) == import_module:
            func_map[name] = cast(ScriptFunc, obj)

    target_name = function_name or "main"
    func = func_map.get(target_name)
    if func is None:
        available = ", ".join(sorted(func_map.keys())) or "<none>"
        raise CommandException(f"Function '{target_name}' not found in '{module}'. Available: {available}")

    if inspect.iscoroutinefunction(func):
        await cast(AsyncScriptFunc, func)()
    else:
        cast(SyncScriptFunc, func)()
