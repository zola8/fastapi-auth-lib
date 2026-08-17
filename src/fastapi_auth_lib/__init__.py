"""FastAPI authentication library."""

from .api.schemas.requests import (
    RegisterWithPasswordRequest,
    LoginWithPasswordRequest,
    UserUpdateRequest,
    PasswordChangeRequest,
    UserSelfDeleteRequest
)
from .core.logging_config import configure_logging, LogLevel, LogFormat
from .core.utils import normalize_username, normalize_email

__version__ = "0.1.3"

__all__ = [
    "configure_logging",
    "LogLevel",
    "LogFormat",

    "normalize_username",
    "normalize_email",

    "RegisterWithPasswordRequest",
    "LoginWithPasswordRequest",
    "UserUpdateRequest",
    "PasswordChangeRequest",
    "UserSelfDeleteRequest",

]
