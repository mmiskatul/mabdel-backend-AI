from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routers import (
    agent,
    automations,
    auth,
    calendar,
    calls,
    commands,
    conversations,
    dashboard,
    documents,
    group,
    home,
    integrations,
    messages,
    settings,
    voice,
    webhooks,
)
from app.api.websocket.routes import router as ws_router
from app.infrastructure.db.indexes import ensure_indexes
from app.infrastructure.db.mongo import MongoManager
from app.shared.config import get_settings
from app.shared.errors import AppError
from app.shared.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    db = MongoManager.db()
    await ensure_indexes(db)
    yield
    await MongoManager.close()


def create_app() -> FastAPI:
    settings_obj = get_settings()
    app = FastAPI(title=settings_obj.app_name, lifespan=lifespan)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(automations.router, prefix="/api/v1")
    app.include_router(integrations.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(calendar.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(calls.router, prefix="/api/v1")
    app.include_router(commands.router, prefix="/api/v1")
    app.include_router(agent.router, prefix="/api/v1")
    app.include_router(settings.router, prefix="/api/v1")
    app.include_router(home.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(voice.router, prefix="/api/v1")
    app.include_router(group.router, prefix="/api/v1")
    app.include_router(ws_router)

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
