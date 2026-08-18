import uuid
from datetime import datetime
from datetime import timezone

import pytest
from pydantic import ValidationError

from fastapi_auth_lib.api.schemas.constants import USERNAME_MAX_LENGTH
from fastapi_auth_lib.api.schemas.constants import USERNAME_MIN_LENGTH
from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus
from fastapi_auth_lib.models.user import UserProfile
from tests.conftest import USER_ID
from tests.conftest import VALID_EMAIL


def valid_username() -> str:
    return "a" * USERNAME_MIN_LENGTH


def max_username() -> str:
    return "a" * USERNAME_MAX_LENGTH


def below_min_username() -> str:
    return "a" * max(0, USERNAME_MIN_LENGTH - 1)


def above_max_username() -> str:
    return "a" * (USERNAME_MAX_LENGTH + 1)


def invalid_pattern_username() -> str:
    return "!" * USERNAME_MIN_LENGTH


class TestUserProfileDefaults:
    def test_minimal_user_profile(self):
        user = UserProfile(email=VALID_EMAIL)

        assert user.user_id is None
        assert user.username is None
        assert user.email == VALID_EMAIL
        assert user.status == UserStatus.INACTIVE
        assert user.roles == [UserRole.USER]
        assert isinstance(user.created_at, datetime)
        assert user.updated_at is None

    def test_created_at_is_timezone_aware(self):
        user = UserProfile(email=VALID_EMAIL)

        assert user.created_at.tzinfo is not None

    def test_default_roles_are_not_shared_between_instances(self):
        user_one = UserProfile(email="one@example.com")
        user_two = UserProfile(email="two@example.com")

        user_one.roles.append(UserRole.ADMIN)

        assert user_one.roles == [UserRole.USER, UserRole.ADMIN]
        assert user_two.roles == [UserRole.USER]


class TestUserId:
    def test_user_id_is_optional(self):
        user = UserProfile(email=VALID_EMAIL)
        assert user.user_id is None

    def test_user_id_accepts_uuid_object(self):
        user_id = uuid.uuid4()
        user = UserProfile(
            user_id=user_id,
            email=VALID_EMAIL,
        )
        assert user.user_id == user_id

    def test_user_id_accepts_valid_uuid_string(self):
        user = UserProfile(
            user_id=USER_ID,
            email=VALID_EMAIL,
        )
        assert user.user_id == uuid.UUID(USER_ID)

    def test_user_id_rejects_invalid_string(self):
        with pytest.raises(ValidationError):
            UserProfile(
                user_id="not-a-uuid",
                email=VALID_EMAIL,
            )


class TestUsername:
    def test_username_is_optional(self):
        user = UserProfile(email=VALID_EMAIL, username=None)

        assert user.username is None

    @pytest.mark.parametrize(
        "username",
        [
            valid_username(),
            max_username(),
            "A" * USERNAME_MIN_LENGTH,
            "_" * USERNAME_MIN_LENGTH,
            "-" * USERNAME_MIN_LENGTH,
        ],
    )
    def test_valid_username(self, username):
        user = UserProfile(email=VALID_EMAIL, username=username)

        assert user.username == username

    @pytest.mark.parametrize(
        "username",
        [
            "",
            below_min_username(),
            above_max_username(),
            invalid_pattern_username(),
            "user name",
            "user@name",
            "user.name",
            "user!",
        ],
    )
    def test_invalid_username(self, username):
        with pytest.raises(ValidationError):
            UserProfile(email=VALID_EMAIL, username=username)

    def test_username_is_not_normalized(self):
        """
        Normalization now happens in API/service layers.

        Since the model no longer strips whitespace, a username with surrounding
        whitespace should fail the pattern validation.
        """
        raw_username = f"  {valid_username()}  "

        with pytest.raises(ValidationError):
            UserProfile(email=VALID_EMAIL, username=raw_username)

    def test_username_case_is_preserved(self):
        username = "A" * USERNAME_MIN_LENGTH

        user = UserProfile(email=VALID_EMAIL, username=username)

        assert user.username == username


class TestEmail:
    def test_email_is_required(self):
        with pytest.raises(ValidationError):
            UserProfile()

    def test_valid_email(self):
        user = UserProfile(email=VALID_EMAIL)

        assert user.email == VALID_EMAIL

    @pytest.mark.parametrize(
        "email",
        [
            "not-an-email",
            "user@",
            "@example.com",
            "",
            None,
            123,
        ],
    )
    def test_invalid_email(self, email):
        with pytest.raises(ValidationError):
            UserProfile(email=email)

    def test_uppercase_email_is_accepted(self):
        user = UserProfile(email="USER@EXAMPLE.COM")

        assert user.email.lower() == VALID_EMAIL


class TestStatus:
    def test_default_status_is_inactive(self):
        user = UserProfile(email=VALID_EMAIL)

        assert user.status == UserStatus.INACTIVE

    def test_status_accepts_enum(self):
        user = UserProfile(
            email=VALID_EMAIL,
            status=UserStatus.ACTIVE,
        )

        assert user.status == UserStatus.ACTIVE

    def test_status_accepts_string_value(self):
        user = UserProfile(
            email=VALID_EMAIL,
            status="active",
        )

        assert user.status == UserStatus.ACTIVE

    def test_deleted_status_is_currently_allowed_by_model(self):
        """
        Current model does not reject DELETED.

        If you add validate_status_not_deleted later, this test should change.
        """
        user = UserProfile(
            email=VALID_EMAIL,
            status=UserStatus.DELETED,
        )

        assert user.status == UserStatus.DELETED

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            UserProfile(
                email=VALID_EMAIL,
                status="locked",
            )


class TestRoles:
    def test_default_roles(self):
        user = UserProfile(email=VALID_EMAIL)

        assert user.roles == [UserRole.USER]

    def test_roles_accepts_enum_values(self):
        user = UserProfile(
            email=VALID_EMAIL,
            roles=[UserRole.USER, UserRole.ADMIN],
        )

        assert user.roles == [UserRole.USER, UserRole.ADMIN]

    def test_roles_accepts_string_values(self):
        user = UserProfile(
            email=VALID_EMAIL,
            roles=["admin", "user"],
        )

        assert user.roles == [UserRole.ADMIN, UserRole.USER]

    def test_roles_deduplicates(self):
        user = UserProfile(
            email=VALID_EMAIL,
            roles=[UserRole.USER, UserRole.USER, UserRole.ADMIN, UserRole.ADMIN],
        )

        assert user.roles == [UserRole.USER, UserRole.ADMIN]

    def test_roles_deduplication_preserves_order(self):
        user = UserProfile(
            email=VALID_EMAIL,
            roles=[UserRole.ADMIN, UserRole.USER, UserRole.ADMIN, UserRole.USER],
        )

        assert user.roles == [UserRole.ADMIN, UserRole.USER]

    def test_empty_roles_are_invalid(self):
        with pytest.raises(ValidationError):
            UserProfile(
                email=VALID_EMAIL,
                roles=[],
            )

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            UserProfile(
                email=VALID_EMAIL,
                roles=["superuser"],
            )


class TestTimestamps:
    def test_created_at_has_default(self):
        user = UserProfile(email=VALID_EMAIL)

        assert isinstance(user.created_at, datetime)

    def test_updated_at_defaults_to_none(self):
        user = UserProfile(email=VALID_EMAIL)

        assert user.updated_at is None

    def test_timestamps_can_be_provided_explicitly(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)

        user = UserProfile(
            email=VALID_EMAIL,
            created_at=now,
            updated_at=now,
        )

        assert user.created_at == now
        assert user.updated_at == now


class TestFromAttributes:
    def test_from_attributes(self):
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)

        class DummyUser:
            user_id = uuid.UUID(USER_ID)
            username = "dummy_user"
            email = "user@example.com"
            status = UserStatus.ACTIVE
            roles = [UserRole.ADMIN]
            created_at = now
            updated_at = None

        user = UserProfile.model_validate(DummyUser())

        assert user.user_id == uuid.UUID(USER_ID)
        assert user.username == "dummy_user"
        assert user.email == "user@example.com"
        assert user.status == UserStatus.ACTIVE
        assert user.roles == [UserRole.ADMIN]
        assert user.created_at == now
        assert user.updated_at is None
