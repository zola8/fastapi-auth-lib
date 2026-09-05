import os

import uvicorn

from src.fastapi_auth_lib.api.app_builder import AppBuilder

app = (
    AppBuilder()
    .with_title("My Auth App")
    # .with_sql_services()
    .with_in_memory_services()
    .with_jwt(secret=os.getenv("JWT_SECRET", "dev-only-secret"), issuer="my-app")
    .with_auth_router()
    .with_users_router()
    .with_admin_router()
    .with_exception_handlers()
    .build()
)

if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
