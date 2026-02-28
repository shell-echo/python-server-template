import package
from internal import config


@package.command.command(name="echo", help="......")
def command() -> None:
    print("echo.")
    print(config.application.name)
