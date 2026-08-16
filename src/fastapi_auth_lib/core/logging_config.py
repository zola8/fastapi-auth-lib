import logging
import logging.config
from enum import StrEnum


class LogFormat(StrEnum):
    DEV = "dev"
    PROD = "prod"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def configure_logging(log_format: LogFormat, log_level: LogLevel) -> None:
    dev_formatter = {
        "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    prod_formatter = {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
    }

    active_formatter = LogFormat.DEV if log_format == LogFormat.DEV else LogFormat.PROD

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            LogFormat.DEV: dev_formatter,
            LogFormat.PROD: prod_formatter,
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": active_formatter,
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn.access": {
                "level": LogLevel.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": LogLevel.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
