import os

import uvicorn

from src.fastapi_auth_lib.core.app_builder import AppBuilder
from src.fastapi_auth_lib.core.logging_config import configure_logging

configure_logging()

app = (
    AppBuilder()
    .with_title("My Auth App")
    .with_sql_services()
    # .with_in_memory_services()
    .with_jwt(secret=os.getenv("JWT_SECRET", "dev-only-secret-should-be-super-super-long"), issuer="my-app")
    .with_all_routers()
    .with_health_check()
    .with_exception_handlers()
    .with_cors()
    .with_dummy_email()
    .with_users([
        {
            "email": "admin@test.com",
            "password": "admin123",
            "roles": ["admin", "user"],
        },
        {
            "email": "user@test.com",
            "password": "aaaaaaaa",
            "roles": ["user"],
        },
    ])
    .build()
)

if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
