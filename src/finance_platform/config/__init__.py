from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DATABASE_URL: str = "sqlite+aiosqlite:///./finance_platform.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OBJECT_STORE_URL: str = "file://./storage"
    FX_SOURCE: str = "corporate-table"
    JWT_SECRET: str = "change-me-in-production"
    TIMEZONE: str = "UTC"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "*"
    API_PREFIX: str = "/api/v1"
    MAX_UPLOAD_SIZE_MB: int = 50
    RATE_LIMIT_PER_MINUTE: int = 100


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    global _settings
    _settings = Settings()
    return _settings


__all__ = [
    "Settings",
    "get_settings",
    "reload_settings",
]
