from datetime import datetime
from typing import List
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field
from pydantic import field_validator

from fastapi_auth_lib.api.schemas.constants import USERNAME_MAX_LENGTH
from fastapi_auth_lib.api.schemas.constants import USERNAME_MIN_LENGTH
from fastapi_auth_lib.api.schemas.constants import USERNAME_PATTERN
from fastapi_auth_lib.core.utils import _now
from fastapi_auth_lib.models.base import UserRole
from fastapi_auth_lib.models.base import UserStatus


class UserProfile(BaseModel):
    """
    User profile model.

    I want to handle the restrictions at the beginning on the API request level. No rules and restrictions are here.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    user_id: Optional[UUID] = Field(
        default=None,
        description="Unique user identifier (UUID)",
    )

    username: Optional[str] = Field(
        default=None,
        min_length=USERNAME_MIN_LENGTH,
        max_length=USERNAME_MAX_LENGTH,
        pattern=USERNAME_PATTERN,
        description="Display name",
    )

    email: EmailStr = Field(
        description="Primary email address",
    )

    status: UserStatus = Field(
        default=UserStatus.INACTIVE,
        description="Account status",
    )

    roles: List[UserRole] = Field(
        default_factory=lambda: [UserRole.USER],
        min_length=1,
        description="User roles",
    )

    created_at: datetime = Field(
        default_factory=_now,
        description="Creation timestamp",
    )

    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp",
    )

    @field_validator("roles", mode="after")
    @classmethod
    def _deduplicate_roles(cls, roles: List[UserRole]) -> List[UserRole]:
        return list(dict.fromkeys(roles))
