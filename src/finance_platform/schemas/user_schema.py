from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from finance_platform.models.base import BaseModel


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., max_length=256)
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., max_length=256)
    phone: Optional[str] = Field(None, max_length=32)


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=256)
    email: Optional[str] = Field(None, max_length=256)
    phone: Optional[str] = Field(None, max_length=32)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
