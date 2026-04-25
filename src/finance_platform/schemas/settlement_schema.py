from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel


class SettlementCreate(BaseModel):
    company_id: str
    settlement_currency_code: str = "USD"
    settlement_amount_minor: int = Field(..., ge=0)
    settlement_functional_amount_minor: Optional[int] = Field(None, ge=0)
    settlement_fx_rate_to_functional: Optional[str] = None
    proof_file_url: Optional[str] = None
    proof_file_sha256: Optional[str] = None
    payment_method: str = "bank_transfer"
    external_ref_no: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2048)


class SettlementResponse(BaseModel):
    id: str
    company_id: str
    settlement_currency_code: str
    settlement_amount_minor: int
    settlement_amount: str
    settlement_functional_amount_minor: Optional[int] = None
    settlement_functional_amount: Optional[str] = None
    settlement_fx_rate_to_functional: Optional[str] = None
    proof_file_url: Optional[str] = None
    proof_file_sha256: Optional[str] = None
    payment_method: str
    external_ref_no: Optional[str] = None
    status: str
    created_at: datetime
    notes: Optional[str] = None


class SettlementAllocationResponse(BaseModel):
    id: str
    settlement_id: str
    debt_item_id: str
    allocated_amount_minor: int
    allocated_amount: str
    is_carry_forward: bool = False
    priority: str = "NORMAL"
    created_at: datetime


class SettlementPreviewResponse(BaseModel):
    settlement_id: str
    total_amount_minor: int
    total_amount: str
    allocations: List[SettlementAllocationResponse]
    remaining_amount_minor: int
    remaining_amount: str


class SettlementListResponse(BaseModel):
    items: List[SettlementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
