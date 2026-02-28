import dataclasses
import enum
import os
import time
from typing import Any
from typing import Dict
from zoneinfo import ZoneInfo

import package
from package.config import Config


class FixedZone(Config):
    name: str = dataclasses.field(default="CST")
    offset: int = dataclasses.field(default=28800)  # 8*3600


class TimeZone(Config):
    name: str = dataclasses.field(default="Asia/Shanghai")
    fixed_zone: FixedZone = dataclasses.field(default_factory=FixedZone)

    def __post_init__(self):
        # set timezone
        os.environ.setdefault("TZ", self.name)
        time.tzset()

    @property
    def info(self):
        return ZoneInfo(self.name)


class ApplicationMode(enum.Enum):
    DEBUG = "debug"
    PROD = "prod"


class Application(Config):
    name: str
    mode: ApplicationMode = dataclasses.field(default=ApplicationMode.DEBUG)
    secret: str
    time_zone: TimeZone
    logger: Dict[str, Any]

    def __post_init__(self):
        package.logger.config(self.logger)

    @property
    def is_debug(self):
        return self.mode == ApplicationMode.DEBUG

    @property
    def is_prod(self):
        return self.mode == ApplicationMode.PROD
