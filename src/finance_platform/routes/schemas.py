from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    type: str = "about:blank"
    title: str = "error"
    status: int = 400
    detail: str
    instance: str = ""
    error_id: str = ""
    timestamp: str = ""


class ValidationErrorItem(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    errors: List[ValidationErrorItem] = Field(default_factory=list)


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"


class IdResponse(BaseModel):
    id: str


class BulkOperationResponse(BaseModel):
    created: List[IdResponse] = Field(default_factory=list)
    failed: List[Dict[str, Any]] = Field(default_factory=list)
    total_requested: int = 0
    total_created: int = 0
    total_failed: int = 0


class DateRangeFilter(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SortParams(BaseModel):
    sort_by: str = "created_at"
    sort_order: str = "desc"


__all__ = [
    "ErrorResponse",
    "ValidationErrorItem",
    "ValidationErrorResponse",
    "SuccessResponse",
    "IdResponse",
    "BulkOperationResponse",
    "DateRangeFilter",
    "SortParams",
]
