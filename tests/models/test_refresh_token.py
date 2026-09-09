import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from pydantic import ValidationError

from fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.models.refresh_token import RefreshToken


def make_valid_token(**overrides):
    """Create a valid RefreshToken payload with sensible defaults."""
    data = {
        "user_id": uuid.uuid4(),
        "token_hash": "a" * 64,  # typical SHA-256 hex length
        "expires_at": _now() + timedelta(days=7),
    }
    data.update(overrides)
    return data


class TestRefreshToken:
    """Tests for RefreshToken model."""

    def test_valid_creation(self):
        """Should create a valid model with all fields."""
        data = make_valid_token()
        token = RefreshToken(**data)
        assert token.user_id == data["user_id"]
        assert token.token_hash == data["token_hash"]
        assert token.expires_at == data["expires_at"]
        assert token.refresh_token_id is None
        assert isinstance(token.created_at, datetime)

    def test_default_refresh_token_id_none(self):
        """refresh_token_id should default to None."""
        token = RefreshToken(**make_valid_token())
        assert token.refresh_token_id is None

    def test_default_created_at(self):
        """created_at should be set to current UTC time."""
        before = datetime.now(timezone.utc)
        token = RefreshToken(**make_valid_token())
        after = datetime.now(timezone.utc)
        assert before <= token.created_at <= after
        assert token.created_at.tzinfo == timezone.utc

    def test_explicit_refresh_token_id(self):
        """refresh_token_id should accept an integer."""
        token = RefreshToken(**make_valid_token(refresh_token_id=42))
        assert token.refresh_token_id == 42

    def test_missing_user_id_raises(self):
        """user_id is required."""
        data = make_valid_token()
        del data["user_id"]
        with pytest.raises(ValidationError):
            RefreshToken(**data)

    def test_missing_token_hash_raises(self):
        """token_hash is required."""
        data = make_valid_token()
        del data["token_hash"]
        with pytest.raises(ValidationError):
            RefreshToken(**data)

    def test_missing_expires_at_raises(self):
        """expires_at is required."""
        data = make_valid_token()
        del data["expires_at"]
        with pytest.raises(ValidationError):
            RefreshToken(**data)

    def test_invalid_user_id_raises(self):
        """user_id must be a valid UUID."""
        data = make_valid_token(user_id="not-a-uuid")
        with pytest.raises(ValidationError):
            RefreshToken(**data)

    def test_user_id_accepts_uuid_string(self):
        """user_id should accept a UUID string and convert to UUID."""
        uid = str(uuid.uuid4())
        token = RefreshToken(**make_valid_token(user_id=uid))
        assert isinstance(token.user_id, uuid.UUID)
        assert str(token.user_id) == uid

    def test_invalid_expires_at_type_raises(self):
        """expires_at must be datetime; unparseable string should raise."""
        data = make_valid_token(expires_at="not-a-valid-date")
        with pytest.raises(ValidationError):
            RefreshToken(**data)

    def test_none_refresh_token_id_allowed(self):
        """refresh_token_id can be explicitly None."""
        token = RefreshToken(**make_valid_token(refresh_token_id=None))
        assert token.refresh_token_id is None

    def test_none_created_at_raises(self):
        """created_at cannot be None."""
        data = make_valid_token()
        data["created_at"] = None
        with pytest.raises(ValidationError):
            RefreshToken(**data)
