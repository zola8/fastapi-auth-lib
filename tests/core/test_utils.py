from datetime import datetime
from datetime import timedelta
from datetime import timezone

from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.core.utils import normalize_username


class TestNormalizeEmail:
    """Tests for normalize_email function."""

    def test_none_returns_none(self):
        """None input should be returned unchanged."""
        assert normalize_email(None) is None

    def test_non_string_returns_unchanged(self):
        """Non-string values should be returned as is."""
        for value in [42, 3.14, [], {}, object()]:
            assert normalize_email(value) is value

    def test_strips_whitespace(self):
        """Leading/trailing spaces should be removed."""
        assert normalize_email("  user@example.com  ") == "user@example.com"
        assert normalize_email("\tuser@example.com\n") == "user@example.com"

    def test_lowercases(self):
        """Uppercase characters should be converted to lowercase."""
        assert normalize_email("USER@EXAMPLE.COM") == "user@example.com"
        assert normalize_email("User@Example.Com") == "user@example.com"

    def test_empty_string(self):
        """Empty string should remain empty after strip."""
        assert normalize_email("") == ""

    def test_only_whitespace(self):
        """Whitespace-only string becomes empty string."""
        assert normalize_email("   ") == ""

    def test_mixed_case_and_spaces(self):
        """Should strip and lowercase in one pass."""
        assert normalize_email("  User@Example.COM  ") == "user@example.com"


class TestNormalizeUsername:
    """Tests for normalize_username function."""

    def test_none_returns_none(self):
        assert normalize_username(None) is None

    def test_non_string_returns_unchanged(self):
        for value in [1, True, None, ["a"]]:
            assert normalize_username(value) is value

    def test_strips_whitespace(self):
        assert normalize_username("  john_doe  ") == "john_doe"
        assert normalize_username("\tjohn_doe\n") == "john_doe"

    def test_does_not_lowercase(self):
        """Username should keep original case."""
        assert normalize_username("John_Doe") == "John_Doe"
        assert normalize_username("  John_Doe  ") == "John_Doe"

    def test_empty_string(self):
        assert normalize_username("") == ""

    def test_only_whitespace(self):
        assert normalize_username("   ") == ""


class TestNow:
    """Tests for _now function."""

    def test_returns_datetime_with_utc(self):
        """Should return datetime with UTC timezone by default."""
        result = _now()
        assert isinstance(result, datetime)
        assert result.tzinfo is timezone.utc

    def test_accepts_custom_timezone(self):
        """Should accept a custom timezone object."""
        custom_tz = timezone(timedelta(hours=5, minutes=30))
        result = _now(tz=custom_tz)
        assert result.tzinfo is custom_tz

    def test_returns_close_to_current_time(self):
        """Should be within a few seconds of the actual current time."""
        before = datetime.now(timezone.utc)
        result = _now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after or before <= result or result <= after
        # Allow a small tolerance for execution time
        assert abs((result - before).total_seconds()) < 2
        assert abs((after - result).total_seconds()) < 2

    def test_timezone_aware(self):
        """Result should be timezone-aware."""
        result = _now()
        assert result.tzinfo is not None
        assert result.utcoffset() is not None
