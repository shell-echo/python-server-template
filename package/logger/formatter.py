import copy
import logging

from package.logger.color import AnsiColor

LOGGER_LEVEL_COLORS = {
    "DEBUG": AnsiColor.Text.BLUE,
    "INFO": AnsiColor.Text.GREEN,
    "WARNING": AnsiColor.Text.YELLOW,
    "ERROR": AnsiColor.Text.RED,
    "CRITICAL": AnsiColor.Text.PURPLE,
}


LOGGER_LEVELNAME_MIN_LENGTH = 8


class Formatter(logging.Formatter):

    def __format_levelname__(self, levelname: str) -> str:
        return f"{levelname.center(LOGGER_LEVELNAME_MIN_LENGTH)}"

    def format(self, record: logging.LogRecord) -> str:
        record.levelname = self.__format_levelname__(levelname=record.levelname)
        return super().format(record)


class ConsoleFormatter(Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record_copy = copy.copy(record)
        levelname = record_copy.levelname
        if levelname in LOGGER_LEVEL_COLORS:
            levelname_color = AnsiColor.color_str(
                value=self.__format_levelname__(levelname=levelname),
                color=LOGGER_LEVEL_COLORS[levelname],
            )
            record_copy.levelname = levelname_color
        return super().format(record_copy)
