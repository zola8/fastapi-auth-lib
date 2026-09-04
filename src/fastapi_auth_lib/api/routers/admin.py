import logging

from fastapi import APIRouter

from src.fastapi_auth_lib.api.dependencies import UserServiceDep
from src.fastapi_auth_lib.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("", response_model=list[UserProfile])
async def list_users(service: UserServiceDep):
    return await service.list_users()
