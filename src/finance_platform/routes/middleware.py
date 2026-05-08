from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = request.headers.get(
            "X-Correlation-Id", str(uuid.uuid4())
        )
        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response


class CompanyContextValidationMiddleware(BaseHTTPMiddleware):
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/auth/register",
        # Frontend pages are served without mandatory company context.
        # They prompt the user to set X-Company-Id for scoped data views.
        "/",
        "/dashboard",
        "/static",
        "/select-company",
        "/expenses",
        "/approvals",
        "/settlements",
        "/frontend-health-check",
    }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        # Allow any frontend path that does not start with /api/
        if not path.startswith("/api/v1/"):
            return await call_next(request)
        if not any(path.startswith(p) for p in self.EXEMPT_PATHS):
            company_id = request.headers.get("X-Company-Id")
            if not company_id or company_id.strip() == "":
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=400,
                    content={
                        "type": "about:blank",
                        "title": "Missing Company Context",
                        "status": 400,
                        "detail": "X-Company-Id header is required",
                        "instance": path,
                    },
                )
        return await call_next(request)
