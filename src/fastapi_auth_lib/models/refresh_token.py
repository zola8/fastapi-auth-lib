from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from src.fastapi_auth_lib.core.utils import _now


class RefreshToken(BaseModel):
    """
    A stored refresh token session.

    Only the SHA-256 hash of the raw token is persisted.
    """

    model_config = ConfigDict(from_attributes=True)

    refresh_token_id: Optional[int] = Field(
        default=None,
        description="Unique refresh token identifier",
    )
    user_id: UUID = Field(description="Owner of this session")
    token_hash: str = Field(description="SHA-256 hash of the raw refresh token")
    created_at: datetime = Field(default_factory=_now, description="Issued at")
    expires_at: datetime = Field(description="Expiry timestamp (mirrors the JWT exp claim)")
