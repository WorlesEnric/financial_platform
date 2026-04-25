from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

CORRELATION_ID_KEY = "correlation_id"
COMPANY_ID_KEY = "company_id"
REQUEST_PATH_KEY = "request_path"
REQUEST_METHOD_KEY = "request_method"
USER_ID_KEY = "user_id"
SESSION_ID_KEY = "session_id"
TENANT_ID_KEY = "tenant_id"
SOURCE_IP_KEY = "source_ip"
USER_AGENT_KEY = "user_agent"

_correlation_id_var: ContextVar[Optional[str]] = ContextVar(CORRELATION_ID_KEY, default=None)
_company_id_var: ContextVar[Optional[str]] = ContextVar(COMPANY_ID_KEY, default=None)
_user_id_var: ContextVar[Optional[str]] = ContextVar(USER_ID_KEY, default=None)


def generate_correlation_id() -> str:
    return str(uuid.uuid4())


def get_current_correlation_id() -> Optional[str]:
    return _correlation_id_var.get()


def set_correlation_id(cid: str) -> None:
    _correlation_id_var.set(cid)


def get_current_company_id() -> Optional[str]:
    return _company_id_var.get()


def set_company_id(cid: str) -> None:
    _company_id_var.set(cid)
    bind_contextvars(**{COMPANY_ID_KEY: cid})


def get_current_user_id() -> Optional[str]:
    return _user_id_var.get()


def set_user_id(uid: str) -> None:
    _user_id_var.set(uid)
    bind_contextvars(**{USER_ID_KEY: uid})


def get_correlation_id_context() -> dict:
    return {
        CORRELATION_ID_KEY: get_current_correlation_id(),
        COMPANY_ID_KEY: get_current_company_id(),
        USER_ID_KEY: get_current_user_id(),
    }


def reset_context() -> None:
    clear_contextvars()
    _correlation_id_var.set(None)
    _company_id_var.set(None)
    _user_id_var.set(None)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_name: str = "X-Correlation-Id") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next) -> Response:
        reset_context()

        correlation_id = request.headers.get(self.header_name) or generate_correlation_id()
        _correlation_id_var.set(correlation_id)

        bind_contextvars(
            **{
                CORRELATION_ID_KEY: correlation_id,
                REQUEST_PATH_KEY: request.url.path,
                REQUEST_METHOD_KEY: request.method,
                SOURCE_IP_KEY: request.client.host if request.client else "unknown",
                USER_AGENT_KEY: request.headers.get("user-agent", "unknown"),
            }
        )

        response: Response = await call_next(request)
        response.headers[self.header_name] = correlation_id
        reset_context()
        return response
