import logging

from fastapi import APIRouter
from fastapi import status

from fastapi_auth_lib.api.dependencies import AuthServiceDep
from fastapi_auth_lib.api.schemas.requests import ActivationRequest
from fastapi_auth_lib.api.schemas.requests import LoginWithPasswordRequest
from fastapi_auth_lib.api.schemas.requests import RefreshTokenRequest
from fastapi_auth_lib.api.schemas.requests import RegisterWithPasswordRequest
from fastapi_auth_lib.api.schemas.requests import ResetPasswordRequest
from fastapi_auth_lib.api.schemas.responses import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register/password",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_with_password(
    req: RegisterWithPasswordRequest,
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("POST /auth/register/password, request: %s", req)

    # TODO: call auth service
    # await _service.register_with_password(req)

    return ApiResponse(success=True, data=None)


@router.post(
    "/login/password",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    req: LoginWithPasswordRequest,
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("POST /auth/login/password, request: %s", req)

    # TODO: call auth service
    # await _service.login(req)

    return ApiResponse(success=True, data=None)


@router.get(
    "/logout",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("GET /auth/logout")

    # TODO: call auth service
    # await _service.logout(req)

    return ApiResponse(success=True, data=None)


@router.post(
    "/refresh-token",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    req: RefreshTokenRequest,
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("POST /auth/refresh, request: %s", req)

    # TODO: call auth service
    # await _service.refresh_token(req)

    return ApiResponse(success=True, data=None)


@router.post(
    "/activate",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def activate_user_account(
    req: ActivationRequest,
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("POST /auth/activate, request: %s", req)

    # TODO: call auth service
    # await _service.activate_user_account(req)

    return ApiResponse(success=True, data=None)


@router.post(
    "/resend-activation",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def resend_activation(
    req: ActivationRequest,
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("POST /auth/resend-activation, request: %s", req)

    # TODO: call auth service
    # await _service.resend_activation(req)

    return ApiResponse(success=True, data=None)


@router.post(
    "/reset-password",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    req: ResetPasswordRequest,
    _service: AuthServiceDep,
) -> ApiResponse:
    logger.debug("POST /auth/forgot-password, request: %s", req)

    # TODO: call auth service
    # await _service.reset_password(req)

    return ApiResponse(success=True, data=None)
