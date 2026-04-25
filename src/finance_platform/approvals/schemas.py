from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from finance_platform.approvals.models import ApprovalStatus, ApprovalType, StepStatus


class ApprovalStepCreate(BaseModel):
    step_order: int
    approver_id: str
    role_required: str = ""
    escalation_minutes: int = 4320


class ApprovalCreate(BaseModel):
    approval_type: ApprovalType = ApprovalType.EXPENSE_REPORT
    reference_id: str
    reference_type: str
    requester_id: str
    amount: Decimal = Field(default=Decimal("0.00"), max_digits=18, decimal_places=2)
    currency: str = "USD"
    policy_id: Optional[str] = None
    reason: str = ""
    steps: list[ApprovalStepCreate] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None


class ApprovalStepResponse(BaseModel):
    id: str
    approval_id: str
    step_order: int
    approver_id: str
    role_required: str
    status: StepStatus
    comments: str
    decided_at: Optional[datetime]
    escalation_minutes: int
    delegated_from: Optional[str]
    notification_sent: bool

    class Config:
        from_attributes = True


class ApprovalResponse(BaseModel):
    id: str
    approval_type: ApprovalType
    reference_id: str
    reference_type: str
    requester_id: str
    amount: Decimal
    currency: str
    status: ApprovalStatus
    steps: list[ApprovalStepResponse]
    current_step_index: int
    policy_id: Optional[str]
    reason: str
    metadata: dict[str, str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

    @property
    def current_step(self) -> Optional[ApprovalStepResponse]:
        if not self.steps or self.current_step_index >= len(self.steps):
            return None
        return self.steps[self.current_step_index]


class ApprovalDecision(BaseModel):
    step_id: str
    approve: bool
    comments: str = ""
    delegated_to: Optional[str] = None


class ApprovalListParams(BaseModel):
    status: Optional[ApprovalStatus] = None
    approval_type: Optional[ApprovalType] = None
    requester_id: Optional[str] = None
    approver_id: Optional[str] = None
    reference_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ApprovalListResponse(BaseModel):
    items: list[ApprovalResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PolicyRuleCreate(BaseModel):
    name: str
    description: str = ""
    min_approvers: int = 1
    required_roles: list[str] = Field(default_factory=list)
    max_amount: Optional[Decimal] = None
    min_amount: Optional[Decimal] = None
    requires_chain_of_approval: bool = False
    escalation_enabled: bool = True
    auto_approve_threshold: Optional[Decimal] = None


class PolicyRuleResponse(BaseModel):
    id: str
    name: str
    description: str
    min_approvers: int
    required_roles: list[str]
    max_amount: Optional[Decimal]
    min_amount: Optional[Decimal]
    requires_chain_of_approval: bool
    escalation_enabled: bool
    auto_approve_threshold: Optional[Decimal]

    class Config:
        from_attributes = True


class ApprovalPolicyCreate(BaseModel):
    name: str
    approval_type: ApprovalType = ApprovalType.EXPENSE_REPORT
    rules: list[PolicyRuleCreate] = Field(default_factory=list)


class ApprovalPolicyResponse(BaseModel):
    id: str
    name: str
    approval_type: ApprovalType
    rules: list[PolicyRuleResponse]
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DelegationCreate(BaseModel):
    delegator_id: str
    delegate_id: str
    role: str
    start_date: datetime
    end_date: Optional[datetime] = None
    reason: str = ""


class DelegationResponse(BaseModel):
    id: str
    delegator_id: str
    delegate_id: str
    role: str
    active: bool
    start_date: datetime
    end_date: Optional[datetime]
    reason: str
    created_at: datetime

    class Config:
        from_attributes = True


class EscalationRequest(BaseModel):
    approval_id: str
    reason: str = ""


class BulkDecisionRequest(BaseModel):
    decisions: list[ApprovalDecision]


class ApprovalStats(BaseModel):
    total_pending: int
    total_approved: int
    total_rejected: int
    total_escalated: int
    total_expired: int
    average_approval_time_hours: float = 0.0
    pending_approvals_by_type: dict[str, int] = Field(default_factory=dict)
