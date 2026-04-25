from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel


class CompanyCreate(BaseModel):
    name: str = Field(..., max_length=256)
    legal_name: Optional[str] = Field(None, max_length=512)
    tax_id: Optional[str] = Field(None, max_length=64)
    address: Optional[str] = Field(None, max_length=512)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=256)
    website: Optional[str] = Field(None, max_length=256)
    currency: str = "USD"
    timezone: str = "UTC"


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=256)
    legal_name: Optional[str] = Field(None, max_length=512)
    tax_id: Optional[str] = Field(None, max_length=64)
    address: Optional[str] = Field(None, max_length=512)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=256)
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    currency: str
    timezone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CompanyMemberResponse(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    joined_at: datetime


class CompanySwitchRequest(BaseModel):
    company_id: str


class CompanyLeaveCheckResponse(BaseModel):
    can_leave: bool
    blocking_reasons: List[str] = Field(default_factory=list)
    unsettled_debts: bool = False
    open_approvals: bool = False
    sole_leader: bool = False
