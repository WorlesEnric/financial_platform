from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional


class EntityType(str, Enum):
    EXPENSE = "expense"
    REIMBURSEMENT = "reimbursement"
    DEBT = "debt"
    CARRY_FORWARD = "carry_forward"
    AMORTIZATION = "amortization"


class SettlementPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class SettlementBatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class PaymentMethod(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    CHEQUE = "cheque"
    CASH = "cash"
    INTERNAL_OFFSET = "internal_offset"
    WIRE = "wire"
    ACH = "ach"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERSED = "reversed"


@dataclass
class SettlementOrder:
    entity_type: EntityType = EntityType.DEBT
    entity_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    priority: SettlementPriority = SettlementPriority.NORMAL
    description: str = ""
    reference_number: str = ""
    department: str = ""
    cost_center: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[date] = None

    @property
    def sort_key(self) -> tuple[int, datetime]:
        priority_order = {
            SettlementPriority.HIGH: 0,
            SettlementPriority.NORMAL: 1,
            SettlementPriority.LOW: 2,
        }
        return (priority_order.get(self.priority, 99), self.created_at)


@dataclass
class SettlementPayment:
    id: str = ""
    settlement_id: str = ""
    run_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    payment_reference: str = ""
    status: PaymentStatus = PaymentStatus.PENDING
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    bank_account_ref: str = ""
    beneficiary_name: str = ""
    beneficiary_account: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_confirmed(self) -> bool:
        return self.status == PaymentStatus.CONFIRMED

    @property
    def is_failed(self) -> bool:
        return self.status == PaymentStatus.FAILED


@dataclass
class SettlementBatch:
    id: str = ""
    run_id: str = ""
    name: str = ""
    status: SettlementBatchStatus = SettlementBatchStatus.PENDING
    total_amount: float = 0.0
    currency: str = "USD"
    item_count: int = 0
    settled_count: int = 0
    failed_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error_message: str = ""

    @property
    def progress_pct(self) -> float:
        if self.item_count == 0:
            return 100.0
        return round((self.settled_count / self.item_count) * 100, 2)

    @property
    def is_complete(self) -> bool:
        return self.status in (
            SettlementBatchStatus.COMPLETED,
            SettlementBatchStatus.FAILED,
        )


@dataclass
class SettlementFilter:
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
    tags: list[str] = field(default_factory=list)
    is_deleted: bool = False

    @property
    def has_filters(self) -> bool:
        return any(
            [
                self.entity_type,
                self.entity_id,
                self.status,
                self.run_id,
                self.priority,
                self.currency,
                self.department,
                self.cost_center,
                self.date_from,
                self.date_to,
                self.tags,
            ]
        )


@dataclass
class SettlementSummary:
    total_pending: int = 0
    total_processing: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_reversed: int = 0
    total_amount_pending: float = 0.0
    total_amount_settled: float = 0.0
    total_high_priority_pending: int = 0
    total_high_priority_amount: float = 0.0
    pending_by_entity_type: dict[str, int] = field(default_factory=dict)
    amount_by_currency: dict[str, float] = field(default_factory=dict)
    active_run_count: int = 0
    last_run_date: Optional[date] = None
