from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Optional, TypeVar

from finance_platform.logging.logger import AuditLogger, get_logger

F = TypeVar("F", bound=Callable[..., Any])


def log_call(logger_name: Optional[str] = None) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        log = get_logger(logger_name or func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()
            log.debug("call_start", function=func.__qualname__, args=_summarize_args(args), kwargs=_summarize_kwargs(kwargs))
            try:
                result = await func(*args, **kwargs)
                elapsed = time.monotonic() - start
                log.debug("call_end", function=func.__qualname__, elapsed_ms=round(elapsed * 1000, 2))
                return result
            except Exception as exc:
                elapsed = time.monotonic() - start
                log.error("call_failed", function=func.__qualname__, elapsed_ms=round(elapsed * 1000, 2), error=str(exc), error_type=type(exc).__name__)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()
            log.debug("call_start", function=func.__qualname__)
            try:
                result = func(*args, **kwargs)
                elapsed = time.monotonic() - start
                log.debug("call_end", function=func.__qualname__, elapsed_ms=round(elapsed * 1000, 2))
                return result
            except Exception as exc:
                elapsed = time.monotonic() - start
                log.error("call_failed", function=func.__qualname__, elapsed_ms=round(elapsed * 1000, 2), error=str(exc), error_type=type(exc).__name__)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_duration(logger_name: Optional[str] = None, threshold_ms: float = 0) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        log = get_logger(logger_name or func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.monotonic() - start
                elapsed_ms = round(elapsed * 1000, 2)
                if elapsed_ms >= threshold_ms:
                    log.info("duration", function=func.__qualname__, elapsed_ms=elapsed_ms)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.monotonic()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.monotonic() - start
                elapsed_ms = round(elapsed * 1000, 2)
                if elapsed_ms >= threshold_ms:
                    log.info("duration", function=func.__qualname__, elapsed_ms=elapsed_ms)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_audit(
    event_type: str,
    entity_type: Optional[str] = None,
    logger_name: str = "finance_platform.audit",
) -> Callable[[F], F]:
    audit_logger = AuditLogger(logger_name)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            _emit_audit(func, event_type, entity_type, kwargs, audit_logger, result)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            _emit_audit(func, event_type, entity_type, kwargs, audit_logger, result)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _emit_audit(func, event_type, entity_type, kwargs, audit_logger, result):
    entity_id = kwargs.get("entity_id") or kwargs.get("expense_id") or kwargs.get("debt_id") or kwargs.get("settlement_id") or ""
    company_id = kwargs.get("company_id") or ""
    actor_id = kwargs.get("actor_id") or kwargs.get("user_id") or ""
    audit_logger.log_event(
        event_type=event_type,
        entity_type=entity_type or func.__name__,
        entity_id=str(entity_id),
        actor_id=str(actor_id),
        company_id=str(company_id),
        details={"result": str(result)[:500] if result else None},
    )


def _summarize_args(args: tuple[Any, ...]) -> list[str]:
    return [type(a).__name__ for a in args[:5]]


def _summarize_kwargs(kwargs: dict[str, Any]) -> dict[str, str]:
    return {k: type(v).__name__ for k, v in kwargs.items()}
