from pathlib import Path

import package
from command import echo
from command import script
from command import shell
from internal import config
from package.command import CommandPath
from package.config import CONFIG_ENV_VAR
from package.config import DEFAULT_CONFIG_FILE_PATH
from package.config import normalize_config_file_path


@package.command.group(
    context_settings={
        "terminal_width": 128,
        "max_content_width": 128,
        "help_option_names": ["-h", "--help"],
    }
)
@package.command.option(
    "-c",
    "--config",
    "config_file_path",
    type=CommandPath(exists=True, dir_okay=False, readable=True, path_type=Path),
    default=DEFAULT_CONFIG_FILE_PATH,
    envvar=CONFIG_ENV_VAR,
    callback=normalize_config_file_path,
    help=f"Set config file path. [Env: {CONFIG_ENV_VAR}][Default: {DEFAULT_CONFIG_FILE_PATH}]",
)
def command(config_file_path: Path | None) -> None:
    config.load(config_file_path=config_file_path)


command.add_command(echo.command)
command.add_command(shell.command)
command.add_command(script.command)
