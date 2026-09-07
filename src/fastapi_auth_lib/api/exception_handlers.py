from fastapi import FastAPI
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.fastapi_auth_lib.api.schemas.responses import ErrorDetail
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.core.exceptions import FeatureNotConfiguredException
from src.fastapi_auth_lib.core.exceptions import TokenException


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(EntityNotFoundException)
    async def handle_not_found(request: Request, exc: EntityNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorDetail(error_msg=exc.description).model_dump(),
        )

    @app.exception_handler(DuplicateEntityException)
    async def handle_duplicate(request: Request, exc: DuplicateEntityException):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorDetail(error_msg=exc.description).model_dump(),
        )

    @app.exception_handler(AuthenticationException)
    async def handle_auth_failed(request: Request, exc: AuthenticationException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorDetail(error_msg=exc.description).model_dump(),
        )

    @app.exception_handler(TokenException)
    async def handle_token(request: Request, exc: TokenException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorDetail(error_msg=exc.description).model_dump(),
        )

    @app.exception_handler(FeatureNotConfiguredException)
    async def handle_feature(request: Request, exc: FeatureNotConfiguredException):
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content=ErrorDetail(error_msg=exc.description).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Convert Pydantic 422 errors into a single ErrorDetail response."""
        messages = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            msg = error["msg"]
            messages.append(f"{field}: {msg}" if field else msg)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorDetail(error_msg="; ".join(messages)).model_dump(),
        )
