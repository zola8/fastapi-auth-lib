import uvicorn
from fastapi import FastAPI

from fastapi_auth_lib.api.routers import admin_router
from fastapi_auth_lib.api.routers import auth_router
from fastapi_auth_lib.api.routers import user_router
from fastapi_auth_lib.core import configure_logging

app = FastAPI()

configure_logging()

app.include_router(user_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
def index_page():
    return {"status": "ok"}


if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
