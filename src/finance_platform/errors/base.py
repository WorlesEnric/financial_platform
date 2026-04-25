from __future__ import annotations

import enum
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


class ErrorSeverity(enum.IntEnum):
    DEBUG = 0
    INFO = 10
    WARNING = 20
    ERROR = 30
    CRITICAL = 40
    FATAL = 50


class FinancePlatformError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "UNKNOWN",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        http_status: int = 500,
        cause: Optional[BaseException] = None,
        context: Optional[dict[str, Any]] = None,
        error_id: Optional[str] = None,
        user_message: Optional[str] = None,
        module: Optional[str] = None,
        recoverable: bool = False,
    ) -> None:
        self.message = message
        self.code = code
        self.severity = severity
        self.http_status = http_status
        self.cause = cause
        self.context = context or {}
        self.error_id = error_id or str(uuid.uuid4())
        self.user_message = user_message or message
        self.module = module or self.__class__.__module__
        self.recoverable = recoverable
        self.timestamp = datetime.now(timezone.utc)
        self.stack = traceback.format_exc() if cause else None
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "error_id": self.error_id,
            "code": self.code,
            "message": self.message,
            "user_message": self.user_message,
            "severity": self.severity.name,
            "http_status": self.http_status,
            "module": self.module,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.context:
            d["context"] = {k: str(v) for k, v in self.context.items()}
        if self.stack:
            d["stack"] = self.stack
        return d

    def with_context(self, **kwargs: Any) -> FinancePlatformError:
        self.context.update(kwargs)
        return self

    def with_user_message(self, msg: str) -> FinancePlatformError:
        self.user_message = msg
        return self

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"error_id={self.error_id!r}, "
            f"code={self.code!r}, "
            f"message={self.message!r}, "
            f"severity={self.severity.name}, "
            f"http_status={self.http_status})"
        )
