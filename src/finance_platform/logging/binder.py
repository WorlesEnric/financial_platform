from __future__ import annotations

from contextlib import contextmanager, asynccontextmanager
from typing import Any, AsyncGenerator, Generator, Optional

from structlog.contextvars import bind_contextvars, clear_contextvars, unbind_contextvars

from finance_platform.logging.correlation import (
    COMPANY_ID_KEY,
    SESSION_ID_KEY,
    TENANT_ID_KEY,
    USER_ID_KEY,
)
from finance_platform.logging.context import LogContext, current_log_context


class CompanyLogBinder:
    def __init__(self) -> None:
        self._bound: set[str] = set()

    def bind(self, **kwargs: Any) -> None:
        bind_contextvars(**kwargs)
        self._bound.update(kwargs.keys())

    def unbind(self, *keys: str) -> None:
        unbind_contextvars(*keys)
        for key in keys:
            self._bound.discard(key)

    def clear(self) -> None:
        if self._bound:
            unbind_contextvars(*self._bound)
        self._bound.clear()

    def is_bound(self, key: str) -> bool:
        return key in self._bound

    def get_bound_keys(self) -> frozenset:
        return frozenset(self._bound)

    @contextmanager
    def scope(self, **kwargs: Any) -> Generator[None, None, None]:
        previous = set(self._bound)
        self.bind(**kwargs)
        try:
            with current_log_context.push(**kwargs):
                yield
        finally:
            self.clear()
            if previous:
                for key in previous:
                    if key not in self._bound:
                        from structlog.contextvars import bind_contextvars

                        bind_contextvars(**{key: None})

    @asynccontextmanager
    async def async_scope(self, **kwargs: Any) -> AsyncGenerator[None, None]:
        previous = set(self._bound)
        self.bind(**kwargs)
        try:
            yield
        finally:
            self.clear()
            if previous:
                for key in previous:
                    if key not in self._bound:
                        from structlog.contextvars import bind_contextvars

                        bind_contextvars(**{key: None})

    @contextmanager
    def company_scope(self, company_id: str, **extra: Any) -> Generator[None, None, None]:
        ctx = {COMPANY_ID_KEY: company_id, **extra}
        with self.scope(**ctx):
            yield

    @contextmanager
    def user_scope(self, user_id: str, **extra: Any) -> Generator[None, None, None]:
        ctx = {USER_ID_KEY: user_id, **extra}
        with self.scope(**ctx):
            yield

    @contextmanager
    def tenant_scope(self, tenant_id: str, **extra: Any) -> Generator[None, None, None]:
        ctx = {TENANT_ID_KEY: tenant_id, **extra}
        with self.scope(**ctx):
            yield

    @contextmanager
    def request_scope(
        self,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **extra: Any,
    ) -> Generator[None, None, None]:
        ctx: dict[str, Any] = {}
        if company_id:
            ctx[COMPANY_ID_KEY] = company_id
        if user_id:
            ctx[USER_ID_KEY] = user_id
        if session_id:
            ctx[SESSION_ID_KEY] = session_id
        ctx.update(extra)
        with self.scope(**ctx):
            yield


_global_binder = CompanyLogBinder()


def get_company_binder() -> CompanyLogBinder:
    return _global_binder
