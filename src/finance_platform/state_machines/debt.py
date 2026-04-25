from __future__ import annotations

from typing import Any, Dict, Optional, Set

from finance_platform.models.base import DebtStatus
from finance_platform.models.debt import Debt
from finance_platform.state_machines.base import StateMachine, StateMachineRegistry


@StateMachineRegistry.register
class DebtStateMachine(StateMachine[Debt]):
    entity_type = "debt"

    @property
    def state_field(self) -> str:
        return "status"

    @property
    def transitions(self) -> Dict[str, Set[str]]:
        return {
            DebtStatus.ACTIVE: {
                DebtStatus.REPAID,
                DebtStatus.FORGIVEN,
                DebtStatus.WRITTEN_OFF,
                DebtStatus.CANCELLED,
            },
            DebtStatus.REPAID: set(),
            DebtStatus.FORGIVEN: set(),
            DebtStatus.WRITTEN_OFF: set(),
            DebtStatus.CANCELLED: set(),
        }

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: Debt,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if to_state == DebtStatus.REPAID:
            entity.outstanding_amount = 0.0
