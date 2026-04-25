from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Optional

from finance_platform.logging.correlation import (
    COMPANY_ID_KEY,
    CORRELATION_ID_KEY,
    USER_ID_KEY,
)


class LogContext:
    _instance: Optional[LogContext] = None

    def __init__(self) -> None:
        self._stack: list[dict[str, Any]] = [{}]

    @classmethod
    def get_instance(cls) -> LogContext:
        if cls._instance is None:
            cls._instance = LogContext()
        return cls._instance

    def current(self) -> dict[str, Any]:
        return self._stack[-1] if self._stack else {}

    def push(self, **kwargs: Any) -> None:
        merged = {**self.current(), **kwargs}
        self._stack.append(merged)

    def pop(self) -> None:
        if len(self._stack) > 1:
            self._stack.pop()

    @contextmanager
    def scope(self, **kwargs: Any) -> Generator[None, None, None]:
        self.push(**kwargs)
        try:
            yield
        finally:
            self.pop()

    @property
    def correlation_id(self) -> Optional[str]:
        return self.current().get(CORRELATION_ID_KEY)

    @property
    def company_id(self) -> Optional[str]:
        return self.current().get(COMPANY_ID_KEY)

    @property
    def user_id(self) -> Optional[str]:
        return self.current().get(USER_ID_KEY)


current_log_context = LogContext.get_instance()
