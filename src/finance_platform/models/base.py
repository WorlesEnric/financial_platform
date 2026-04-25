from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict


T = TypeVar("T", bound="BaseModel")


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RECALLED = "recalled"
    ESCALATED = "escalated"
    DEFERRED = "deferred"


class ReimbursementStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class AmortizationMethod(str, Enum):
    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS_DIGITS = "sum_of_years_digits"
    MANUAL = "manual"
    CUSTOM = "custom"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    INR = "INR"
    MXN = "MXN"
    BRL = "BRL"
    SEK = "SEK"
    NOK = "NOK"
    DKK = "DKK"
    NZD = "NZD"
    KRW = "KRW"
    SGD = "SGD"
    HKD = "HKD"
    TRY = "TRY"
    ZAR = "ZAR"


class ExpenseCategory(str, Enum):
    TRAVEL = "travel"
    MEALS = "meals"
    ENTERTAINMENT = "entertainment"
    OFFICE_SUPPLIES = "office_supplies"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    PROFESSIONAL_SERVICES = "professional_services"
    TRAINING = "training"
    TRANSPORTATION = "transportation"
    ACCOMMODATION = "accommodation"
    UTILITIES = "utilities"
    RENT = "rent"
    INSURANCE = "insurance"
    TAXES = "taxes"
    OTHER = "other"


class DebtStatus(str, Enum):
    ACTIVE = "active"
    REPAID = "repaid"
    FORGIVEN = "forgiven"
    WRITTEN_OFF = "written_off"
    CANCELLED = "cancelled"


class SettlementStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class NotificationType(str, Enum):
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    PAYMENT_SENT = "payment_sent"
    PAYMENT_RECEIVED = "payment_received"
    REIMBURSEMENT_APPROVED = "reimbursement_approved"
    REIMBURSEMENT_PAID = "reimbursement_paid"
    EXPENSE_DUE = "expense_due"
    AMORTIZATION_COMPLETED = "amortization_completed"
    DEBT_REMINDER = "debt_reminder"
    SETTLEMENT_COMPLETED = "settlement_completed"
    AUDIT_ALERT = "audit_alert"
    SYSTEM = "system"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"
    PAY = "pay"
    VOID = "void"
    EXPORT = "export"
    IMPORT = "import"
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_default=True,
        extra="ignore",
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def model_dump_safe(self) -> Dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)

    def update_from_dict(self: T, data: Dict[str, Any], strict: bool = False) -> T:
        allowed = set(self.model_fields.keys())
        filtered = {k: v for k, v in data.items() if k in allowed} if strict else data
        for key, value in filtered.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseModel):
            return NotImplemented
        return self.id == other.id


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


class SoftDeleteMixin(BaseModel):
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None


class VersionMixin(BaseModel):
    version: int = Field(default=1, ge=1)
    previous_version_id: Optional[str] = None

    def bump_version(self, previous_id: Optional[str] = None) -> None:
        self.version += 1
        if previous_id is not None:
            self.previous_version_id = previous_id
