import pytest
from pydantic import ValidationError

from fastapi_auth_lib.api.schemas.constants import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)
from fastapi_auth_lib.api.schemas.requests import (
    RegisterWithPasswordRequest,
    LoginWithPasswordRequest,
    UserUpdateRequest,
    PasswordChangeRequest,
    UserSelfDeleteRequest,
)
from tests.conftest import VALID_EMAIL


def valid_new_password() -> str:
    return "a" * PASSWORD_MIN_LENGTH


def below_min_password() -> str:
    return "a" * max(0, PASSWORD_MIN_LENGTH - 1)


def max_password() -> str:
    return "a" * PASSWORD_MAX_LENGTH


def above_max_password() -> str:
    return "a" * (PASSWORD_MAX_LENGTH + 1)


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


def make_register_payload(email=VALID_EMAIL, password=None):
    return {
        "email": email,
        "password": valid_new_password() if password is None else password,
    }


class TestRegisterWithPasswordRequest:
    def test_valid_request(self):
        request = RegisterWithPasswordRequest(**make_register_payload())

        assert request.email == VALID_EMAIL
        assert request.password.get_secret_value() == valid_new_password()

    def test_email_is_normalized(self):
        request = RegisterWithPasswordRequest(
            **make_register_payload(email="  USER@EXAMPLE.COM  ")
        )

        assert request.email == "user@example.com"

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
            RegisterWithPasswordRequest(**make_register_payload(email=email))

    def test_missing_email(self):
        payload = make_register_payload()
        del payload["email"]

        with pytest.raises(ValidationError):
            RegisterWithPasswordRequest(**payload)

    def test_missing_password(self):
        payload = make_register_payload()
        del payload["password"]

        with pytest.raises(ValidationError):
            RegisterWithPasswordRequest(**payload)

    def test_password_min_length_is_valid(self):
        request = RegisterWithPasswordRequest(
            **make_register_payload(password=valid_new_password())
        )

        assert request.password.get_secret_value() == valid_new_password()

    def test_password_max_length_is_valid(self):
        request = RegisterWithPasswordRequest(
            **make_register_payload(password=max_password())
        )

        assert request.password.get_secret_value() == max_password()

    @pytest.mark.parametrize(
        "password",
        [
            "",
            below_min_password(),
            above_max_password(),
        ],
    )
    def test_invalid_password(self, password):
        with pytest.raises(ValidationError):
            RegisterWithPasswordRequest(**make_register_payload(password=password))

    def test_password_is_not_trimmed(self):
        raw_password = ("  " + valid_new_password() + "  ")[:PASSWORD_MAX_LENGTH]

        request = RegisterWithPasswordRequest(
            **make_register_payload(password=raw_password)
        )

        assert request.password.get_secret_value() == raw_password

    def test_password_is_hidden_from_repr(self):
        secret = valid_new_password()
        request = RegisterWithPasswordRequest(**make_register_payload(password=secret))

        assert secret not in repr(request)

    def test_password_is_hidden_from_json_dump(self):
        secret = valid_new_password()
        request = RegisterWithPasswordRequest(**make_register_payload(password=secret))

        assert secret not in request.model_dump_json()


class TestLoginWithPasswordRequest:
    def test_valid_request(self):
        request = LoginWithPasswordRequest(
            email=VALID_EMAIL,
            password="a",
        )

        assert request.email == VALID_EMAIL
        assert request.password.get_secret_value() == "a"

    def test_email_is_normalized(self):
        request = LoginWithPasswordRequest(
            email="  USER@EXAMPLE.COM  ",
            password="a",
        )

        assert request.email == "user@example.com"

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
            LoginWithPasswordRequest(
                email=email,
                password="a",
            )

    def test_missing_email(self):
        with pytest.raises(ValidationError):
            LoginWithPasswordRequest(password="a")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            LoginWithPasswordRequest(email=VALID_EMAIL)

    def test_password_min_length_is_one(self):
        request = LoginWithPasswordRequest(
            email=VALID_EMAIL,
            password="a",
        )

        assert request.password.get_secret_value() == "a"

    def test_empty_password_is_invalid(self):
        with pytest.raises(ValidationError):
            LoginWithPasswordRequest(
                email=VALID_EMAIL,
                password="",
            )

    def test_password_max_length_is_valid(self):
        request = LoginWithPasswordRequest(
            email=VALID_EMAIL,
            password=max_password(),
        )

        assert request.password.get_secret_value() == max_password()

    def test_password_above_max_length_is_invalid(self):
        with pytest.raises(ValidationError):
            LoginWithPasswordRequest(
                email=VALID_EMAIL,
                password=above_max_password(),
            )

    def test_password_is_not_trimmed(self):
        raw_password = ("  a  ")[:PASSWORD_MAX_LENGTH]

        request = LoginWithPasswordRequest(
            email=VALID_EMAIL,
            password=raw_password,
        )

        assert request.password.get_secret_value() == raw_password


class TestUserUpdateRequest:
    def test_valid_username(self):
        request = UserUpdateRequest(username=valid_username())

        assert request.username == valid_username()

    def test_max_length_username_is_valid(self):
        request = UserUpdateRequest(username=max_username())

        assert request.username == max_username()

    def test_username_is_stripped_and_case_preserved(self):
        base_username = "A" * USERNAME_MIN_LENGTH
        raw_username = f"  {base_username}  "

        request = UserUpdateRequest(username=raw_username)

        assert request.username == base_username

    def test_explicit_null_username_is_allowed(self):
        request = UserUpdateRequest.model_validate({"username": None})

        assert request.username is None

    def test_empty_request_is_invalid(self):
        with pytest.raises(ValidationError):
            UserUpdateRequest.model_validate({})

    def test_no_fields_is_invalid(self):
        with pytest.raises(ValidationError):
            UserUpdateRequest()

    def test_whitespace_only_username_is_invalid(self):
        with pytest.raises(ValidationError):
            UserUpdateRequest(username="   ")

    @pytest.mark.parametrize(
        "username",
        [
            below_min_username(),
            above_max_username(),
            invalid_pattern_username(),
            "user name",
            "user@name",
            "user.name",
        ],
    )
    def test_invalid_username(self, username):
        with pytest.raises(ValidationError):
            UserUpdateRequest(username=username)


class TestPasswordChangeRequest:
    def test_valid_request(self):
        request = PasswordChangeRequest(
            current_password="old",
            new_password=valid_new_password(),
        )

        assert request.current_password.get_secret_value() == "old"
        assert request.new_password.get_secret_value() == valid_new_password()

    def test_current_password_can_be_shorter_than_password_policy(self):
        request = PasswordChangeRequest(
            current_password="a",
            new_password=valid_new_password(),
        )

        assert request.current_password.get_secret_value() == "a"

    def test_missing_current_password_is_invalid(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(new_password=valid_new_password())

    def test_missing_new_password_is_invalid(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(current_password="old")

    def test_empty_current_password_is_invalid(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="",
                new_password=valid_new_password(),
            )

    def test_current_password_above_max_length_is_invalid(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password=above_max_password(),
                new_password=valid_new_password(),
            )

    def test_new_password_below_min_length_is_invalid(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="old",
                new_password=below_min_password(),
            )

    def test_new_password_above_max_length_is_invalid(self):
        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password="old",
                new_password=above_max_password(),
            )

    def test_same_current_and_new_password_is_invalid(self):
        password = valid_new_password()

        with pytest.raises(ValidationError):
            PasswordChangeRequest(
                current_password=password,
                new_password=password,
            )


class TestUserSelfDeleteRequest:
    def test_valid_request(self):
        request = UserSelfDeleteRequest(password="a")

        assert request.password.get_secret_value() == "a"

    def test_missing_password_is_invalid(self):
        with pytest.raises(ValidationError):
            UserSelfDeleteRequest()

    def test_empty_password_is_invalid(self):
        with pytest.raises(ValidationError):
            UserSelfDeleteRequest(password="")

    def test_password_max_length_is_valid(self):
        request = UserSelfDeleteRequest(password=max_password())

        assert request.password.get_secret_value() == max_password()

    def test_password_above_max_length_is_invalid(self):
        with pytest.raises(ValidationError):
            UserSelfDeleteRequest(password=above_max_password())

    def test_password_is_not_trimmed(self):
        raw_password = ("  a  ")[:PASSWORD_MAX_LENGTH]

        request = UserSelfDeleteRequest(password=raw_password)

        assert request.password.get_secret_value() == raw_password
