import uuid
from datetime import datetime
from datetime import timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from fastapi_auth_lib.api.schemas.constants import PASSWORD_HASH_MAX_LENGTH
from fastapi_auth_lib.api.schemas.constants import PROVIDER_SUBJECT_MAX_LENGTH
from fastapi_auth_lib.models.auth_identity import AuthIdentity
from fastapi_auth_lib.models.base import AuthProvider
from tests.conftest import USER_ID


def valid_password_hash(length: int = 32) -> str:
    return "a" * max(1, min(length, PASSWORD_HASH_MAX_LENGTH))


def max_password_hash() -> str:
    return "a" * PASSWORD_HASH_MAX_LENGTH


def above_max_password_hash() -> str:
    return "a" * (PASSWORD_HASH_MAX_LENGTH + 1)


def sample_provider_subject() -> str:
    subject = "user@example.com"

    if len(subject) <= PROVIDER_SUBJECT_MAX_LENGTH:
        return subject

    return "a" * PROVIDER_SUBJECT_MAX_LENGTH


def max_provider_subject() -> str:
    return "a" * PROVIDER_SUBJECT_MAX_LENGTH


def above_max_provider_subject() -> str:
    return "a" * (PROVIDER_SUBJECT_MAX_LENGTH + 1)


def make_payload(**overrides):
    payload = {
        "user_id": USER_ID,
        "provider": AuthProvider.PASSWORD,
        "provider_subject": sample_provider_subject(),
        "password_hash": valid_password_hash(),
    }

    payload.update(overrides)
    return payload


def make_auth_identity(**overrides) -> AuthIdentity:
    return AuthIdentity(**make_payload(**overrides))


class TestValidAuthIdentity:
    def test_valid_password_identity(self):
        identity = make_auth_identity()

        assert identity.auth_identity_id is None
        assert str(identity.user_id) == USER_ID
        assert identity.provider == AuthProvider.PASSWORD
        assert identity.provider_subject == sample_provider_subject()
        assert identity.password_hash == valid_password_hash()
        assert isinstance(identity.created_at, datetime)
        assert identity.updated_at is None

    def test_provider_accepts_string_value(self):
        identity = make_auth_identity(provider="password")

        assert identity.provider == AuthProvider.PASSWORD

    def test_auth_identity_id_accepts_int(self):
        identity = make_auth_identity(auth_identity_id=10)

        assert identity.auth_identity_id == 10

    def test_created_at_default_is_timezone_aware(self):
        identity = make_auth_identity()

        assert identity.created_at.tzinfo is not None

    def test_updated_at_defaults_to_none(self):
        identity = make_auth_identity()

        assert identity.updated_at is None

    def test_explicit_timestamps_are_preserved(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)

        identity = make_auth_identity(
            created_at=now,
            updated_at=now,
        )

        assert identity.created_at == now
        assert identity.updated_at == now


class TestRequiredFields:
    @pytest.mark.parametrize(
        "missing_field",
        [
            "user_id",
            "provider",
            "provider_subject",
            "password_hash",
        ],
    )
    def test_missing_required_field_for_password_provider(self, missing_field):
        payload = make_payload()
        del payload[missing_field]

        with pytest.raises(ValidationError):
            AuthIdentity(**payload)


class TestUserId:
    def test_empty_user_id_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(user_id="")

    def test_empty_user_id_is_invalid_2(self):
        with pytest.raises(ValidationError):
            make_auth_identity(user_id="a")


class TestProvider:
    def test_invalid_provider_is_rejected(self):
        with pytest.raises(ValidationError):
            make_auth_identity(provider="oauth")


class TestProviderSubject:
    def test_empty_provider_subject_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(provider_subject="")

    def test_blank_provider_subject_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(provider_subject="   ")

    @pytest.mark.parametrize(
        "provider_subject",
        [
            " leading",
            "trailing ",
            "  both  ",
            "\tsubject",
            "subject\n",
        ],
    )
    def test_provider_subject_with_surrounding_whitespace_is_invalid(
        self,
        provider_subject,
    ):
        with pytest.raises(ValidationError):
            make_auth_identity(provider_subject=provider_subject)

    def test_provider_subject_max_length_is_valid(self):
        identity = make_auth_identity(provider_subject=max_provider_subject())

        assert identity.provider_subject == max_provider_subject()

    def test_provider_subject_above_max_length_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(provider_subject=above_max_provider_subject())

    def test_provider_subject_is_not_normalized(self):
        """
        The model does not lowercase provider_subject.

        Normalization should happen before this model is constructed.
        """
        raw_subject = sample_provider_subject().upper()

        identity = make_auth_identity(provider_subject=raw_subject)

        assert identity.provider_subject == raw_subject


class TestPasswordHash:
    def test_password_hash_is_required_for_password_provider(self):
        with pytest.raises(ValidationError) as exc_info:
            make_auth_identity(password_hash=None)

        assert "password_hash is required" in str(exc_info.value)

    def test_empty_password_hash_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(password_hash="")

    def test_blank_password_hash_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(password_hash="   ")

    @pytest.mark.parametrize(
        "password_hash",
        [
            "abc def",
            " abcdef",
            "abcdef ",
            "abc\ndef",
            "abc\tdef",
        ],
    )
    def test_password_hash_with_whitespace_is_invalid(self, password_hash):
        with pytest.raises(ValidationError):
            make_auth_identity(password_hash=password_hash)

    def test_password_hash_max_length_is_valid(self):
        password_hash = max_password_hash()

        identity = make_auth_identity(password_hash=password_hash)

        assert identity.password_hash == password_hash

    def test_password_hash_above_max_length_is_invalid(self):
        with pytest.raises(ValidationError):
            make_auth_identity(password_hash=above_max_password_hash())

    def test_password_hash_is_still_accessible_on_model(self):
        password_hash = valid_password_hash()

        identity = make_auth_identity(password_hash=password_hash)

        assert identity.password_hash == password_hash

    def test_password_hash_is_excluded_from_model_dump(self):
        password_hash = valid_password_hash()

        identity = make_auth_identity(password_hash=password_hash)

        dumped = identity.model_dump()

        assert "password_hash" not in dumped

    def test_password_hash_is_not_in_json_dump(self):
        password_hash = valid_password_hash()

        identity = make_auth_identity(password_hash=password_hash)

        assert password_hash not in identity.model_dump_json()

    def test_password_hash_is_hidden_from_repr(self):
        password_hash = valid_password_hash()

        identity = make_auth_identity(password_hash=password_hash)

        assert password_hash not in repr(identity)


class TestFromAttributes:
    def test_from_attributes(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        password_hash = valid_password_hash()

        dummy = SimpleNamespace(
            auth_identity_id=1,
            user_id=uuid.UUID(USER_ID),
            provider=AuthProvider.PASSWORD,
            provider_subject=sample_provider_subject(),
            password_hash=password_hash,
            created_at=now,
            updated_at=None,
        )

        identity = AuthIdentity.model_validate(dummy)

        assert identity.auth_identity_id == 1
        assert str(identity.user_id) == USER_ID
        assert identity.provider == AuthProvider.PASSWORD
        assert identity.provider_subject == sample_provider_subject()
        assert identity.password_hash == password_hash
        assert identity.created_at == now
        assert identity.updated_at is None

        assert "password_hash" not in identity.model_dump()
