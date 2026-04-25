from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    VersionMixin,
    ApprovalState,
    ReimbursementStatus,
    CurrencyCode,
)


class ReimbursementItem(BaseModel):
    expense_id: str
    amount: float = Field(..., ge=0)
    allocated_amount: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class Reimbursement(TimestampMixin, SoftDeleteMixin, VersionMixin):
    user_id: str
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=4096)
    currency: CurrencyCode = CurrencyCode.USD
    total_amount: float = Field(..., ge=0)
    status: ReimbursementStatus = ReimbursementStatus.DRAFT
    approval_state: ApprovalState = ApprovalState.PENDING
    items: List[ReimbursementItem] = Field(default_factory=list)
    submitted_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    paid_by: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_method: Optional[str] = None
    rejection_reason: Optional[str] = Field(None, max_length=1024)
    approval_chain_id: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    budget_period: Optional[str] = None
    fiscal_year: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_submittable(self) -> bool:
        return self.status == ReimbursementStatus.DRAFT and len(self.items) > 0

    @property
    def total_items_amount(self) -> float:
        return sum(item.amount for item in self.items)

    @property
    def item_count(self) -> int:
        return len(self.items)
