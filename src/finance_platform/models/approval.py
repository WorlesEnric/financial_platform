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
)


class ApprovalDecision(BaseModel):
    approver_id: str
    state: ApprovalState
    decided_at: datetime = Field(default_factory=datetime.now)
    comments: Optional[str] = Field(None, max_length=2048)
    escalation_reason: Optional[str] = None
    delegated_from: Optional[str] = None
    signature_ref: Optional[str] = None


class ApprovalStep(BaseModel):
    step_order: int = Field(..., ge=1)
    approver_id: str
    role_required: Optional[str] = None
    state: ApprovalState = ApprovalState.PENDING
    min_amount: float = Field(default=0.0, ge=0)
    max_amount: Optional[float] = None
    decision: Optional[ApprovalDecision] = None
    timeout_hours: Optional[int] = None
    escalation_user_id: Optional[str] = None
    is_parallel: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_resolved(self) -> bool:
        return self.state in (ApprovalState.APPROVED, ApprovalState.REJECTED,
                              ApprovalState.CANCELLED, ApprovalState.ESCALATED)


class ApprovalChain(TimestampMixin, SoftDeleteMixin, VersionMixin):
    entity_type: str  # expense, reimbursement, settlement
    entity_id: str
    title: str = Field(..., max_length=256)
    steps: List[ApprovalStep] = Field(default_factory=list)
    current_step: int = Field(default=1, ge=1)
    state: ApprovalState = ApprovalState.PENDING
    initiated_by: str
    initiated_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    amount: float = Field(..., ge=0)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def current_step_obj(self) -> Optional[ApprovalStep]:
        for step in self.steps:
            if step.step_order == self.current_step:
                return step
        return None

    @property
    def is_fully_approved(self) -> bool:
        return all(s.state == ApprovalState.APPROVED for s in self.steps)

    @property
    def max_step_order(self) -> int:
        return max((s.step_order for s in self.steps), default=0)

    def advance_step(self) -> bool:
        if self.current_step >= self.max_step_order:
            return False
        self.current_step += 1
        return True
