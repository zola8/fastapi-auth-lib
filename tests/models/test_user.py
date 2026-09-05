from datetime import datetime
from datetime import timezone

import pytest
from pydantic import ValidationError

from src.fastapi_auth_lib.core.constants import EMAIL_MAX_LENGTH
from src.fastapi_auth_lib.core.constants import USERNAME_MAX_LENGTH
from src.fastapi_auth_lib.core.constants import USERNAME_MIN_LENGTH
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.base import UserStatus
from src.fastapi_auth_lib.models.user import UserProfile


class TestUserProfileDefaults:
    """Tests for default values."""

    def test_default_status(self):
        """Default status should be INACTIVE."""
        profile = UserProfile(email="user@example.com")
        assert profile.status == UserStatus.INACTIVE

    def test_default_roles(self):
        """Default roles should be [USER]."""
        profile = UserProfile(email="user@example.com")
        assert profile.roles == [UserRole.USER]

    def test_default_created_at(self):
        """created_at should be set to current UTC time."""
        profile = UserProfile(email="user@example.com")
        assert isinstance(profile.created_at, datetime)
        assert profile.created_at.tzinfo == timezone.utc
        # Within a few seconds
        now = datetime.now(timezone.utc)
        assert abs((now - profile.created_at).total_seconds()) < 5

    def test_default_user_id_none(self):
        """user_id should be None by default."""
        profile = UserProfile(email="user@example.com")
        assert profile.user_id is None

    def test_default_username_none(self):
        """username should be None by default."""
        profile = UserProfile(email="user@example.com")
        assert profile.username is None

    def test_default_updated_at_none(self):
        """updated_at should be None by default."""
        profile = UserProfile(email="user@example.com")
        assert profile.updated_at is None


class TestUserProfileValidators:
    """Tests for field validators."""

    def test_email_normalized(self):
        """Email should be stripped and lowercased."""
        profile = UserProfile(email="  User@Example.COM  ")
        assert profile.email == "user@example.com"

    def test_username_stripped(self):
        """Username should have leading/trailing whitespace removed."""
        profile = UserProfile(email="user@example.com", username="  john_doe  ")
        assert profile.username == "john_doe"

    def test_roles_deduplicated(self):
        """Duplicate roles should be removed."""
        profile = UserProfile(
            email="user@example.com",
            roles=[UserRole.USER, UserRole.ADMIN, UserRole.USER],
        )
        assert profile.roles == [UserRole.USER, UserRole.ADMIN]

    def test_roles_order_preserved(self):
        """The first occurrence of each role should be kept."""
        profile = UserProfile(
            email="user@example.com",
            roles=[UserRole.ADMIN, UserRole.USER, UserRole.ADMIN],
        )
        assert profile.roles == [UserRole.ADMIN, UserRole.USER]


class TestUserProfileValidationErrors:
    """Tests for validation failures."""

    def test_email_required(self):
        """Email must be provided."""
        with pytest.raises(ValidationError):
            UserProfile()

    def test_email_invalid_format(self):
        """Invalid email format should raise."""
        with pytest.raises(ValidationError):
            UserProfile(email="not-an-email")

    def test_email_too_long(self):
        """Email exceeding max length should raise."""
        long_email = "a" * (EMAIL_MAX_LENGTH + 1) + "@example.com"
        with pytest.raises(ValidationError):
            UserProfile(email=long_email)

    def test_username_too_short(self):
        """Username shorter than min length should raise."""
        short_username = "a" * (USERNAME_MIN_LENGTH - 1)
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", username=short_username)

    def test_username_too_long(self):
        """Username exceeding max length should raise."""
        long_username = "a" * (USERNAME_MAX_LENGTH + 1)
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", username=long_username)

    def test_username_invalid_pattern(self):
        """Username containing invalid characters should raise."""
        # Space and exclamation are not allowed by USERNAME_PATTERN
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", username="invalid name!")

    def test_username_empty_after_strip(self):
        """Whitespace-only username becomes empty and fails min_length."""
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", username="   ")

    def test_roles_empty_list(self):
        """Empty roles list should fail min_length."""
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", roles=[])

    def test_roles_invalid_enum_value(self):
        """Role value not in enum should raise."""
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", roles=["superuser"])

    def test_status_invalid_value(self):
        """Invalid status value should raise."""
        with pytest.raises(ValidationError):
            UserProfile(email="user@example.com", status="banned")


class TestUserProfileEdgeCases:
    """Tests for edge cases and None handling."""

    def test_user_id_accepts_none(self):
        """user_id can be None."""
        profile = UserProfile(email="user@example.com", user_id=None)
        assert profile.user_id is None

    def test_username_accepts_none(self):
        """username can be None."""
        profile = UserProfile(email="user@example.com", username=None)
        assert profile.username is None

    def test_updated_at_accepts_none(self):
        """updated_at can be None."""
        profile = UserProfile(email="user@example.com", updated_at=None)
        assert profile.updated_at is None

    def test_email_not_normalized_when_none(self):
        """Email is required; None should raise, not be normalized."""
        with pytest.raises(ValidationError):
            UserProfile(email=None)

    def test_username_not_normalized_when_none(self):
        """None username stays None."""
        profile = UserProfile(email="user@example.com", username=None)
        assert profile.username is None
