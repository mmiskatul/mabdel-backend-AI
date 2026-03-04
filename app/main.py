from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import MongoClientManager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    MongoClientManager.get_client()
    try:
        yield
    finally:
        MongoClientManager.close_client()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()

