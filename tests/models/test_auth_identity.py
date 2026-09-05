from datetime import datetime
from datetime import timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.fastapi_auth_lib.core.constants import PASSWORD_HASH_MAX_LENGTH
from src.fastapi_auth_lib.core.constants import PROVIDER_SUBJECT_MAX_LENGTH
from src.fastapi_auth_lib.models.auth_identity import AuthIdentity
from src.fastapi_auth_lib.models.base import AuthProvider


class TestAuthIdentityDefaults:
    """Tests for default values."""

    def test_default_auth_identity_id_none(self):
        """auth_identity_id should be None by default."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="user@example.com",
            password_hash="hash",
        )
        assert identity.auth_identity_id is None

    def test_default_created_at(self):
        """created_at should be set to current UTC time."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="user@example.com",
            password_hash="hash",
        )
        assert isinstance(identity.created_at, datetime)
        assert identity.created_at.tzinfo == timezone.utc
        now = datetime.now(timezone.utc)
        assert abs((now - identity.created_at).total_seconds()) < 5

    def test_default_updated_at_none(self):
        """updated_at should be None by default."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="user@example.com",
            password_hash="hash",
        )
        assert identity.updated_at is None


class TestAuthIdentityValidators:
    """Tests for model validators."""

    def test_password_provider_normalizes_email(self):
        """provider_subject should be normalized email for PASSWORD provider."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="  User@Example.COM  ",
            password_hash="hash",
        )
        assert identity.provider_subject == "user@example.com"

    def test_password_hash_required_for_password_provider(self):
        """password_hash must be provided for PASSWORD provider."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                provider_subject="user@example.com",
            )

    def test_password_hash_excluded_from_serialization(self):
        """password_hash should not appear in model_dump()."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="user@example.com",
            password_hash="secret",
        )
        assert "password_hash" not in identity.model_dump()

    def test_password_hash_not_printed_in_repr(self):
        """password_hash should not be shown in repr."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="user@example.com",
            password_hash="secret",
        )
        assert "secret" not in repr(identity)

    def test_provider_subject_blank_after_strip_raises(self):
        """provider_subject that becomes empty after stripping should raise."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                provider_subject="   ",
                password_hash="hash",
            )


class TestAuthIdentityValidationErrors:
    """Tests for field validation failures."""

    def test_user_id_required(self):
        """user_id must be provided."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                provider=AuthProvider.PASSWORD,
                provider_subject="user@example.com",
                password_hash="hash",
            )

    def test_provider_required(self):
        """provider must be provided."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider_subject="user@example.com",
                password_hash="hash",
            )

    def test_provider_subject_required(self):
        """provider_subject must be provided."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                password_hash="hash",
            )

    def test_provider_invalid_enum(self):
        """Invalid provider value should raise."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider="github",
                provider_subject="user@example.com",
                password_hash="hash",
            )

    def test_provider_subject_too_long(self):
        """provider_subject exceeding max length should raise."""
        long_subject = "a" * (PROVIDER_SUBJECT_MAX_LENGTH + 1)
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                provider_subject=long_subject,
                password_hash="hash",
            )

    def test_password_hash_too_long(self):
        """password_hash exceeding max length should raise."""
        long_hash = "a" * (PASSWORD_HASH_MAX_LENGTH + 1)
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                provider_subject="user@example.com",
                password_hash=long_hash,
            )


class TestAuthIdentityEdgeCases:
    """Tests for edge cases and None handling."""

    def test_user_id_accepts_uuid(self):
        """user_id should accept a valid UUID."""
        uid = uuid4()
        identity = AuthIdentity(
            user_id=uid,
            provider=AuthProvider.PASSWORD,
            provider_subject="user@example.com",
            password_hash="hash",
        )
        assert identity.user_id == uid

    def test_provider_subject_accepts_min_length(self):
        """provider_subject of length 1 is allowed."""
        identity = AuthIdentity(
            user_id=uuid4(),
            provider=AuthProvider.PASSWORD,
            provider_subject="a",
            password_hash="hash",
        )
        assert identity.provider_subject == "a"

    def test_provider_subject_none_raises(self):
        """None provider_subject should raise (required + min_length)."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                provider_subject=None,
                password_hash="hash",
            )

    def test_password_hash_none_with_password_provider_raises(self):
        """None password_hash with PASSWORD provider should raise."""
        with pytest.raises(ValidationError):
            AuthIdentity(
                user_id=uuid4(),
                provider=AuthProvider.PASSWORD,
                provider_subject="user@example.com",
                password_hash=None,
            )
