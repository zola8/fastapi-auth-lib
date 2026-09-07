from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import SecretStr
from pydantic import field_validator

from src.fastapi_auth_lib.core.constants import PASSWORD_MAX_LENGTH
from src.fastapi_auth_lib.core.constants import PASSWORD_MIN_LENGTH
from src.fastapi_auth_lib.core.utils import normalize_email


class RegisterWithPasswordRequest(BaseModel):
    """Request body for password registration."""

    email: EmailStr = Field(description="Primary email address")

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
    """Request body for password login."""

    email: EmailStr = Field(description="Email address")
    password: SecretStr = Field(description="Raw password")

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class ResendActivationRequest(BaseModel):
    """Request body for resending the activation email."""

    email: EmailStr = Field(description="Registered email address")

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing an access token."""

    refresh_token: str = Field(
        min_length=1,
        description="Valid refresh token from a previous login",
    )


class RequestPasswordResetRequest(BaseModel):
    """Request body for the 'forgot password' step."""

    email: EmailStr = Field(description="Registered email address")

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return normalize_email(value)


class ResetPasswordRequest(BaseModel):
    """Request body for setting a new password with a reset token."""

    token: str = Field(min_length=1, description="Reset token from the email link")
    new_password: SecretStr = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="New raw password",
    )
