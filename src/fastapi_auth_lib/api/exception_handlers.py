from fastapi import FastAPI
from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.fastapi_auth_lib.api.schemas.responses import ErrorDetail
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import DuplicateEntityException
from src.fastapi_auth_lib.core.exceptions import EntityNotFoundException
from src.fastapi_auth_lib.core.exceptions import TokenException


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(EntityNotFoundException)
    async def handle_not_found(request: Request, exc: EntityNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorDetail(description=exc.description).model_dump(),
        )

    @app.exception_handler(DuplicateEntityException)
    async def handle_duplicate(request: Request, exc: DuplicateEntityException):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorDetail(description=exc.description).model_dump(),
        )

    @app.exception_handler(AuthenticationException)
    async def handle_auth_failed(request: Request, exc: AuthenticationException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorDetail(description=exc.description).model_dump(),
        )

    @app.exception_handler(TokenException)
    async def handle_token(request: Request, exc: TokenException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorDetail(description=exc.description).model_dump(),
        )
