from typing import Annotated

from fastapi import Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.core.database import get_db_session
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import PermissionDeniedException
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.email.email_protocol import EmailServiceProtocol
from src.fastapi_auth_lib.services.password_hasher.argon2_hasher import Argon2PasswordHasher
from src.fastapi_auth_lib.services.service_factory import AuthServiceBuilder
from src.fastapi_auth_lib.services.service_factory import UserServiceBuilder

# ---------------------------------------------------------------------------
# Service dependencies
# ---------------------------------------------------------------------------

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_user_service(request: Request, session: SessionDep) -> AsyncUserService:
    """
    In-memory mode: return the singleton from app.state.
    SQL mode: build a fresh service from the request session.
    """
    singleton = getattr(request.app.state, "user_service", None)
    if singleton is not None:
        return singleton
    return UserServiceBuilder().with_sql_session(session).build()


UserServiceDep = Annotated[AsyncUserService, Depends(get_user_service)]


async def get_auth_service(
    request: Request,
    session: SessionDep,
    user_service: UserServiceDep
) -> AsyncAuthService:
    singleton = getattr(request.app.state, "auth_service", None)
    if singleton is not None:
        return singleton  # in-memory mode

    builder = (
        AuthServiceBuilder()
        .with_user_service(user_service)
        .with_sql_session(session)
        .with_password_hasher(Argon2PasswordHasher())
    )

    jwt_config = getattr(request.app.state, "jwt_config", None)
    if jwt_config is not None:
        builder = builder.with_jwt(**jwt_config)

    return builder.build()


async def get_email_service(request: Request) -> EmailServiceProtocol | None:
    """
    Returns the configured email service, or None if email is disabled.
    """
    return getattr(request.app.state, "email_service")


EmailServiceDep = Annotated[EmailServiceProtocol | None, Depends(get_email_service)]

AuthServiceDep = Annotated[AsyncAuthService, Depends(get_auth_service)]


def require_role(*roles: UserRole | str):
    """
    Access guard: user must have AT LEAST ONE of the given roles.

    (Later if I need more: require_all_roles)
    Usage: dependencies=[Depends(require_role("admin"))]
    """
    allowed = {UserRole(r) for r in roles}  # accepts "admin" or UserRole.ADMIN

    async def _check(current_user: CurrentUserDep) -> UserProfile:
        if not (set(current_user.roles) & allowed):
            raise PermissionDeniedException(
                f"Requires one of roles: {[r.value for r in allowed]}"
            )
        return current_user

    return _check


async def get_current_user(
    request: Request,
    auth_service: AuthServiceDep,
) -> UserProfile:
    header = request.headers.get("Authorization")
    if not header or not header.startswith("Bearer "):
        raise AuthenticationException("Missing bearer token")
    token = header.removeprefix("Bearer ").strip()
    return await auth_service.get_user_from_access_token(token)


CurrentUserDep = Annotated[UserProfile, Depends(get_current_user)]
