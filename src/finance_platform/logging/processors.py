from __future__ import annotations

import sys
import traceback
from typing import Any

from structlog.processors import format_exc_info


def format_exc_info_structured(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        if isinstance(exc_info, BaseException):
            exc = exc_info
        elif isinstance(exc_info, tuple) and len(exc_info) == 3:
            exc = exc_info[1]
        else:
            return event_dict
        event_dict["exception"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        }
    return event_dict


def add_service_info(service_name: str = "finance_platform", environment: str = "production"):
    def processor(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        event_dict["service"] = service_name
        event_dict["environment"] = environment
        return event_dict
    return processor


def add_company_info(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    from finance_platform.logging.correlation import get_current_company_id
    company_id = get_current_company_id()
    if company_id:
        event_dict["company_id"] = company_id
    return event_dict


def inject_log_context(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    from finance_platform.logging.context import current_log_context
    ctx = current_log_context.get()
    if ctx:
        for key, value in ctx.items():
            if key not in event_dict:
                event_dict[key] = value
    return event_dict


def drop_empty_keys(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in event_dict.items() if v is not None and v != "" and v != {} and v != []}


def limit_string_length(max_length: int = 2000):
    def processor(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return _truncate_values(event_dict, max_length)
    return processor


def _truncate_values(data: Any, max_length: int, depth: int = 0) -> Any:
    if depth > 10:
        return data
    if isinstance(data, dict):
        return {k: _truncate_values(v, max_length, depth + 1) for k, v in data.items()}
    if isinstance(data, list):
        return [_truncate_values(item, max_length, depth + 1) for item in data]
    if isinstance(data, str) and len(data) > max_length:
        return data[:max_length] + "..."
    return data
