import logging

from fastapi import APIRouter

from src.fastapi_auth_lib.api.dependencies import AuthServiceDep
from src.fastapi_auth_lib.api.schemas.requests import RegisterWithPasswordRequest
from src.fastapi_auth_lib.models.user import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/password", response_model=UserProfile, status_code=201)
async def register_with_password(req: RegisterWithPasswordRequest, auth_service: AuthServiceDep):
    return await auth_service.register(email=req.email, password=req.password.get_secret_value())
