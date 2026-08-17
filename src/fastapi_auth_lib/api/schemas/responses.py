from typing import Generic, Optional, Any, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
