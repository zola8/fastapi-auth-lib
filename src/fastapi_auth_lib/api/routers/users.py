import logging

from fastapi import APIRouter
from fastapi import status

from fastapi_auth_lib.api.dependencies import CurrentLoggedInUserId
from fastapi_auth_lib.api.dependencies import UserServiceDep
from fastapi_auth_lib.api.schemas.requests import UserUpdateRequest
from fastapi_auth_lib.api.schemas.responses import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# /me routes
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def get_me(
    user_id: CurrentLoggedInUserId,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("GET /users/me, user_id: %s", user_id)

    if user_id is None:
        return ApiResponse(success=True, data=None)

    return await get_user(
        user_id=user_id,
        _service=_service,
    )


@router.patch(
    "/me",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def update_me(
    req: UserUpdateRequest,
    user_id: CurrentLoggedInUserId,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("PATCH /users/me, user_id: %s, request: %s", user_id, req)

    if user_id is None:
        return ApiResponse(success=True, data=None)

    return await update_user(
        req=req,
        user_id=user_id,
        _service=_service,
    )


@router.delete(
    "/me",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_me(
    user_id: CurrentLoggedInUserId,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("DELETE /users/me, user_id: %s", user_id)

    if user_id is None:
        return ApiResponse(success=True, data=None)

    return await delete_user(
        user_id=user_id,
        _service=_service,
    )


# ---------------------------------------------------------------------------
# /{user_id} routes
# ---------------------------------------------------------------------------


@router.get(
    "/{user_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user(
    user_id: str,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("GET /users/%s", user_id)

    # TODO: call user service
    # await _service.get_user(user_id)

    return ApiResponse(success=True, data=None)


@router.patch(
    "/{user_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    req: UserUpdateRequest,
    user_id: str,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("PATCH /users/%s, request: %s", user_id, req)

    # TODO: call user service
    # await _service.update_user(user_id, req)

    return ApiResponse(success=True, data=None)


@router.delete(
    "/{user_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_id: str,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("DELETE /users/%s", user_id)

    # TODO: call user service
    # await _service.delete_user(user_id)

    return ApiResponse(success=True, data=None)
