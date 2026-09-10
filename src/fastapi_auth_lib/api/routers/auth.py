import logging

from fastapi import APIRouter
from fastapi import Query
from fastapi import status

from fastapi_auth_lib.api.dependencies import CurrentUserDep
from fastapi_auth_lib.api.schemas.requests import RefreshTokenRequest
from fastapi_auth_lib.api.schemas.responses import LogoutResponse
from fastapi_auth_lib.api.schemas.responses import TokenPairResponse
from src.fastapi_auth_lib.api.dependencies import AuthServiceDep
from src.fastapi_auth_lib.api.dependencies import EmailServiceDep
from src.fastapi_auth_lib.api.schemas.requests import LoginWithPasswordRequest
from src.fastapi_auth_lib.api.schemas.requests import RegisterWithPasswordRequest
from src.fastapi_auth_lib.api.schemas.requests import RequestPasswordResetRequest
from src.fastapi_auth_lib.api.schemas.requests import ResendActivationRequest
from src.fastapi_auth_lib.api.schemas.requests import ResetPasswordRequest
from src.fastapi_auth_lib.api.schemas.responses import ActivateUserAccountResponse
from src.fastapi_auth_lib.api.schemas.responses import RegisterWithPasswordResponse
from src.fastapi_auth_lib.api.schemas.responses import RequestPasswordResetResponse
from src.fastapi_auth_lib.api.schemas.responses import ResendActivationResponse
from src.fastapi_auth_lib.api.schemas.responses import ResetPasswordResponse

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
    activation_token = await auth_service.create_activation_token(user)

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


@router.get(
    "/activate",
    response_model=ActivateUserAccountResponse,
    status_code=status.HTTP_200_OK,
)
async def activate_account(
    token: str = Query(min_length=1, description="Activation token received after registration"),
    auth_service: AuthServiceDep = None,
) -> ActivateUserAccountResponse:
    user = await auth_service.activate_account(token)

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
    # TODO replace this workflow with IdentityService?
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


@router.post(
    "/forgot-password",
    response_model=RequestPasswordResetResponse,
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(
    req: RequestPasswordResetRequest,
    auth_service: AuthServiceDep,
    email_service: EmailServiceDep,
) -> RequestPasswordResetResponse:
    logger.debug("POST /auth/forgot-password")

    result = await auth_service.request_password_reset(req.email)

    if result is not None:
        user, token = result
        if email_service is not None:
            await email_service.send_email(
                to=user.email,
                subject="Reset your password",
                body=_email_body(user.user_id, token),
            )

    return RequestPasswordResetResponse(
        message="If this email is registered, a reset link will be sent."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    req: ResetPasswordRequest,
    auth_service: AuthServiceDep,
) -> ResetPasswordResponse:
    logger.debug("POST /auth/reset-password")

    await auth_service.reset_password(
        token=req.token,
        new_password=req.new_password.get_secret_value(),
    )

    return ResetPasswordResponse(message="Password updated successfully.")


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@router.post(
    "/login/password",
    response_model=TokenPairResponse,
    status_code=status.HTTP_200_OK,
)
async def login_with_password(
    req: LoginWithPasswordRequest,
    auth_service: AuthServiceDep,
) -> TokenPairResponse:
    # TODO replace this workflow with IdentityService?
    logger.debug("POST /auth/login/password")

    user = await auth_service.authenticate_with_password(
        email=req.email,
        password=req.password.get_secret_value(),
    )
    token_pair = await auth_service.create_token_pair(user)

    return TokenPairResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


# ---------------------------------------------------------------------------
# Refresh (stateful with rotation)
# ---------------------------------------------------------------------------
@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_tokens(
    req: RefreshTokenRequest,
    auth_service: AuthServiceDep,
) -> TokenPairResponse:
    logger.debug("POST /auth/refresh")

    token_pair = await auth_service.refresh_access_token(req.refresh_token)

    return TokenPairResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )


# ---------------------------------------------------------------------------
# Logout — single session
# ---------------------------------------------------------------------------
@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(
    req: RefreshTokenRequest,
    auth_service: AuthServiceDep,
    current_user: CurrentUserDep,
) -> LogoutResponse:
    logger.debug("POST /auth/logout")

    await auth_service.logout(req.refresh_token)

    return LogoutResponse(message="Session revoked successfully.")


# ---------------------------------------------------------------------------
# Logout — all sessions
# ---------------------------------------------------------------------------
@router.post(
    "/logout-everywhere",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
async def logout_everywhere(
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> LogoutResponse:
    logger.debug("POST /auth/logout-everywhere")

    await auth_service.logout_all_sessions(current_user.user_id)

    return LogoutResponse(message="All sessions revoked successfully.")
