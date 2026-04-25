from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from finance_platform.settlements.models import (
    EntityType,
    PaymentMethod,
    SettlementPriority,
    SettlementBatchStatus,
    PaymentStatus,
)


class SettlementPriorityItem(BaseModel):
    entity_type: EntityType
    entity_id: str
    amount: float = Field(..., gt=0)
    priority: SettlementPriority = SettlementPriority.NORMAL
    reason: Optional[str] = None


class SettlementCreateRequest(BaseModel):
    entity_type: EntityType
    entity_id: str
    total_amount: float = Field(..., gt=0)
    currency: str = "USD"
    priority: SettlementPriority = SettlementPriority.NORMAL
    description: Optional[str] = Field(None, max_length=1024)
    department: Optional[str] = None
    cost_center: Optional[str] = None
    due_date: Optional[date] = None
    reference_number: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("total_amount")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 2)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        allowed = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "MXN",
                   "BRL", "SEK", "NOK", "DKK", "NZD", "KRW", "SGD", "HKD", "TRY", "ZAR"}
        if v.upper() not in allowed:
            raise ValueError(f"Unsupported currency: {v}")
        return v.upper()


class SettlementUpdateRequest(BaseModel):
    total_amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    priority: Optional[SettlementPriority] = None
    description: Optional[str] = Field(None, max_length=1024)
    department: Optional[str] = None
    cost_center: Optional[str] = None
    due_date: Optional[date] = None
    reference_number: Optional[str] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=2048)


class SettlementAllocationRequest(BaseModel):
    settlement_id: str
    entity_type: EntityType
    entity_id: str
    allocated_amount: float = Field(..., gt=0)
    currency: str = "USD"
    fx_rate: Optional[float] = None
    fx_from_currency: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1024)


class SettlementRunCreateRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=1024)
    currency: str = "USD"
    is_automatic: bool = False
    settlement_ids: list[str] = Field(default_factory=list)
    scheduled_date: Optional[date] = None


class SettlementRunResponse(BaseModel):
    id: str
    run_date: date
    description: Optional[str] = None
    total_settled: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    triggered_by: Optional[str] = None
    is_automatic: bool = False
    settlement_count: int = 0
    batch_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SettlementResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    total_amount: float
    settled_amount: float = 0.0
    remaining_amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    priority: SettlementPriority = SettlementPriority.NORMAL
    settlement_run_id: Optional[str] = None
    settlement_date: Optional[date] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_fully_settled(self) -> bool:
        return abs(self.remaining_amount) < 0.001

    @property
    def settlement_progress_pct(self) -> float:
        if self.total_amount == 0:
            return 100.0
        return round((self.settled_amount / self.total_amount) * 100, 2)


class SettlementListResponse(BaseModel):
    items: list[SettlementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SettlementBatchRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    settlement_ids: list[str] = Field(..., min_length=1)
    currency: str = "USD"


class SettlementSummaryResponse(BaseModel):
    total_pending: int = 0
    total_processing: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_reversed: int = 0
    total_amount_pending: float = 0.0
    total_amount_settled: float = 0.0
    total_high_priority_pending: int = 0
    total_high_priority_amount: float = 0.0
    pending_by_entity_type: dict[str, int] = Field(default_factory=dict)
    amount_by_currency: dict[str, float] = Field(default_factory=dict)
    active_run_count: int = 0
    last_run_date: Optional[date] = None


class PaymentCreateRequest(BaseModel):
    settlement_id: str
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    bank_account_ref: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_account: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1024)


class PaymentResponse(BaseModel):
    id: str
    settlement_id: str
    run_id: Optional[str] = None
    amount: float
    currency: str = "USD"
    payment_method: str = "bank_transfer"
    payment_reference: str = ""
    status: PaymentStatus = PaymentStatus.PENDING
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    bank_account_ref: Optional[str] = None
    beneficiary_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class SettlementSearchParams(BaseModel):
    entity_type: Optional[EntityType] = None
    entity_id: Optional[str] = None
    status: Optional[str] = None
    run_id: Optional[str] = None
    priority: Optional[SettlementPriority] = None
    currency: Optional[str] = None
    department: Optional[str] = None
    cost_center: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    tags: list[str] = Field(default_factory=list)
    q: Optional[str] = Field(None, max_length=256)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = "desc"

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        allowed = {"created_at", "updated_at", "total_amount", "settled_amount", "priority", "status"}
        if v not in allowed:
            raise ValueError(f"Invalid sort_by: {v}. Allowed: {allowed}")
        return v

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        if v not in ("asc", "desc"):
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v
