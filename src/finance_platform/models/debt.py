from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    VersionMixin,
    DebtStatus,
    CurrencyCode,
)


class DebtPayment(BaseModel):
    payment_date: date
    amount: float = Field(..., gt=0)
    currency: CurrencyCode = CurrencyCode.USD
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.now)


class DebtSettlement(BaseModel):
    settled_amount: float = Field(..., gt=0)
    settlement_date: date
    settlement_method: str  # cash, write_off, forgiveness, offset
    approved_by: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class Debt(TimestampMixin, SoftDeleteMixin, VersionMixin):
    creditor_id: str
    debtor_id: str
    original_amount: float = Field(..., gt=0)
    outstanding_amount: float = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    status: DebtStatus = DebtStatus.ACTIVE
    description: Optional[str] = Field(None, max_length=2048)
    incurred_date: date
    due_date: Optional[date] = None
    interest_rate: Optional[float] = Field(None, ge=0)
    interest_calculation_method: Optional[str] = None
    payments: List[DebtPayment] = Field(default_factory=list)
    settlements: List[DebtSettlement] = Field(default_factory=list)
    reference_number: Optional[str] = None
    category: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("outstanding_amount")
    @classmethod
    def validate_outstanding(cls, v: float, info: Any) -> float:
        original = info.data.get("original_amount", 0)
        if v > original:
            raise ValueError("outstanding_amount cannot exceed original_amount")
        return v

    @property
    def total_paid(self) -> float:
        return sum(p.amount for p in self.payments)

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        return self.due_date < date.today() and self.status == DebtStatus.ACTIVE

    @property
    def days_overdue(self) -> Optional[int]:
        if not self.is_overdue:
            return None
        return (date.today() - self.due_date).days

    @property
    def repayment_progress_pct(self) -> float:
        if self.original_amount == 0:
            return 100.0
        return round((self.total_paid / self.original_amount) * 100, 2)
