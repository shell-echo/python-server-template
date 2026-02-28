import package
from internal.config.application import Application


class Config(package.config.Config):
    application: Application
