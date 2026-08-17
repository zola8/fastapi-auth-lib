from typing import Optional, Any

from pydantic import BaseModel, Field, EmailStr, SecretStr, field_validator, model_validator

from .constants import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    USERNAME_PATTERN
)
from fastapi_auth_lib.core.utils import normalize_email, normalize_username


class RegisterWithPasswordRequest(BaseModel):
    """
    Request body for password registration.
    """

    email: EmailStr = Field(
        description="Primary email address",
    )

    password: SecretStr = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="Raw password. Hashed by the backend.",
    )

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class LoginWithPasswordRequest(BaseModel):
    """
    Request body for password login.
    """

    email: EmailStr = Field(
        description="User email address",
    )

    password: SecretStr = Field(
        min_length=1,
        max_length=PASSWORD_MAX_LENGTH,
        description="Raw password",
    )

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class UserUpdateRequest(BaseModel):
    """
    Request body for user self-update.
    """

    username: Optional[str] = Field(
        default=None,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
        description=(
            "Optional display username. "
            "If provided, must be between "
            f"{USERNAME_MIN_LENGTH} and {USERNAME_MAX_LENGTH} characters "
            "and match the allowed pattern."
        ),
    )

    @field_validator("username", mode="before")
    @classmethod
    def _normalize_username(cls, value: Any) -> Any:
        return normalize_username(value)

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "UserUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        return self


class PasswordChangeRequest(BaseModel):
    """
    Request body for password change.
    """

    current_password: SecretStr = Field(
        min_length=1,
        max_length=PASSWORD_MAX_LENGTH,
    )

    new_password: SecretStr = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )

    @model_validator(mode="after")
    def validate_new_password_different(self) -> "PasswordChangeRequest":
        if self.current_password.get_secret_value() == self.new_password.get_secret_value():
            raise ValueError("new_password must be different from current_password")

        return self


class UserSelfDeleteRequest(BaseModel):
    """
    Request body for user self deletion.
    """

    password: SecretStr = Field(
        min_length=1,
        max_length=PASSWORD_MAX_LENGTH,
        description="Current password for confirmation",
    )
