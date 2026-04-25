from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    VersionMixin,
    AmortizationMethod,
    CurrencyCode,
)


class AmortizationRule(BaseModel):
    method: AmortizationMethod = AmortizationMethod.STRAIGHT_LINE
    total_periods: int = Field(..., ge=1)
    period_unit: str = "month"  # month, quarter, year
    start_date: date
    end_date: Optional[date] = None
    residual_value: float = Field(default=0.0, ge=0)
    acceleration_factor: Optional[float] = None
    custom_schedule: Optional[Dict[int, float]] = None
    deferral_days: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info: Any) -> Optional[date]:
        start = info.data.get("start_date")
        if v is not None and start is not None and v <= start:
            raise ValueError("end_date must be after start_date")
        return v


class AmortizationEntry(BaseModel):
    period_number: int = Field(..., ge=1)
    period_start: date
    period_end: date
    scheduled_amount: float = Field(..., ge=0)
    actual_amount: Optional[float] = None
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def remaining(self) -> float:
        if self.actual_amount is not None:
            return self.scheduled_amount - self.actual_amount
        return self.scheduled_amount

    @property
    def is_overdue(self) -> bool:
        if self.is_paid:
            return False
        return self.period_end < date.today()


class AmortizationSchedule(TimestampMixin, SoftDeleteMixin, VersionMixin):
    entity_type: str  # expense, asset, prepaid
    entity_id: str
    total_amount: float = Field(..., ge=0)
    amortized_amount: float = Field(default=0.0, ge=0)
    remaining_amount: float = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    rule: AmortizationRule
    entries: List[AmortizationEntry] = Field(default_factory=list)
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=1024)
    cost_center: Optional[str] = None
    department: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def progress_pct(self) -> float:
        if self.total_amount == 0:
            return 100.0
        return round((self.amortized_amount / self.total_amount) * 100, 2)

    @property
    def paid_entries(self) -> List[AmortizationEntry]:
        return [e for e in self.entries if e.is_paid]

    @property
    def upcoming_entries(self) -> List[AmortizationEntry]:
        return [e for e in self.entries if not e.is_paid and e.period_start >= date.today()]

    @property
    def overdue_entries(self) -> List[AmortizationEntry]:
        return [e for e in self.entries if e.is_overdue]
