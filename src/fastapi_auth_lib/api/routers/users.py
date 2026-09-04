import logging
import uuid

from fastapi import APIRouter

from src.fastapi_auth_lib.api.dependencies import UserServiceDep
from src.fastapi_auth_lib.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(user_id: uuid.UUID, user_service: UserServiceDep):
    return await user_service.get_user(user_id)
