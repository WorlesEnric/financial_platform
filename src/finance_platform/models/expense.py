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
    ExpenseCategory,
    CurrencyCode,
    ApprovalState,
    ReimbursementStatus,
)


class ExpenseLineItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=1024)
    quantity: float = Field(default=1.0, gt=0)
    unit_price: float = Field(..., ge=0)
    tax_rate: float = Field(default=0.0, ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    currency: CurrencyCode = CurrencyCode.USD
    cost_center: Optional[str] = None
    project_code: Optional[str] = None
    reference_number: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price

    @property
    def total(self) -> float:
        return self.subtotal + self.tax_amount - self.discount_amount


class ExpenseAttachment(BaseModel):
    filename: str = Field(..., max_length=512)
    content_type: str = Field(..., max_length=128)
    size_bytes: int = Field(..., ge=0)
    storage_key: str
    is_ocr_processed: bool = False
    ocr_text: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.now)


class Expense(TimestampMixin, SoftDeleteMixin, VersionMixin):
    user_id: str
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=4096)
    category: ExpenseCategory
    currency: CurrencyCode = CurrencyCode.USD
    amount: float = Field(..., ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    total_amount: float = Field(..., ge=0)
    expense_date: date
    submitted_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    status: ReimbursementStatus = ReimbursementStatus.DRAFT
    approval_state: ApprovalState = ApprovalState.PENDING
    line_items: List[ExpenseLineItem] = Field(default_factory=list)
    attachments: List[ExpenseAttachment] = Field(default_factory=list)
    vendor_name: Optional[str] = Field(None, max_length=256)
    vendor_tax_id: Optional[str] = None
    invoice_number: Optional[str] = None
    receipt_required: bool = True
    receipt_received: bool = False
    billable: bool = False
    billable_client_id: Optional[str] = None
    reimbursable: bool = True
    budget_code: Optional[str] = None
    project_id: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = Field(None, max_length=1024)
    notes: Optional[str] = Field(None, max_length=2048)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("total_amount")
    @classmethod
    def validate_total(cls, v: float, info: Any) -> float:
        amount = info.data.get("amount", 0)
        tax = info.data.get("tax_amount", 0)
        if v < amount + tax:
            raise ValueError("total_amount must be >= amount + tax_amount")
        return v

    @property
    def is_approved(self) -> bool:
        return self.approval_state == ApprovalState.APPROVED

    @property
    def is_paid(self) -> bool:
        return self.status in (ReimbursementStatus.PAID, ReimbursementStatus.PARTIALLY_PAID)

    @property
    def line_items_total(self) -> float:
        return sum(li.total for li in self.line_items)

    @property
    def days_outstanding(self) -> Optional[int]:
        if self.submitted_at is None:
            return None
        delta = datetime.now() - self.submitted_at
        return delta.days
