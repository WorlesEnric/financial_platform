from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from finance_platform.errors.base import FinancePlatformError
from finance_platform.errors.exceptions import (
    AuthError,
    AuthorizationError,
    BusinessRuleError,
    ConfigurationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from finance_platform.errors.registry import ErrorRegistry


class ErrorContext:
    def __init__(self) -> None:
        self._error_id: Optional[str] = None
        self._correlation_id: Optional[str] = None

    @property
    def error_id(self) -> str:
        if self._error_id is None:
            self._error_id = str(uuid.uuid4())
        return self._error_id

    @property
    def correlation_id(self) -> Optional[str]:
        return self._correlation_id

    @correlation_id.setter
    def correlation_id(self, value: str) -> None:
        self._correlation_id = value


def format_error_response(
    status_code: int,
    detail: str,
    error_type: str = "about:blank",
    error_id: Optional[str] = None,
    instance: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    return {
        "type": error_type,
        "title": "error",
        "status": status_code,
        "detail": detail,
        "instance": instance or "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error_id": error_id or str(uuid.uuid4()),
        **extra,
    }


def error_response_factory(
    status_code: int,
    title: str = "error",
):
    def factory(detail: str, instance: Optional[str] = None) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content=format_error_response(
                status_code=status_code,
                detail=detail,
                error_type=f"https://api.finance-platform.com/errors/{title.lower().replace(' ', '-')}",
                instance=instance,
            ),
        )
    return factory


class ErrorHandler:
    def __init__(self, registry: Optional[ErrorRegistry] = None) -> None:
        self._registry = registry or ErrorRegistry()

    async def handle_finance_platform_error(
        self, request: Request, exc: FinancePlatformError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_validation_error(
        self, request: Request, exc: ValidationError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_not_found(
        self, request: Request, exc: NotFoundError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_auth_error(
        self, request: Request, exc: AuthError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_authorization_error(
        self, request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_business_rule_error(
        self, request: Request, exc: BusinessRuleError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_database_error(
        self, request: Request, exc: DatabaseError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_configuration_error(
        self, request: Request, exc: ConfigurationError
    ) -> JSONResponse:
        content = exc.to_dict()
        content["instance"] = str(request.url)
        return JSONResponse(status_code=exc.http_status, content=content)

    async def handle_generic_exception(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        error_id = str(uuid.uuid4())
        content = {
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": str(request.url),
            "error_id": error_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return JSONResponse(status_code=500, content=content)

    def register_handlers(self, app: FastAPI) -> None:
        app.add_exception_handler(FinancePlatformError, self.handle_finance_platform_error)
        app.add_exception_handler(ValidationError, self.handle_validation_error)
        app.add_exception_handler(NotFoundError, self.handle_not_found)
        app.add_exception_handler(AuthError, self.handle_auth_error)
        app.add_exception_handler(AuthorizationError, self.handle_authorization_error)
        app.add_exception_handler(BusinessRuleError, self.handle_business_rule_error)
        app.add_exception_handler(DatabaseError, self.handle_database_error)
        app.add_exception_handler(ConfigurationError, self.handle_configuration_error)
        app.add_exception_handler(Exception, self.handle_generic_exception)


_error_handler: Optional[ErrorHandler] = None


def error_handler() -> ErrorHandler:
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def register_error_handlers(app: FastAPI) -> None:
    handler = error_handler()
    handler.register_handlers(app)
