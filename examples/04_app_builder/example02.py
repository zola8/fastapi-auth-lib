import os

import uvicorn

from src.fastapi_auth_lib.core.app_builder import AppBuilder
from src.fastapi_auth_lib.core.logging_config import configure_logging

configure_logging()

# 2. SQL App (production / persistent)

app = (
    AppBuilder()
    .with_title("Auth API")
    .with_version("1.0.0")
    .with_sql_services()
    # tables created on startup,
    # engine disposed on shutdown
    .with_jwt(
        secret=os.getenv("JWT_SECRET", "dev-secret-do-not-use-in-prod"), # for this example only
        issuer="auth-api",
    )
    .with_email_service(None)  # or a real SmtpEmailService later
    .with_all_routers()
    .with_exception_handlers()
    .with_cors(
        origins=["https://myapp.example.com"],  # explicit origins in prod
    )
    .with_health_check()
    .build()
)

if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
