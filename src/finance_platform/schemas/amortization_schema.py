from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel


class AmortizationGroupCreate(BaseModel):
    company_id: str
    name: str = Field(..., max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AmortizationGroupResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    status: str
    current_version_no: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AmortizationGroupVersionCreate(BaseModel):
    group_id: str
    effective_from: date
    ratio_percent: float = Field(..., ge=0, le=100)
    is_leader: bool = False
    notes: Optional[str] = Field(None, max_length=2048)


class AmortizationGroupVersionResponse(BaseModel):
    id: str
    group_id: str
    version_no: int
    effective_from: date
    effective_to: Optional[date] = None
    ratio_percent: float
    is_leader: bool
    status: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
