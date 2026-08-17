"""FastAPI authentication library."""
from .core.logging_config import configure_logging, LogLevel, LogFormat
from .core.utils import normalize_username, normalize_email

__version__ = "0.1.3"

__all__ = [
    "configure_logging",
    "LogLevel",
    "LogFormat",

    "normalize_username",
    "normalize_email",

]
