from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel, TimestampMixin


class CarryForwardState(str, Enum):
    DRAFT = "draft"
    PENDING_AMORTIZATION = "pending_amortization"
    AMORTIZING = "amortizing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CarryForwardRecord(TimestampMixin):
    company_id: str
    from_period: str
    to_period: str
    debtor_company_id: str
    creditor_company_id: str
    net_amount_minor: int = Field(..., ge=0)
    currency: str = "USD"
    priority_level: str = "HIGH"
    state: CarryForwardState = CarryForwardState.PENDING_AMORTIZATION
    source_snapshot_file_url: Optional[str] = None
    source_snapshot_file_sha256: Optional[str] = None
    voucher_generated: bool = False
    voucher_url: Optional[str] = None
    voucher_sha256: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=2048)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def net_amount(self) -> Decimal:
        return Decimal(self.net_amount_minor) / 100


class CarryForwardBucket(BaseModel):
    company_id: str
    period: str
    total_carry_forward_minor: int = Field(default=0, ge=0)
    currency: str = "USD"
    record_count: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def total_carry_forward(self) -> Decimal:
        return Decimal(self.total_carry_forward_minor) / 100


class CarryForwardEntry(BaseModel):
    record_id: str
    from_company_id: str
    to_company_id: str
    amount_minor: int = Field(..., ge=0)
    currency: str = "USD"
    period: str
    is_settled: bool = False
    settled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def amount(self) -> Decimal:
        return Decimal(self.amount_minor) / 100
