from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    VersionMixin,
    SettlementStatus,
    CurrencyCode,
)


class SettlementAllocation(BaseModel):
    entity_type: str  # expense, reimbursement, debt
    entity_id: str
    allocated_amount: float = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    fx_rate_applied: Optional[float] = None
    fx_from_currency: Optional[CurrencyCode] = None
    notes: Optional[str] = None


class SettlementRun(TimestampMixin, SoftDeleteMixin, VersionMixin):
    run_date: date = Field(default_factory=date.today)
    description: Optional[str] = None
    total_settled: float = Field(default=0.0, ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    status: SettlementStatus = SettlementStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    triggered_by: Optional[str] = None
    is_automatic: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Settlement(TimestampMixin, SoftDeleteMixin, VersionMixin):
    settlement_run_id: Optional[str] = None
    entity_type: str  # expense, reimbursement, debt
    entity_id: str
    total_amount: float = Field(..., ge=0)
    settled_amount: float = Field(..., ge=0)
    remaining_amount: float = Field(default=0.0, ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    status: SettlementStatus = SettlementStatus.PENDING
    allocations: List[SettlementAllocation] = Field(default_factory=list)
    settlement_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    bank_account_ref: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2048)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("remaining_amount")
    @classmethod
    def validate_remaining(cls, v: float, info: Any) -> float:
        total = info.data.get("total_amount", 0)
        settled = info.data.get("settled_amount", 0)
        expected_remaining = round(total - settled, 4)
        if abs(v - expected_remaining) > 0.01:
            raise ValueError(f"remaining_amount should be ~{expected_remaining}, got {v}")
        return v

    @property
    def is_fully_settled(self) -> bool:
        return abs(self.remaining_amount) < 0.001

    @property
    def settlement_progress_pct(self) -> float:
        if self.total_amount == 0:
            return 100.0
        return round((self.settled_amount / self.total_amount) * 100, 2)
