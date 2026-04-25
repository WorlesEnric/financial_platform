from __future__ import annotations

from typing import Any, Dict, Optional, Set

from finance_platform.models.base import ApprovalState, ReimbursementStatus
from finance_platform.models.expense import Expense
from finance_platform.state_machines.base import StateMachine, StateMachineRegistry


@StateMachineRegistry.register
class ExpenseStateMachine(StateMachine[Expense]):
    entity_type = "expense"

    @property
    def state_field(self) -> str:
        return "status"

    @property
    def transitions(self) -> Dict[str, Set[str]]:
        return {
            ReimbursementStatus.DRAFT: {
                ReimbursementStatus.SUBMITTED,
                ReimbursementStatus.CANCELLED,
            },
            ReimbursementStatus.SUBMITTED: {
                ReimbursementStatus.APPROVED,
                ReimbursementStatus.REJECTED,
                ReimbursementStatus.CANCELLED,
            },
            ReimbursementStatus.APPROVED: {
                ReimbursementStatus.PAID,
                ReimbursementStatus.PARTIALLY_PAID,
                ReimbursementStatus.CANCELLED,
            },
            ReimbursementStatus.PARTIALLY_PAID: {
                ReimbursementStatus.PAID,
                ReimbursementStatus.CLOSED,
                ReimbursementStatus.CANCELLED,
            },
            ReimbursementStatus.PAID: {ReimbursementStatus.CLOSED},
            ReimbursementStatus.REJECTED: {ReimbursementStatus.DRAFT},
            ReimbursementStatus.CANCELLED: {ReimbursementStatus.DRAFT},
            ReimbursementStatus.CLOSED: set(),
        }

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: Expense,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        from datetime import datetime

        now = datetime.now()
        if to_state == ReimbursementStatus.SUBMITTED:
            entity.submitted_at = now
            entity.approval_state = ApprovalState.PENDING
        elif to_state == ReimbursementStatus.APPROVED:
            if context:
                entity.approved_by = context.get("approved_by")
            entity.approved_at = now
            entity.approval_state = ApprovalState.APPROVED
        elif to_state == ReimbursementStatus.REJECTED:
            if context:
                entity.rejection_reason = context.get("rejection_reason")
            entity.approval_state = ApprovalState.REJECTED
        elif to_state == ReimbursementStatus.PAID or to_state == ReimbursementStatus.PARTIALLY_PAID:
            entity.paid_at = now
