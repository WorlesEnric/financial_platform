from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Set

from finance_platform.models.approval import ApprovalChain, ApprovalState
from finance_platform.state_machines.base import StateMachine, StateMachineRegistry


@StateMachineRegistry.register
class ApprovalChainStateMachine(StateMachine[ApprovalChain]):
    entity_type = "approval_chain"

    @property
    def state_field(self) -> str:
        return "state"

    @property
    def transitions(self) -> Dict[str, Set[str]]:
        return {
            ApprovalState.PENDING: {
                ApprovalState.APPROVED,
                ApprovalState.REJECTED,
                ApprovalState.CANCELLED,
                ApprovalState.ESCALATED,
                ApprovalState.DEFERRED,
            },
            ApprovalState.APPROVED: set(),
            ApprovalState.REJECTED: set(),
            ApprovalState.CANCELLED: set(),
            ApprovalState.ESCALATED: {ApprovalState.APPROVED, ApprovalState.REJECTED, ApprovalState.CANCELLED},
            ApprovalState.DEFERRED: {
                ApprovalState.PENDING,
                ApprovalState.APPROVED,
                ApprovalState.REJECTED,
                ApprovalState.CANCELLED,
                ApprovalState.ESCALATED,
            },
        }

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: ApprovalChain,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if to_state in (ApprovalState.APPROVED, ApprovalState.REJECTED, ApprovalState.CANCELLED):
            entity.resolved_at = datetime.now()
            if context:
                entity.resolved_by = context.get("resolved_by")
