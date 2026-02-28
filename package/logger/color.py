import enum
from typing import Any


class ColorEnum(enum.Enum):
    def __str__(self):
        return self.value


class AnsiColor:
    RESET = "\033[0m"

    class Text(ColorEnum):
        BLACK = "\033[30m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        PURPLE = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"

    @classmethod
    def color_str(cls, value: Any, color: Text) -> str:
        return f"{color}{value}{cls.RESET}"

    class Style(ColorEnum):
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        REVERSE = "\033[7m"
        HIDDEN = "\033[8m"

    class Background(ColorEnum):
        BLACK = "\033[40m"
        RED = "\033[41m"
        GREEN = "\033[42m"
        YELLOW = "\033[43m"
        BLUE = "\033[44m"
        PURPLE = "\033[45m"
        CYAN = "\033[46m"
        WHITE = "\033[47m"
