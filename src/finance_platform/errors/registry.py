from __future__ import annotations

from typing import Any, Dict, List, Optional

from finance_platform.errors.base import FinancePlatformError


class ErrorRegistry:
    def __init__(self) -> None:
        self._error_map: Dict[str, type[FinancePlatformError]] = {}
        self._http_status_map: Dict[int, List[str]] = {}

    def register(self, error_class: type[FinancePlatformError]) -> None:
        name = error_class.__name__
        self._error_map[name] = error_class
        try:
            instance = error_class("test")
            status = instance.http_status
            if status not in self._http_status_map:
                self._http_status_map[status] = []
            self._http_status_map[status].append(name)
        except Exception:
            pass

    def get_error_class(self, name: str) -> Optional[type[FinancePlatformError]]:
        return self._error_map.get(name)

    def get_errors_by_status(self, status: int) -> List[str]:
        return self._http_status_map.get(status, [])

    def list_registered(self) -> List[str]:
        return list(self._error_map.keys())

    def count(self) -> int:
        return len(self._error_map)
