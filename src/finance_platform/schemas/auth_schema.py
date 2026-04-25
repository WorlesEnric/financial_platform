from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class TokenRefreshRequest(BaseModel):
    refresh_token: str
