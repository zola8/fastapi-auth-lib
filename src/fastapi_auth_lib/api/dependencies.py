from typing import Annotated

from fastapi import Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_auth_lib.core.exceptions import FeatureNotConfiguredException
from src.fastapi_auth_lib.core.database import get_db_session
from src.fastapi_auth_lib.core.exceptions import AuthenticationException
from src.fastapi_auth_lib.core.exceptions import PermissionDeniedException
from src.fastapi_auth_lib.models.base import UserRole
from src.fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.email.email_protocol import EmailServiceProtocol

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


# ---------------------------------------------------------------------------
# User Service
# ---------------------------------------------------------------------------

async def get_user_service(request: Request, session: SessionDep) -> AsyncUserService:
    """
    In-memory: return the singleton from app.state.
    SQL: call the factory with this request's session.
    """
    singleton = getattr(request.app.state, "user_service", None)
    if singleton is not None:
        return singleton

    factory = getattr(request.app.state, "user_service_factory", None)
    if factory is None:
        raise FeatureNotConfiguredException(
            "User service not configured — call .with_in_memory_services() or .with_sql_services()")
    return factory(session)


UserServiceDep = Annotated[AsyncUserService, Depends(get_user_service)]


# ---------------------------------------------------------------------------
# Auth Service
# ---------------------------------------------------------------------------


async def get_auth_service(
    request: Request,
    session: SessionDep,
    user_service: UserServiceDep,
) -> AsyncAuthService:
    """
    In-memory: return the singleton from app.state.
    SQL: call the factory with this request's session and user service.
    """
    singleton = getattr(request.app.state, "auth_service", None)
    if singleton is not None:
        return singleton

    factory = getattr(request.app.state, "auth_service_factory", None)
    if factory is None:
        raise FeatureNotConfiguredException(
            "Auth service not configured — call .with_in_memory_services() or .with_sql_services()")
    return factory(session, user_service)


AuthServiceDep = Annotated[AsyncAuthService, Depends(get_auth_service)]


# ---------------------------------------------------------------------------
# Email Service
# ---------------------------------------------------------------------------

async def get_email_service(request: Request) -> EmailServiceProtocol | None:
    """
    Returns the configured email service, or None if email is disabled.
    """
    return getattr(request.app.state, "email_service")


EmailServiceDep = Annotated[EmailServiceProtocol | None, Depends(get_email_service)]


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------
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


def require_role(*roles: UserRole | str):
    """
    Access guard: user must have AT LEAST ONE of the given roles.
    Usage: dependencies=[Depends(require_role("admin"))]
    """
    allowed = {UserRole(r) for r in roles}

    async def _check(current_user: CurrentUserDep) -> UserProfile:
        if not (set(current_user.roles) & allowed):
            raise PermissionDeniedException(
                f"Requires one of roles: {[r.value for r in allowed]}"
            )
        return current_user

    return _check
