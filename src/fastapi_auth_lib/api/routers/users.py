import logging

from fastapi import APIRouter

from src.fastapi_auth_lib.api.dependencies import CurrentUserDep
from src.fastapi_auth_lib.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
async def whoami(user: CurrentUserDep):
    return user
