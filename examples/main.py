import os

import uvicorn

from src.fastapi_auth_lib.core.app_builder import AppBuilder

app = (
    AppBuilder()
    .with_title("My Auth App")
    # .with_sql_services()
    .with_in_memory_services()
    .with_jwt(secret=os.getenv("JWT_SECRET", "dev-only-secret-should-be-super-super-long"), issuer="my-app")
    .with_all_routers()
    .with_health_check()
    .with_exception_handlers()
    .with_cors()
    .build()
)

if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
