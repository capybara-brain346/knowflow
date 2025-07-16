import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from src.core.config import settings


class CustomFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[0;36m",
        "INFO": "\033[0;32m",
        "WARNING": "\033[0;33m",
        "ERROR": "\033[0;31m",
        "CRITICAL": "\033[0;35m",
        "RESET": "\033[0m",
    }

    def format(self, record):
        if hasattr(record, "color"):
            record.color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        else:
            record.color = self.COLORS["RESET"]
        return super().format(record)


def setup_logger(
    name: str = settings.PROJECT_NAME,
    log_file: Optional[str] = settings.LOG_FILE,
    level: int = getattr(logging, settings.LOG_LEVEL.upper()),
    rotation: str = settings.LOG_ROTATION,
    retention: int = settings.LOG_RETENTION,
    format_string: str = settings.LOG_FORMAT,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    colored_format_string = "%(color)s" + format_string + "%(color)s"
    console_formatter = CustomFormatter(colored_format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        if rotation == "midnight":
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file, when="midnight", interval=1, backupCount=retention
            )
        else:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10_000_000,
                backupCount=retention,
            )

        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logger.propagate = False

    return logger


logger = setup_logger()
