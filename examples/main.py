from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.fastapi_auth_lib.core.database import create_tables
from src.fastapi_auth_lib.core.database import dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await dispose_engine()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def index_page():
    return {"status": "ok"}


if __name__ == '__main__':
    print("http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=8080)
