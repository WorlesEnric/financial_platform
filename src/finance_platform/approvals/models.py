from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal
from typing import Optional


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class StepStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    ESCALATED = "escalated"


class ApprovalType(str, Enum):
    EXPENSE_REPORT = "expense_report"
    REIMBURSEMENT = "reimbursement"
    AMORTIZATION_SCHEDULE = "amortization_schedule"
    SETTLEMENT = "settlement"
    DEBT_FORGIVENESS = "debt_forgiveness"
    POLICY_EXCEPTION = "policy_exception"
    MANUAL_REVIEW = "manual_review"


@dataclass
class ApprovalStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    approval_id: str = ""
    step_order: int = 0
    approver_id: str = ""
    role_required: str = ""
    status: StepStatus = StepStatus.PENDING
    comments: str = ""
    decided_at: Optional[datetime] = None
    escalation_minutes: int = 0
    delegated_from: Optional[str] = None
    notification_sent: bool = False

    def approve(self, comments: str = "") -> None:
        self.status = StepStatus.APPROVED
        self.comments = comments
        self.decided_at = datetime.now(timezone.utc)

    def reject(self, comments: str = "") -> None:
        self.status = StepStatus.REJECTED
        self.comments = comments
        self.decided_at = datetime.now(timezone.utc)

    def skip(self) -> None:
        self.status = StepStatus.SKIPPED
        self.decided_at = datetime.now(timezone.utc)

    def escalate(self) -> None:
        self.status = StepStatus.ESCALATED
        self.decided_at = datetime.now(timezone.utc)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            StepStatus.APPROVED,
            StepStatus.REJECTED,
            StepStatus.SKIPPED,
        )


@dataclass
class PolicyRule:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    min_approvers: int = 1
    required_roles: list[str] = field(default_factory=list)
    max_amount: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    requires_chain_of_approval: bool = False
    escalation_enabled: bool = True
    auto_approve_threshold: Optional[Decimal] = None

    def applies_to_amount(self, amount: Decimal) -> bool:
        if self.min_amount is not None and amount < self.min_amount:
            return False
        if self.max_amount is not None and amount > self.max_amount:
            return False
        return True

    def can_auto_approve(self, amount: Decimal) -> bool:
        if self.auto_approve_threshold is None:
            return False
        return amount <= self.auto_approve_threshold


@dataclass
class ApprovalPolicy:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    approval_type: ApprovalType = ApprovalType.EXPENSE_REPORT
    rules: list[PolicyRule] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def find_applicable_rule(self, amount: Decimal) -> Optional[PolicyRule]:
        for rule in self.rules:
            if rule.applies_to_amount(amount):
                return rule
        return None


@dataclass
class Approval:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    approval_type: ApprovalType = ApprovalType.EXPENSE_REPORT
    reference_id: str = ""
    reference_type: str = ""
    requester_id: str = ""
    amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    status: ApprovalStatus = ApprovalStatus.PENDING
    steps: list[ApprovalStep] = field(default_factory=list)
    current_step_index: int = 0
    policy_id: Optional[str] = None
    reason: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @property
    def current_step(self) -> Optional[ApprovalStep]:
        if not self.steps or self.current_step_index >= len(self.steps):
            return None
        return self.steps[self.current_step_index]

    @property
    def all_steps_terminal(self) -> bool:
        return all(s.is_terminal for s in self.steps) if self.steps else False

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == ApprovalStatus.REJECTED

    @property
    def is_pending(self) -> bool:
        return self.status in (ApprovalStatus.PENDING, ApprovalStatus.IN_PROGRESS)

    def advance_step(self) -> None:
        if self.current_step_index < len(self.steps) - 1:
            self.current_step_index += 1
            self.updated_at = datetime.now(timezone.utc)

    def complete(self, status: ApprovalStatus) -> None:
        self.status = status
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def cancel(self) -> None:
        self.status = ApprovalStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at

    def escalate(self) -> None:
        self.status = ApprovalStatus.ESCALATED
        self.updated_at = datetime.now(timezone.utc)

    def expire(self) -> None:
        self.status = ApprovalStatus.EXPIRED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at
