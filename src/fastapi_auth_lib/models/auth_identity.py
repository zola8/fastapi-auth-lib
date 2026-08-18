from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from fastapi_auth_lib.api.schemas.constants import PASSWORD_HASH_MAX_LENGTH
from fastapi_auth_lib.api.schemas.constants import PROVIDER_SUBJECT_MAX_LENGTH
from fastapi_auth_lib.core.utils import _now
from fastapi_auth_lib.models.base import AuthProvider


class AuthIdentity(BaseModel):
    """Authentication identity for a user."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    auth_identity_id: Optional[int] = Field(
        default=None,
        description="Primary key for auth identity",
    )

    user_id: UUID = Field(
        description="References UserProfile.user_id",
    )

    provider: AuthProvider = Field(
        description="Authentication provider",
    )

    provider_subject: str = Field(
        min_length=1,
        max_length=PROVIDER_SUBJECT_MAX_LENGTH,
        description="Provider-specific unique identifier, for email/password: normalized email",
    )

    password_hash: Optional[str] = Field(
        default=None,
        max_length=PASSWORD_HASH_MAX_LENGTH,
        repr=False,
        exclude=True,
        description="Salted password hash.",
    )

    created_at: datetime = Field(
        default_factory=_now,
        description="Creation timestamp",
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp",
    )

    @model_validator(mode="after")
    def validate_provider_credentials(self) -> "AuthIdentity":
        if self.provider == AuthProvider.PASSWORD:
            if not self.password_hash:
                raise ValueError("password_hash is required for PASSWORD provider")
        else:
            if self.password_hash:
                raise ValueError("password_hash is not allowed for non-PASSWORD providers")

        return self

    @field_validator("provider_subject", mode="after")
    @classmethod
    def _validate_provider_subject(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("provider_subject cannot be blank")

        if value != value.strip():
            raise ValueError(
                "provider_subject cannot contain leading or trailing whitespace"
            )

        return value

    @field_validator("password_hash", mode="after")
    @classmethod
    def _validate_password_hash(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value

        if not value.strip():
            raise ValueError("password_hash cannot be blank")

        if any(char.isspace() for char in value):
            raise ValueError("password_hash cannot contain whitespace")

        return value
