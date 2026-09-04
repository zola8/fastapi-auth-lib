from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.fastapi_auth_lib.api.exception_handlers import register_exception_handlers
from src.fastapi_auth_lib.api.routers.admin import router as admin_router
from src.fastapi_auth_lib.api.routers.auth import router as auth_router
from src.fastapi_auth_lib.api.routers.users import router as user_router
from src.fastapi_auth_lib.core.database import create_tables
from src.fastapi_auth_lib.core.database import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await dispose_engine()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)

app.include_router(user_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/")
def index_page():
    return {"status": "ok"}


if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
