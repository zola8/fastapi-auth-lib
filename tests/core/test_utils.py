import pytest

from src.fastapi_auth_lib import normalize_username, normalize_email


class TestNormalizeUsername:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, None),
            (123, 123),
            (["username"], ["username"]),
            ("  User_123  ", "User_123"),
            ("ABC", "ABC"),
        ],
    )
    def test_normalize_username(self, value, expected):
        assert normalize_username(value) == expected


class TestNormalizeEmail:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, None),
            (123, 123),
            (["email"], ["email"]),
            ("  USER@Example.COM ", "user@example.com"),
            ("user@example.com", "user@example.com"),
        ],
    )
    def test_normalize_email(self, value, expected):
        assert normalize_email(value) == expected
