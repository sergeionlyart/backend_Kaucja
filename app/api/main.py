"""FastAPI application factory for /api/v2."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .errors import register_error_handlers
from .router import router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Mobal Kaucja API v2",
        version="0.1.0",
        docs_url="/api/v2/docs",
        openapi_url="/api/v2/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(application)
    application.include_router(router)
    return application


app = create_app()
