import logging

from fastapi import APIRouter

from src.fastapi_auth_lib.api.dependencies import AuthServiceDep
from src.fastapi_auth_lib.api.dependencies import EmailServiceDep
from src.fastapi_auth_lib.api.schemas.requests import ActivateUserAccountRequest
from src.fastapi_auth_lib.api.schemas.requests import LoginWithPasswordRequest
from src.fastapi_auth_lib.api.schemas.requests import RefreshTokenRequest
from src.fastapi_auth_lib.api.schemas.requests import RegisterWithPasswordRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _activation_email_body(user_id: str, token: str) -> str:
    return (
        f"UserId: {user_id}\n" +
        f"Token:  {token}"
    )


@router.post("/register/password", status_code=201)
async def register_with_password(
    req: RegisterWithPasswordRequest,
    auth_service: AuthServiceDep,
    email_service: EmailServiceDep
):
    # TODO replace this workflow with IdentityService?
    user = await auth_service.register(req.email, req.password.get_secret_value())
    activation_token = auth_service.create_activation_token(user)

    if email_service is not None:
        await email_service.send_email(
            to=user.email,
            subject="Activate your account",
            body=_activation_email_body(user.user_id, activation_token),
        )

    return {
        "user_id": user.user_id,
        "email": user.email,
        "activation_token": activation_token
    }


@router.post("/activate")
async def activate(req: ActivateUserAccountRequest, auth: AuthServiceDep):
    user = await auth.activate_account(req.token)
    return {
        "user_id": user.user_id,
        "status": user.status
    }


@router.post("/login/password")
async def login(req: LoginWithPasswordRequest, auth: AuthServiceDep):
    user = await auth.authenticate_with_password(req.email, req.password.get_secret_value())
    tokens = auth.create_token_pair(user)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token
    }


@router.post("/refresh")
async def refresh(req: RefreshTokenRequest, auth: AuthServiceDep):
    tokens = await auth.refresh_access_token(req.refresh_token)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token
    }
