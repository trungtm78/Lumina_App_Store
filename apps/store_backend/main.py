"""Lumina App Store — FastAPI application."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .routers import apps, admin, authoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lumina App Store starting up")
    yield
    logger.info("Lumina App Store shutting down")


app = FastAPI(
    title="Lumina App Store",
    version="0.1.0",
    description="Marketplace API for Lumina ecosystem addons",
    lifespan=lifespan,
)

# Routers
app.include_router(apps.router)
app.include_router(admin.router)
app.include_router(authoring.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())[:8]
    logger.error("Unhandled error [%s]: %s", request_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": request_id,
            }
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "lumina-app-store"}
