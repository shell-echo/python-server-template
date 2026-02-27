from pathlib import Path

import package
from command import echo
from command import script
from command import shell
from package.command import CommandContext
from package.command import CommandPath
from package.config import CONFIG_ENV_VAR
from package.config import normalize_config_file_path
from package.config import set_config_file_path


@package.command.group()
@package.command.option(
    "--config",
    "config_file_path",
    type=CommandPath(exists=True, dir_okay=False, readable=True, path_type=Path),
    envvar=CONFIG_ENV_VAR,
    callback=normalize_config_file_path,
    help=f"Global config file path. You can also set it via {CONFIG_ENV_VAR}.",
    show_envvar=True,
)
@package.command.pass_context
def command(ctx: CommandContext, config_file_path: Path | None) -> None:
    set_config_file_path(ctx, config_file_path)


command.add_command(echo.command)
command.add_command(shell.command)
command.add_command(script.command)
