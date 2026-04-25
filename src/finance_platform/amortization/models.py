from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    VersionMixin,
    CurrencyCode,
)


class AmortizationStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class AmortizationMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS_DIGITS = "sum_of_years_digits"
    DOUBLE_DECLINING = "double_declining"
    ANNUITY = "annuity"
    BALLOON = "balloon"
    CUSTOM = "custom"
    MANUAL = "manual"


class AmortizationFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUALLY = "semi_annually"
    ANNUALLY = "annually"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    CUSTOM = "custom"


class AmortizationEntryStatus(str, Enum):
    SCHEDULED = "scheduled"
    DUE = "due"
    OVERDUE = "overdue"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    WAIVED = "waived"
    DEFERRED = "deferred"


class AmortizationRecord(TimestampMixin, SoftDeleteMixin, VersionMixin):
    company_id: str
    entity_type: str
    entity_id: str
    description: str = Field(..., max_length=1024)
    total_amount_minor: int = Field(..., ge=0)
    amortized_amount_minor: int = Field(default=0, ge=0)
    remaining_amount_minor: int = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    status: AmortizationStatus = AmortizationStatus.DRAFT
    method: AmortizationMethod
    frequency: AmortizationFrequency = AmortizationFrequency.MONTHLY
    total_periods: int = Field(..., ge=1)
    completed_periods: int = Field(default=0, ge=0)
    start_date: date
    end_date: Optional[date] = None
    residual_amount_minor: int = Field(default=0, ge=0)
    acceleration_factor: Optional[float] = None
    interest_rate: Optional[float] = None
    deferral_days: int = Field(default=0, ge=0)
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_code: Optional[str] = None
    budget_code: Optional[str] = None
    fiscal_year: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = Field(None, max_length=2048)
    completed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info: Any) -> Optional[date]:
        start = info.data.get("start_date")
        if v is not None and start is not None and v <= start:
            raise ValueError("end_date must be after start_date")
        return v

    @property
    def progress_pct(self) -> float:
        if self.total_amount_minor == 0:
            return 100.0
        return round((self.amortized_amount_minor / self.total_amount_minor) * 100, 2)

    @property
    def total_amount(self) -> Decimal:
        return Decimal(self.total_amount_minor) / 100

    @property
    def amortized_amount(self) -> Decimal:
        return Decimal(self.amortized_amount_minor) / 100

    @property
    def remaining_amount(self) -> Decimal:
        return Decimal(self.remaining_amount_minor) / 100

    @property
    def residual_amount(self) -> Decimal:
        return Decimal(self.residual_amount_minor) / 100

    @property
    def is_active(self) -> bool:
        return self.status == AmortizationStatus.ACTIVE

    @property
    def is_completed(self) -> bool:
        return self.status == AmortizationStatus.COMPLETED

    @property
    def period_amount_minor(self) -> int:
        if self.total_periods == 0:
            return 0
        effective = self.total_amount_minor - self.residual_amount_minor
        return effective // self.total_periods

    @property
    def period_amount(self) -> Decimal:
        return Decimal(self.period_amount_minor) / 100

    @property
    def expected_completion_date(self) -> Optional[date]:
        if not self.start_date or not self.total_periods:
            return None
        months = self.total_periods
        y = self.start_date.year + (self.start_date.month - 1 + months) // 12
        m = (self.start_date.month - 1 + months) % 12 + 1
        d = min(self.start_date.day, 28)
        return date(y, m, d)


class AmortizationEntry(BaseModel):
    record_id: str
    period_number: int = Field(..., ge=1)
    period_start: date
    period_end: date
    scheduled_amount_minor: int = Field(..., ge=0)
    actual_amount_minor: Optional[int] = None
    status: AmortizationEntryStatus = AmortizationEntryStatus.SCHEDULED
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    paid_by: Optional[str] = None
    payment_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    waiver_reason: Optional[str] = Field(None, max_length=1024)
    deferral_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=2048)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def scheduled_amount(self) -> Decimal:
        return Decimal(self.scheduled_amount_minor) / 100

    @property
    def actual_amount(self) -> Optional[Decimal]:
        if self.actual_amount_minor is not None:
            return Decimal(self.actual_amount_minor) / 100
        return None

    @property
    def remaining_minor(self) -> int:
        if self.actual_amount_minor is not None:
            return self.scheduled_amount_minor - self.actual_amount_minor
        return self.scheduled_amount_minor

    @property
    def remaining(self) -> Decimal:
        return Decimal(self.remaining_minor) / 100

    @property
    def is_overdue(self) -> bool:
        if self.is_paid or self.status in (AmortizationEntryStatus.WAIVED, AmortizationEntryStatus.DEFERRED):
            return False
        return self.period_end < date.today()

    @property
    def is_due(self) -> bool:
        if self.is_paid or self.status in (AmortizationEntryStatus.WAIVED, AmortizationEntryStatus.DEFERRED):
            return False
        today = date.today()
        return self.period_start <= today <= self.period_end


class AmortizationRule(BaseModel):
    company_id: str
    name: str = Field(..., max_length=256)
    description: Optional[str] = Field(None, max_length=1024)
    method: AmortizationMethod
    frequency: AmortizationFrequency = AmortizationFrequency.MONTHLY
    total_periods: int = Field(..., ge=1)
    acceleration_factor: Optional[float] = None
    interest_rate: Optional[float] = None
    residual_rate: float = Field(default=0.0, ge=0, le=1)
    deferral_days: int = Field(default=0, ge=0)
    is_active: bool = True
    applies_to_entity_types: List[str] = Field(default_factory=lambda: ["expense", "asset", "prepaid"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AmortizationAdjustment(BaseModel):
    record_id: str
    adjustment_number: int = Field(..., ge=1)
    adjustment_type: str
    previous_amount_minor: int = Field(..., ge=0)
    new_amount_minor: int = Field(..., ge=0)
    difference_minor: int
    reason: str = Field(..., max_length=2048)
    adjusted_by: str
    adjusted_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def previous_amount(self) -> Decimal:
        return Decimal(self.previous_amount_minor) / 100

    @property
    def new_amount(self) -> Decimal:
        return Decimal(self.new_amount_minor) / 100

    @property
    def difference(self) -> Decimal:
        return Decimal(self.difference_minor) / 100


class AmortizationForecast(BaseModel):
    record_id: str
    forecast_date: date
    projected_end_date: date
    projected_total_amount_minor: int = Field(..., ge=0)
    projected_remaining_amount_minor: int = Field(..., ge=0)
    projected_periods_remaining: int = Field(..., ge=0)
    projected_period_amount_minor: int = Field(..., ge=0)
    confidence_score: float = Field(default=1.0, ge=0, le=1)
    assumptions: List[str] = Field(default_factory=list)
    scenarios: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def projected_total_amount(self) -> Decimal:
        return Decimal(self.projected_total_amount_minor) / 100

    @property
    def projected_remaining_amount(self) -> Decimal:
        return Decimal(self.projected_remaining_amount_minor) / 100

    @property
    def projected_period_amount(self) -> Decimal:
        return Decimal(self.projected_period_amount_minor) / 100


class AmortizationSummary(BaseModel):
    company_id: str
    fiscal_year: str
    total_active_records: int = 0
    total_completed_records: int = 0
    total_amount_minor: int = 0
    total_amortized_minor: int = 0
    total_remaining_minor: int = 0
    total_overdue_entries: int = 0
    total_overdue_amount_minor: int = 0
    records_by_method: Dict[str, int] = Field(default_factory=dict)
    records_by_department: Dict[str, int] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_amount(self) -> Decimal:
        return Decimal(self.total_amount_minor) / 100

    @property
    def total_amortized(self) -> Decimal:
        return Decimal(self.total_amortized_minor) / 100

    @property
    def total_remaining(self) -> Decimal:
        return Decimal(self.total_remaining_minor) / 100

    @property
    def total_overdue_amount(self) -> Decimal:
        return Decimal(self.total_overdue_amount_minor) / 100

    @property
    def overall_progress_pct(self) -> float:
        if self.total_amount_minor == 0:
            return 100.0
        return round((self.total_amortized_minor / self.total_amount_minor) * 100, 2)
