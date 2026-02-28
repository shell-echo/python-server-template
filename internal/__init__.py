from pathlib import Path
from typing import Any

from internal.config import Config


class ConfigProxy:
    def __init__(self) -> None:
        self._config: Config | None = None

    def load(self, config_file_path: Path | None = None) -> Config:
        self._config = Config.load(config_file_path=config_file_path)
        return self._config

    def _require_loaded_config(self) -> Config:
        if self._config is None:
            raise RuntimeError("Config is not loaded. Call 'config.load(...)' first.")
        return self._config

    def __getattr__(self, name: str) -> Any:
        return getattr(self._require_loaded_config(), name)


config = ConfigProxy()

__all__ = ["config"]
