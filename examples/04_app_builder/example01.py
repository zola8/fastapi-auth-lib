import os

import uvicorn
from fastapi import APIRouter

from fastapi_auth_lib.api.dependencies import UserServiceDep
from fastapi_auth_lib.models.user import UserProfile
from src.fastapi_auth_lib.core.app_builder import AppBuilder
from src.fastapi_auth_lib.core.logging_config import configure_logging

configure_logging()

# 1. In-Memory App (development / testing)

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/users", response_model=list[UserProfile])
async def list_users(user_service: UserServiceDep):
    return await user_service.list_users()


app = (
    AppBuilder()
    .with_title("Auth Demo (In-Memory)")
    .with_version("0.1.0")
    .with_in_memory_services()
    .with_jwt(
        secret=os.getenv("JWT_SECRET", "dev-secret-do-not-use-in-prod"),
        issuer="auth-demo",
    )
    .with_dummy_email()
    .with_users([
        {"email": "admin@test.com", "password": "a" * 8, "roles": ["admin"]},
        {"email": "user@test.com", "password": "a" * 8, "roles": ["user"]},
    ])
    .with_all_routers()
    .with_router(router)
    .with_exception_handlers()
    .with_cors()
    .with_health_check()
    .build()
)

if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
