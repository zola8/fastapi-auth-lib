from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field
from pydantic import SecretStr
from pydantic import field_validator

from src.fastapi_auth_lib.core.constants import PASSWORD_MAX_LENGTH
from src.fastapi_auth_lib.core.constants import PASSWORD_MIN_LENGTH
from src.fastapi_auth_lib.core.utils import normalize_email


class RegisterWithPasswordRequest(BaseModel):
    """
    Request body for password registration.
    """

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
