from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Generator, Optional

from finance_platform.logging.logger import get_logger


class MetricsLogger:
    def __init__(self, logger_name: str = "finance_platform.metrics") -> None:
        self._logger = get_logger(logger_name)
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def increment(self, metric: str, value: int = 1, tags: Optional[dict[str, str]] = None) -> None:
        self._counters[metric] += value
        self._logger.debug("metric_counter", metric=metric, value=self._counters[metric], tags=tags or {})

    def gauge(self, metric: str, value: float, tags: Optional[dict[str, str]] = None) -> None:
        self._gauges[metric] = value
        self._logger.debug("metric_gauge", metric=metric, value=value, tags=tags or {})

    def histogram(self, metric: str, value: float, tags: Optional[dict[str, str]] = None) -> None:
        self._histograms[metric].append(value)
        self._logger.debug("metric_histogram", metric=metric, value=value, tags=tags or {})

    def timing(self, metric: str, duration_ms: float, tags: Optional[dict[str, str]] = None) -> None:
        self.histogram(metric, duration_ms, tags)
        self._logger.info("metric_timing", metric=metric, duration_ms=round(duration_ms, 2), tags=tags or {})

    def record_api_call(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        self._logger.info(
            "api_call",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
        )

    def record_db_query(self, query_name: str, duration_ms: float, rows_affected: int = 0) -> None:
        self._logger.debug(
            "db_query",
            query=query_name,
            duration_ms=round(duration_ms, 2),
            rows=rows_affected,
        )

    def record_business_event(
        self,
        event: str,
        entity_type: str,
        company_id: str,
        duration_ms: Optional[float] = None,
        **extra: Any,
    ) -> None:
        self._logger.info(
            "business_event",
            event=event,
            entity_type=entity_type,
            company_id=company_id,
            duration_ms=round(duration_ms, 2) if duration_ms is not None else None,
            **extra,
        )

    def get_counters(self) -> dict[str, int]:
        return dict(self._counters)

    def get_gauges(self) -> dict[str, float]:
        return dict(self._gauges)

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()

    @contextmanager
    def measure(self, metric: str, tags: Optional[dict[str, str]] = None) -> Generator[None, None, None]:
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed = time.monotonic() - start
            self.timing(metric, elapsed * 1000, tags)

    @contextmanager
    def measure_db_query(self, query_name: str) -> Generator[None, None, None]:
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed = time.monotonic() - start
            self.record_db_query(query_name, elapsed * 1000)


_global_metrics = MetricsLogger()


def get_metrics_logger() -> MetricsLogger:
    return _global_metrics
