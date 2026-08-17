import logging

from fastapi import APIRouter
from fastapi import status

from fastapi_auth_lib.api.dependencies import UserServiceDep
from fastapi_auth_lib.api.schemas.requests import UserUpdateRequest
from fastapi_auth_lib.api.schemas.responses import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# TODO add authorization later

@router.get(
    "/users",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def list_all_users(
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("GET /admin/users")

    # await _service.list_all_users()

    return ApiResponse(success=True, data=None)


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def admin_get_user(
    user_id: str,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("GET /admin/users/%s", user_id)

    # await _service.get_user(user_id)

    return ApiResponse(success=True, data=None)


@router.patch(
    "/users/{user_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def admin_update_user(
    req: UserUpdateRequest,
    user_id: str,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("PATCH /admin/users/%s, request: %s", user_id, req)

    # await _service.update_user(user_id, req)

    return ApiResponse(success=True, data=None)


@router.delete(
    "/users/{user_id}",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def admin_delete_user(
    user_id: str,
    _service: UserServiceDep,
) -> ApiResponse:
    logger.debug("DELETE /admin/users/%s", user_id)

    # await _service.delete_user(user_id)

    return ApiResponse(success=True, data=None)
