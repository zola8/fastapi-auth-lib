from pydantic import BaseModel


class ErrorDetail(BaseModel):
    description: str
