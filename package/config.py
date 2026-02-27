import tomllib
from pathlib import Path
from typing import Final
from typing import cast

from package.command import CommandContext
from package.command import CommandException
from package.command import CommandOption
from package.command import get_current_context

CONFIG_ENV_VAR: Final = "CONFIG_FILE_PATH"
_CONFIG_FILE_PATH_KEY: Final = "config_file_path"
_ConfigContext = dict[str, Path]


def normalize_config_file_path(_: CommandContext, __: CommandOption, value: Path | None) -> Path | None:
    if value is None:
        return None

    path = value.expanduser().resolve()
    if path.suffix.lower() != ".toml":
        raise CommandException(f"Config file must be a TOML file (*.toml): {path}")

    try:
        with path.open("rb") as file:
            tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise CommandException(f"Config file is not valid TOML: {path}") from exc

    return path


def set_config_file_path(ctx: CommandContext, config_file_path: Path | None) -> None:
    context = cast(_ConfigContext, ctx.ensure_object(dict))
    if config_file_path is None:
        context.pop(_CONFIG_FILE_PATH_KEY, None)
        return
    context[_CONFIG_FILE_PATH_KEY] = config_file_path


def get_config_file_path() -> Path | None:
    ctx = get_current_context(silent=True)
    if ctx is None:
        return None

    obj = ctx.obj
    if not isinstance(obj, dict):
        return None

    context = cast(_ConfigContext, obj)
    config_file_path = context.get(_CONFIG_FILE_PATH_KEY)
    if isinstance(config_file_path, Path):
        return config_file_path
    return None
