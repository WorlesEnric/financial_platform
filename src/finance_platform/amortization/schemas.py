from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from finance_platform.amortization.models import (
    AmortizationFrequency,
    AmortizationMethod,
    AmortizationStatus,
    AmortizationEntryStatus,
)
from finance_platform.models.base import BaseModel, CurrencyCode


class AmortizationRuleSchema(BaseModel):
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


class AmortizationRecordCreate(BaseModel):
    company_id: str
    entity_type: str
    entity_id: str
    description: str = Field(..., max_length=1024)
    total_amount_minor: int = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    method: AmortizationMethod
    frequency: AmortizationFrequency = AmortizationFrequency.MONTHLY
    total_periods: int = Field(..., ge=1)
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
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info: Any) -> Optional[date]:
        start = info.data.get("start_date")
        if v is not None and start is not None and v <= start:
            raise ValueError("end_date must be after start_date")
        return v

    @field_validator("total_periods")
    @classmethod
    def validate_total_periods(cls, v: int, info: Any) -> int:
        method = info.data.get("method")
        if method == AmortizationMethod.STRAIGHT_LINE and v < 1:
            raise ValueError("total_periods must be >= 1 for straight line")
        return v


class AmortizationRecordUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=1024)
    total_amount_minor: Optional[int] = Field(None, ge=0)
    residual_amount_minor: Optional[int] = Field(None, ge=0)
    acceleration_factor: Optional[float] = None
    interest_rate: Optional[float] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_code: Optional[str] = None
    budget_code: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class AmortizationEntryResponse(BaseModel):
    id: str
    record_id: str
    period_number: int
    period_start: date
    period_end: date
    scheduled_amount_minor: int
    actual_amount_minor: Optional[int] = None
    scheduled_amount: str
    actual_amount: Optional[str] = None
    status: AmortizationEntryStatus
    is_paid: bool
    paid_at: Optional[datetime] = None
    paid_by: Optional[str] = None
    payment_reference: Optional[str] = None
    is_overdue: bool
    is_due: bool
    remaining: str
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AmortizationRecordResponse(BaseModel):
    id: str
    company_id: str
    entity_type: str
    entity_id: str
    description: str
    total_amount_minor: int
    amortized_amount_minor: int
    remaining_amount_minor: int
    total_amount: str
    amortized_amount: str
    remaining_amount: str
    currency: CurrencyCode
    status: AmortizationStatus
    method: AmortizationMethod
    frequency: AmortizationFrequency
    total_periods: int
    completed_periods: int
    start_date: date
    end_date: Optional[date] = None
    residual_amount_minor: int
    period_amount_minor: int
    period_amount: str
    progress_pct: float
    acceleration_factor: Optional[float] = None
    interest_rate: Optional[float] = None
    is_active: bool
    is_completed: bool
    deferral_days: int
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_code: Optional[str] = None
    budget_code: Optional[str] = None
    fiscal_year: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    expected_completion_date: Optional[date] = None
    entries: List[AmortizationEntryResponse] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AmortizationListResponse(BaseModel):
    items: List[AmortizationRecordResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AmortizationAdjustmentCreate(BaseModel):
    record_id: str
    new_amount_minor: int = Field(..., ge=0)
    reason: str = Field(..., max_length=2048)


class AmortizationForecastResponse(BaseModel):
    record_id: str
    forecast_date: date
    projected_end_date: date
    projected_total_amount_minor: int
    projected_remaining_amount_minor: int
    projected_periods_remaining: int
    projected_period_amount_minor: int
    projected_total_amount: str
    projected_remaining_amount: str
    projected_period_amount: str
    confidence_score: float
    assumptions: List[str] = Field(default_factory=list)
    scenarios: Dict[str, Any] = Field(default_factory=dict)


class AmortizationSummaryResponse(BaseModel):
    company_id: str
    fiscal_year: str
    total_active_records: int
    total_completed_records: int
    total_amount_minor: int
    total_amortized_minor: int
    total_remaining_minor: int
    total_amount: str
    total_amortized: str
    total_remaining: str
    total_overdue_entries: int
    total_overdue_amount_minor: int
    total_overdue_amount: str
    overall_progress_pct: float
    records_by_method: Dict[str, int]
    records_by_department: Dict[str, int]
    generated_at: datetime


class AmortizationBulkCreateRequest(BaseModel):
    company_id: str
    items: List[AmortizationRecordCreate]


class AmortizationBulkCreateResponse(BaseModel):
    created: List[AmortizationRecordResponse]
    failed: List[Dict[str, Any]]
    total_requested: int
    total_created: int
    total_failed: int


class AmortizationStatusUpdateRequest(BaseModel):
    status: AmortizationStatus
    reason: Optional[str] = Field(None, max_length=2048)


class AmortizationEntryPaymentRequest(BaseModel):
    entry_id: str
    actual_amount_minor: int = Field(..., ge=0)
    paid_by: str
    payment_reference: Optional[str] = None
    invoice_reference: Optional[str] = None
    notes: Optional[str] = None


class AmortizationEntryDeferRequest(BaseModel):
    entry_id: str
    deferral_date: date
    reason: str = Field(..., max_length=1024)


class AmortizationEntryWaiveRequest(BaseModel):
    entry_id: str
    reason: str = Field(..., max_length=1024)


class AmortizationFilterParams(BaseModel):
    company_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    status: Optional[AmortizationStatus] = None
    method: Optional[AmortizationMethod] = None
    frequency: Optional[AmortizationFrequency] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_code: Optional[str] = None
    fiscal_year: Optional[str] = None
    is_overdue: Optional[bool] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    end_date_from: Optional[date] = None
    end_date_to: Optional[date] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"
