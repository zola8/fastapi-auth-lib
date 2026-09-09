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
    """Always identical regardless of outcome (anti-enumeration)."""
    message: str


class RequestPasswordResetResponse(BaseModel):
    """Always identical regardless of outcome (anti-enumeration)."""
    message: str


class ResetPasswordResponse(BaseModel):
    message: str


class LogoutResponse(BaseModel):
    message: str


class TokenPairResponse(BaseModel):
    """Response containing a fresh access + refresh token pair."""

    access_token: str
    refresh_token: str
