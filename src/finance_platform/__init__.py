from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from finance_platform.routes.middleware import CorrelationIdMiddleware, CompanyContextValidationMiddleware
from finance_platform.routes import init_routes, mount_all_routes

__all__ = [
    "create_app",
]


def create_app() -> FastAPI:
    from finance_platform.logging.configuration import configure_logging
    from finance_platform.errors.handler import register_error_handlers

    configure_logging()

    app = FastAPI(
        title="Finance Platform",
        description="Enterprise Financial Reimbursement + Amortization Platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(CompanyContextValidationMiddleware)

    # Mount static files for the Jinja2 frontend
    try:
        app.mount("/static", StaticFiles(directory="src/finance_platform/static"), name="static")
    except RuntimeError:
        # Static directory may not exist if package is not installed in editable mode
        pass

    init_routes()
    mount_all_routes(app)

    register_error_handlers(app)

    return app
