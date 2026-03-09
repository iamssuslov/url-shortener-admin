from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from .db import init_db, engine
from .middleware import RequestIDMiddleware
from .models import ApiKey
from .routes_api import router as api_router
from .routes_ui import router as ui_router
from .settings import settings
from .logging_config import setup_logging

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application startup initiated")
    init_db()

    with Session(engine) as session:
        existing = session.exec(select(ApiKey).where(ApiKey.name == "default")).first()
        if not existing:
            default_key = ApiKey(
                name="default",
                key=settings.default_api_key,
                is_active=True,
            )
            session.add(default_key)
            session.commit()
            logger.info("Default API key created")
        else:
            logger.info("Default API key already exists")

    logger.info("Application startup completed")
    yield
    logger.info("Application shutdown")


def create_app() -> FastAPI:
    app = FastAPI(title="URL Shortener", lifespan=lifespan)
    app.add_middleware(RequestIDMiddleware)
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(api_router)
    app.include_router(ui_router)

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={"detail": "Not Found"},
            )

        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": 404,
                "title": "Page not found",
                "message": "The page or resource you requested does not exist or is no longer available.",
            },
            status_code=404,
        )

    @app.exception_handler(401)
    async def unauthorized_handler(request: Request, exc):
        if request.url.path.startswith("/api/"):
            detail = getattr(exc, "detail", "Unauthorized")
            return JSONResponse(
                status_code=401,
                content={"detail": detail},
            )

        return templates.TemplateResponse(
            request,
            "error.html",
            {
                "status_code": 401,
                "title": "Unauthorized",
                "message": "You need valid credentials to access this area.",
            },
            status_code=401,
        )

    return app


app = create_app()