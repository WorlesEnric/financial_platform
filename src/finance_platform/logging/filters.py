from __future__ import annotations

import logging
import re
from typing import Any

REDACTED = "***REDACTED***"

SENSITIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b\d{16}\b"),
    re.compile(r"\b\d{3,4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
]


class SensitiveDataFilter:
    def __init__(self, sensitive_fields: tuple[str, ...]) -> None:
        self._sensitive_fields = sensitive_fields

    def __call__(self, logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
        return self._redact(event_dict)

    def _redact(self, data: Any, depth: int = 0) -> Any:
        if depth > 10:
            return data
        if isinstance(data, dict):
            return {
                k: (REDACTED if self._is_sensitive(k) else self._redact(v, depth + 1))
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._redact(item, depth + 1) for item in data]
        if isinstance(data, tuple):
            return tuple(self._redact(item, depth + 1) for item in data)
        if isinstance(data, str):
            return self._redact_string(data)
        return data

    def _redact_string(self, value: str) -> str:
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(value):
                return REDACTED
        return value

    def _is_sensitive(self, key: str) -> bool:
        key_lower = key.lower()
        for field in self._sensitive_fields:
            if field in key_lower:
                return True
        return False


class CompanyIdFilter(logging.Filter):
    def __init__(self, param: str = "company_id") -> None:
        super().__init__()
        self.param = param

    def filter(self, record: logging.LogRecord) -> bool:
        return True


import logging
