from __future__ import annotations

from pathlib import Path

import loguru
from loguru import logger

from ferros.core.utils import get_settings

loggers: dict[str, loguru.Logger] = {}


def get_logger(name: str, file_prefix: str = "app.log") -> loguru.Logger:
    """
    Get a logger instance with the specified settings.

    Args:
        name (str): The name of the logger.
        file_prefix (str): The prefix for the log file name.
    Returns:
        logger: A logger instance configured with the provided settings.
    """
    global loggers
    if name in loggers:
        return loggers[name]
    settings = get_settings()
    file_name = f"{settings.logging.root_dir}/{file_prefix}.log"
    Path(settings.logging.root_dir).mkdir(parents=True, exist_ok=True)
    Path(file_name).touch(exist_ok=True)
    logger.remove()

    logger.add(
        file_name,
        mode="a",
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression=settings.logging.compression,
    )
    logger.bind(name=name)
    loggers[name] = logger
    return logger
