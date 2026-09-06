from uuid import UUID

from pydantic import BaseModel
from pydantic import EmailStr


class ErrorDetail(BaseModel):
    error_msg: str


class RegisterWithPasswordResponse(BaseModel):
    """Response returned after successful password registration."""

    user_id: UUID
    email: EmailStr
    activation_token: str
