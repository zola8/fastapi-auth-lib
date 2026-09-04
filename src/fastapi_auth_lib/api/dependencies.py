import logging
from typing import Annotated
from typing import Optional

from fastapi import Depends

from src.fastapi_auth_lib.services.async_auth_service import AsyncAuthService
from src.fastapi_auth_lib.services.async_user_service import AsyncUserService
from src.fastapi_auth_lib.services.service_factory import AuthServiceBuilder
from src.fastapi_auth_lib.services.service_factory import UserServiceBuilder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton in-memory services for the application lifecycle
# Built once at module load via the builders; shared across all requests.
# ---------------------------------------------------------------------------
_user_service: AsyncUserService = UserServiceBuilder().build()

_auth_service: AsyncAuthService = (
    AuthServiceBuilder()
    .with_user_service(_user_service)
    .build()
)

# TODO check DB session
# from src.fastapi_auth_lib.database import get_db_session, SessionDep
#
# async def get_user_service(session: SessionDep) -> AsyncUserService:
#     return UserServiceBuilder().with_sql_session(session).build()
#
# async def get_auth_service(
#     session: SessionDep,
#     user_service: Annotated[AsyncUserService, Depends(get_user_service)],
# ) -> AsyncAuthService:
#     return (
#         AuthServiceBuilder()
#         .with_user_service(user_service)
#         .with_sql_session(session)
#         .build()
#     )

# ---------------------------------------------------------------------------
# Service dependencies
# ---------------------------------------------------------------------------
async def get_user_service() -> AsyncUserService:
    """Provides the UserService backed by in-memory repositories."""
    logger.debug("Dependency called: get_user_service")
    return _user_service


async def get_auth_service() -> AsyncAuthService:
    """Provides the AuthService backed by in-memory repositories."""
    logger.debug("Dependency called: get_auth_service")
    return _auth_service


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------
async def get_current_logged_in_user() -> Optional[str]:
    """Placeholder dependency for the current logged-in user."""
    logger.debug("Dependency called: get_current_logged_in_user")
    return None


# ---------------------------------------------------------------------------
# Type Aliases for clean routers
# ---------------------------------------------------------------------------
AuthServiceDep = Annotated[AsyncAuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[AsyncUserService, Depends(get_user_service)]
CurrentLoggedInUserId = Annotated[Optional[str], Depends(get_current_logged_in_user)]
