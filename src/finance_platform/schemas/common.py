from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import Field

from finance_platform.models.base import BaseModel

T = TypeVar("T")


class MoneyDecimal(BaseModel):
    amount_minor: int = Field(..., ge=0)
    currency: str = "USD"

    @property
    def amount(self) -> str:
        return str(Decimal(self.amount_minor) / 100)


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    type: str = "about:blank"
    title: str = "error"
    status: int
    detail: str
    instance: Optional[str] = None
    error_id: Optional[str] = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
