import logging
from typing import Annotated
from typing import Optional

from fastapi import Depends
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_auth_lib.core.database import get_db_session
from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.service_factory import AuthServiceBuilder
from src.fastapi_auth_lib.services.service_factory import UserServiceBuilder

logger = logging.getLogger(__name__)

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


async def get_auth_service(
    request: Request,
    session: SessionDep,
    user_service: Annotated[AsyncUserService, Depends(get_user_service)],
) -> AsyncAuthService:
    singleton = getattr(request.app.state, "auth_service", None)
    if singleton is not None:
        return singleton
    return (
        AuthServiceBuilder()
        .with_user_service(user_service)
        .with_sql_session(session)
        .build()
    )


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

async def get_current_logged_in_user() -> Optional[str]:
    """Placeholder dependency for the current logged-in user."""
    return None


# ---------------------------------------------------------------------------
# Type Aliases for clean routers
# ---------------------------------------------------------------------------
AuthServiceDep = Annotated[AsyncAuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[AsyncUserService, Depends(get_user_service)]
CurrentLoggedInUserId = Annotated[Optional[str], Depends(get_current_logged_in_user)]
