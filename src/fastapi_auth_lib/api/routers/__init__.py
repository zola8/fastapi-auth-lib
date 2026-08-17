from .admin import router as admin_router
from .auth import router as auth_router
from .users import router as user_router

__all__ = [
    "user_router",
    "auth_router",
    "admin_router",
]
