import logging
from typing import Any, Annotated, Optional

from fastapi import Depends

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service dependencies
# ---------------------------------------------------------------------------

async def get_auth_service() -> Any:
    """
    Placeholder auth service dependency.
    """
    logger.debug("Dependency called: get_auth_service")
    return None


async def get_user_service() -> Any:
    """
    Placeholder user service dependency.
    """
    logger.debug("Dependency called: get_user_service")
    return None


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

async def get_current_logged_in_user() -> Optional[str]:
    """
    Placeholder dependency for the current logged-in user.
    """
    logger.debug("Dependency called: get_current_logged_in_user")
    return None


# ---------------------------------------------------------------------------
# Type Aliases for clean routers
# ---------------------------------------------------------------------------

AuthServiceDep = Annotated[Any, Depends(get_auth_service),]
UserServiceDep = Annotated[Any, Depends(get_user_service),]

CurrentLoggedInUserId = Annotated[Optional[str], Depends(get_current_logged_in_user),]
