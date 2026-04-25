from __future__ import annotations

import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from finance_platform.logging.correlation import (
    COMPANY_ID_KEY,
    CORRELATION_ID_KEY,
    REQUEST_METHOD_KEY,
    REQUEST_PATH_KEY,
    USER_ID_KEY,
    get_current_correlation_id,
    reset_context,
    set_company_id,
)
from finance_platform.logging.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        start = time.monotonic()
        correlation_id = get_current_correlation_id()

        bind_contextvars(
            CORRELATION_ID_KEY=correlation_id,
            REQUEST_PATH_KEY=request.url.path,
            REQUEST_METHOD_KEY=request.method,
        )

        company_id = request.headers.get("X-Company-Id") or request.query_params.get("company_id")
        if company_id:
            bind_contextvars(**{COMPANY_ID_KEY: company_id})

        user_id = request.headers.get("X-User-Id") or request.headers.get("X-Auth-User-Id")
        if user_id:
            bind_contextvars(**{USER_ID_KEY: user_id})

        response: Response = await call_next(request)
        elapsed = time.monotonic() - start

        bind_contextvars(
            status_code=response.status_code,
            elapsed_ms=round(elapsed * 1000, 2),
        )

        if response.status_code >= 500:
            logger.error("request_failed")
        elif response.status_code >= 400:
            logger.warning("request_warning")
        else:
            logger.info("request_completed")

        clear_contextvars()
        return response


class CompanyLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        company_id = request.headers.get("X-Company-Id") or request.query_params.get("company_id")
        if company_id:
            set_company_id(company_id)
            bind_contextvars(**{COMPANY_ID_KEY: company_id})
        response: Response = await call_next(request)
        return response


class LogContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        from finance_platform.logging.binder import get_company_binder

        binder = get_company_binder()

        correlation_id = get_current_correlation_id()
        company_id = request.headers.get("X-Company-Id") or request.query_params.get("company_id")
        user_id = request.headers.get("X-User-Id") or request.headers.get("X-Auth-User-Id")

        ctx = {
            CORRELATION_ID_KEY: correlation_id,
            REQUEST_PATH_KEY: request.url.path,
            REQUEST_METHOD_KEY: request.method,
        }
        if company_id:
            ctx[COMPANY_ID_KEY] = company_id
        if user_id:
            ctx[USER_ID_KEY] = user_id

        with binder.scope(**ctx):
            response: Response = await call_next(request)

        reset_context()
        return response
