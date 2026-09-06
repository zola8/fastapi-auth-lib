from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr

from src.fastapi_auth_lib.models.base import UserStatus


class ErrorDetail(BaseModel):
    error_msg: str


class RegisterWithPasswordResponse(BaseModel):
    """Response returned after successful password registration."""

    user_id: UUID
    email: EmailStr
    activation_token: str


class ActivateUserAccountResponse(BaseModel):
    """Response returned after successful account activation."""

    user_id: UUID
    status: UserStatus


class ResendActivationResponse(BaseModel):
    """Always identical regardless of outcome (prevents account enumeration)."""

    message: str
