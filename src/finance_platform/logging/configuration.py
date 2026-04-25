from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    UnicodeDecoder,
    format_exc_info,
)

from finance_platform.logging.correlation import CORRELATION_ID_KEY
from finance_platform.logging.filters import SensitiveDataFilter
from finance_platform.logging.handlers import JsonFileHandler, JsonStdoutHandler, RotatingJsonFileHandler
from finance_platform.logging.processors import (
    add_company_info,
    add_service_info,
    drop_empty_keys,
    format_exc_info_structured,
    inject_log_context,
    limit_string_length,
)

DEFAULT_SENSITIVE_FIELDS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "ssn",
    "bank_account",
    "routing_number",
    "cvv",
    "pin",
    "credit_card",
    "card_number",
    "access_key",
    "private_key",
    "session_id",
    "cookie",
    "refresh_token",
)


@dataclass
class LoggingConfiguration:
    log_level: str = "INFO"
    json_output: bool = True
    log_file: Optional[Path] = None
    log_file_max_bytes: int = 10485760
    log_file_backup_count: int = 5
    sensitive_fields: tuple[str, ...] = DEFAULT_SENSITIVE_FIELDS
    include_timestamps: bool = True
    include_caller_info: bool = True
    max_string_length: int = 2000
    correlation_id_key: str = CORRELATION_ID_KEY
    service_name: str = "finance_platform"
    environment: str = "production"
    enable_structlog: bool = True
    enable_stdlib_capture: bool = True
    stdlib_loggers: tuple[str, ...] = (
        "finance_platform",
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    )
    processors: list = field(default_factory=list)


def _build_structlog_processors(config: LoggingConfiguration) -> list:
    procs = []

    if config.include_timestamps:
        procs.append(TimeStamper(fmt="iso", utc=True))

    procs.extend(
        [
            add_service_info(service_name=config.service_name, environment=config.environment),
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            StackInfoRenderer(),
            format_exc_info_structured,
            SensitiveDataFilter(sensitive_fields=config.sensitive_fields),
            limit_string_length(max_length=config.max_string_length),
            inject_log_context,
            drop_empty_keys,
            UnicodeDecoder(),
        ]
    )

    if config.processors:
        procs.extend(config.processors)

    if config.json_output:
        procs.append(JSONRenderer())
    else:
        procs.append(ConsoleRenderer())

    return procs


def _setup_stdlib_logging(config: LoggingConfiguration) -> None:
    if not config.enable_stdlib_capture:
        return

    stdlib_level = getattr(logging, config.log_level.upper(), logging.INFO)

    structlog.stdlib.recreate_defaults(
        log_level=stdlib_level,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(stdlib_level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    if config.log_file:
        file_handler = RotatingJsonFileHandler(
            config.log_file,
            max_bytes=config.log_file_max_bytes,
            backup_count=config.log_file_backup_count,
        )
        file_handler.setLevel(stdlib_level)
        root_logger.addHandler(file_handler)

    stdout_handler = JsonStdoutHandler()
    stdout_handler.setLevel(stdlib_level)
    root_logger.addHandler(stdout_handler)


def configure_logging(config: Optional[LoggingConfiguration] = None) -> None:
    if config is None:
        config = LoggingConfiguration()

    if not config.enable_structlog:
        return

    structlog.configure(
        processors=_build_structlog_processors(config),
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _setup_stdlib_logging(config)
