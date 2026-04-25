from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, TextIO


class JsonFileHandler(logging.Handler):
    def __init__(self, filepath: Path, mode: str = "a") -> None:
        super().__init__()
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.filepath, mode)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = self._format_record(record)
            self._file.write(json.dumps(entry, default=str) + "\n")
            self._file.flush()
        except Exception:
            self.handleError(record)

    def _format_record(self, record: logging.LogRecord) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

    def close(self) -> None:
        self._file.close()
        super().close()


class JsonStdoutHandler(logging.Handler):
    def __init__(self, stream: Optional[TextIO] = None) -> None:
        super().__init__()
        self._stream = stream or sys.stdout

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = self._format_record(record)
            self._stream.write(json.dumps(entry, default=str) + "\n")
            self._stream.flush()
        except Exception:
            self.handleError(record)

    def _format_record(self, record: logging.LogRecord) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }


class RotatingJsonFileHandler(logging.Handler):
    def __init__(
        self,
        filepath: Path,
        max_bytes: int = 10485760,
        backup_count: int = 5,
    ) -> None:
        super().__init__()
        self.filepath = filepath
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._current_size = 0
        self._open_file()

    def _open_file(self) -> None:
        self._file = open(self.filepath, "a")
        self._current_size = self.filepath.stat().st_size

    def _rotate(self) -> None:
        self._file.close()
        for i in range(self.backup_count - 1, 0, -1):
            src = Path(f"{self.filepath}.{i}")
            dst = Path(f"{self.filepath}.{i + 1}")
            if src.exists():
                src.rename(dst)
        if self.filepath.exists():
            self.filepath.rename(Path(f"{self.filepath}.1"))
        self._open_file()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            entry = self._format_record(record)
            line = json.dumps(entry, default=str) + "\n"
            if self._current_size + len(line) > self.max_bytes:
                self._rotate()
            self._file.write(line)
            self._file.flush()
            self._current_size += len(line)
        except Exception:
            self.handleError(record)

    def _format_record(self, record: logging.LogRecord) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

    def close(self) -> None:
        self._file.close()
        super().close()
