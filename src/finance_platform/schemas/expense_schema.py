from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel


class ExpenseCreate(BaseModel):
    company_id: str
    description: str = Field(..., max_length=1024)
    amount_minor: int = Field(..., ge=0)
    currency: str = "USD"
    category: str = "other"
    incurred_date: str
    notes: Optional[str] = Field(None, max_length=2048)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=1024)
    amount_minor: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2048)
    metadata: Optional[Dict[str, Any]] = None


class ExpenseResponse(BaseModel):
    id: str
    company_id: str
    user_id: str
    description: str
    amount_minor: int
    amount: str
    currency: str
    category: str
    status: str
    incurred_date: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExpenseTimelineResponse(BaseModel):
    expense_id: str
    events: List[Dict[str, Any]] = Field(default_factory=list)


class ExpenseListResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
