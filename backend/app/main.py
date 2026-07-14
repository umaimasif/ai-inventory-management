"""FastAPI application entrypoint."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.limiter import limiter
from app.services.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

# Import models so their tables are registered on the metadata before create_all.
from app import models  # noqa: F401

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inventory")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hook."""
    if settings.is_production:
        # Production schema is owned by Alembic (`alembic upgrade head`, run by
        # the container entrypoint). Auto-creating tables here would silently
        # diverge from the migration history.
        logger.info("Production mode: schema managed by Alembic migrations.")
    else:
        Base.metadata.create_all(bind=engine)
        logger.info("Development mode: tables ensured via create_all.")
    yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="AI Inventory Management System",
        version="1.0.0",
        description="AI-powered inventory management with a multi-agent layer.",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_error_handlers(app)
    app.include_router(api_router)
    _mount_frontend(app)

    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Map domain exceptions to HTTP responses so routes stay thin."""

    _STATUS = {
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ConflictError: status.HTTP_409_CONFLICT,
        ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    }

    @app.exception_handler(DomainError)
    async def _handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        code = _STATUS.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=code, content={"detail": exc.message})


def _mount_frontend(app: FastAPI) -> None:
    """Serve the exported Next.js frontend from the same origin as the API.

    In the container build, the frontend is statically exported to STATIC_DIR.
    Serving it here means the browser talks to one origin, so no CORS is
    involved. Mounted last so it never shadows /api routes.
    """
    if not settings.STATIC_DIR:
        return

    static_dir = Path(settings.STATIC_DIR)
    if not static_dir.is_dir():
        logger.warning("STATIC_DIR %s does not exist; frontend not served.", static_dir)
        return

    # `html=True` resolves /dashboard/ -> dashboard/index.html (the export uses
    # trailingSlash, so every route is a directory with an index.html).
    app.mount(
        "/", StaticFiles(directory=static_dir, html=True), name="frontend"
    )

    @app.exception_handler(404)
    async def _spa_fallback(request: Request, _exc) -> FileResponse | JSONResponse:
        """Unknown API paths stay JSON 404s; unknown page paths get the app's 404."""
        if request.url.path.startswith("/api"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        not_found = static_dir / "404.html"
        if not_found.is_file():
            return FileResponse(not_found, status_code=404)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    logger.info("Serving frontend from %s", static_dir)


app = create_app()
