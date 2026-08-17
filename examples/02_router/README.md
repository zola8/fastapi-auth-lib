# FastAPI Auth Lib - Quick Start

A minimal FastAPI application using `fastapi_auth_lib` with built-in authentication routers.

## Router usage

```python
import uvicorn
from fastapi import FastAPI

from fastapi_auth_lib.api.routers import admin_router
from fastapi_auth_lib.api.routers import auth_router
from fastapi_auth_lib.api.routers import user_router
from fastapi_auth_lib.core import configure_logging

app = FastAPI()

configure_logging()

# Add routers
app.include_router(user_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
def index_page():
    return {"status": "ok"}


if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Features

- Authentication: Built-in auth routes for login, registration, and token management
- User Management: User profile and account management endpoints
- Admin Routes: Admin-only endpoints for user administration
- Logging: Pre-configured logging with configure_logging()

## API Endpoints

| Router       | Prefix | Description                                       |
|--------------|--------|---------------------------------------------------|
| auth_router  | /auth  | Authentication (login, register, refresh, logout) |
| user_router  | /users | User profile and account management               |
| admin_router | /admin | Admin-only user management                        |

