from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import agent, auth, users
from app.application.services.auth_service import ensure_seed_admin
from app.persistence.indexes import ensure_indexes
from app.persistence.mongo import MongoManager
from app.persistence.repositories import MongoRepository
from app.shared.config import get_settings
from app.shared.errors import AppError
from app.shared.logging import configure_logging

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    db = MongoManager.db()
    await ensure_indexes(db)
    await ensure_seed_admin(MongoRepository())
    yield
    await MongoManager.close()


def create_app() -> FastAPI:
    settings_obj = get_settings()
    app = FastAPI(title=settings_obj.app_name, lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(auth.customer_router, prefix="/api/v1")
    app.include_router(auth.admin_router, prefix="/api/v1")
    app.include_router(agent.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @app.get("/voice-agent-test", include_in_schema=False)
    async def voice_agent_test():
        return FileResponse(STATIC_DIR / "voice-agent-test" / "index.html")

    return app


app = create_app()
