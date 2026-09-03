from datetime import datetime, timezone
from typing import Any


def _now(tz=timezone.utc) -> datetime:
    """
    Return the current datetime in the specified timezone.
    """
    return datetime.now(tz)


def normalize_email(value: Any) -> Any:
    """
    Normalize an email address by stripping whitespace and converting to lowercase.
    """
    if value is None or not isinstance(value, str):
        return value

    return value.strip().lower()


def normalize_username(value: Any) -> Any:
    """
    Normalize a username by stripping leading/trailing whitespace.
    """
    if value is None or not isinstance(value, str):
        return value

    return value.strip()
