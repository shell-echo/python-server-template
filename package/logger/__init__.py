import logging.config
import os
from typing import Any
from typing import Dict
from typing import cast


def config(config: Dict[str, Any]) -> None:
    handlers = config.get("handlers", {})
    if isinstance(handlers, dict):
        for handler in cast(Dict[str, Dict[str, Any]], handlers).values():
            filename = handler.get("filename", "")
            if not filename:
                continue
            log_file_dir = os.path.dirname(filename)
            if not os.path.exists(log_file_dir):
                os.makedirs(log_file_dir)

    logging.config.dictConfig(config=config)
