import logging

from fastapi import APIRouter
from fastapi import status

from src.fastapi_auth_lib.api.dependencies import AuthServiceDep
from src.fastapi_auth_lib.api.dependencies import EmailServiceDep
from src.fastapi_auth_lib.api.schemas.requests import ActivateUserAccountRequest
from src.fastapi_auth_lib.api.schemas.requests import LoginWithPasswordRequest
from src.fastapi_auth_lib.api.schemas.requests import RefreshTokenRequest
from src.fastapi_auth_lib.api.schemas.requests import RegisterWithPasswordRequest
from src.fastapi_auth_lib.api.schemas.requests import ResendActivationRequest
from src.fastapi_auth_lib.api.schemas.responses import ActivateUserAccountResponse
from src.fastapi_auth_lib.api.schemas.responses import RegisterWithPasswordResponse
from src.fastapi_auth_lib.api.schemas.responses import ResendActivationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _email_body(user_id: str, token: str) -> str:
    return (
        f"UserId: {user_id}\n" +
        f"Token:  {token}"
    )


@router.post("/register/password", status_code=status.HTTP_201_CREATED)
async def register_with_password(
    req: RegisterWithPasswordRequest,
    auth_service: AuthServiceDep,
    email_service: EmailServiceDep
):
    logger.debug("POST /register/password for email: %s", req.email)
    # TODO replace this workflow with IdentityService?
    user = await auth_service.register(req.email, req.password.get_secret_value())
    activation_token = auth_service.create_activation_token(user)

    if email_service is not None:
        await email_service.send_email(
            to=user.email,
            subject="Activate your account",
            body=_email_body(user.user_id, activation_token),
        )

    return RegisterWithPasswordResponse(
        user_id=user.user_id,
        email=user.email,
        activation_token=activation_token,
    )


@router.post("/activate")
async def activate(req: ActivateUserAccountRequest, auth_service: AuthServiceDep):
    logger.debug("POST /auth/activate for token: %s", req.activation_token)
    user = await auth_service.activate_account(req.token)

    return ActivateUserAccountResponse(
        user_id=user.user_id,
        status=user.status,
    )


@router.post(
    "/resend-activation",
    response_model=ResendActivationResponse,
    status_code=status.HTTP_200_OK,
)
async def resend_activation(
    req: ResendActivationRequest,
    auth_service: AuthServiceDep,
    email_service: EmailServiceDep,
) -> ResendActivationResponse:
    logger.debug("POST /auth/resend-activation for email: %s", req.email)

    result = await auth_service.resend_activation(req.email)

    if result is not None:
        user, token = result
        if email_service is not None:
            await email_service.send_email(
                to=user.email,
                subject="Activate your account",
                body=_email_body(user.user_id, token),
            )

    # Identical response in ALL cases
    return ResendActivationResponse(
        message="If your account exists and is inactive, an activation email has been sent."
    )


@router.post("/login/password")
async def login(req: LoginWithPasswordRequest, auth_service: AuthServiceDep):
    user = await auth_service.authenticate_with_password(req.email, req.password.get_secret_value())
    tokens = auth_service.create_token_pair(user)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token
    }


@router.post("/refresh")
async def refresh(req: RefreshTokenRequest, auth_service: AuthServiceDep):
    tokens = await auth_service.refresh_access_token(req.refresh_token)
    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token
    }
