from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from src.fastapi_auth_lib.core.constants import PASSWORD_HASH_MAX_LENGTH
from src.fastapi_auth_lib.core.constants import PROVIDER_SUBJECT_MAX_LENGTH
from src.fastapi_auth_lib.core.utils import _now
from src.fastapi_auth_lib.core.utils import normalize_email
from src.fastapi_auth_lib.models.base import AuthProvider


class AuthIdentity(BaseModel):
    """Authentication identity for a user.

    (provider, provider_subject) must be unique.
    """

    model_config = ConfigDict(from_attributes=True)

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
        description=(
            "Provider-specific unique identifier. "
            "For PASSWORD provider: normalized email."
        ),
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
    def _normalize_and_validate(self) -> "AuthIdentity":
        if self.provider == AuthProvider.PASSWORD:
            if not self.password_hash:
                raise ValueError("password_hash is required for PASSWORD provider")
            self.provider_subject = normalize_email(self.provider_subject)
        else:
            if self.password_hash:
                raise ValueError(
                    "password_hash is not allowed for non-PASSWORD providers"
                )
            self.provider_subject = self.provider_subject.strip()

        if not self.provider_subject:
            raise ValueError("provider_subject cannot be blank after normalization")

        return self
