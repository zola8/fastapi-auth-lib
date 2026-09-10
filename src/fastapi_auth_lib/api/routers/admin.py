import logging
import uuid

from fastapi import APIRouter
from fastapi import Depends

from src.fastapi_auth_lib.api.dependencies import UserServiceDep
from src.fastapi_auth_lib.api.dependencies import require_role
from src.fastapi_auth_lib.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=list[UserProfile],
    dependencies=[Depends(require_role("admin"))]
)
async def list_users(user_service: UserServiceDep):
    return await user_service.list_users()


@router.get(
    "/get/{user_id}",
    response_model=UserProfile,
    dependencies=[Depends(require_role("admin"))]
)
async def get_user(user_id: uuid.UUID, user_service: UserServiceDep):
    return await user_service.get_user(user_id)
