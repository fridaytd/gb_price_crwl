import logging

from ._config import Config

## Seting logger
logger = logging.getLogger(name=__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formater = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s :: %(message)s"
)
handler.setFormatter(formater)
logger.addHandler(handler)


config = Config.from_env()


__all__ = ["config", "logger"]
