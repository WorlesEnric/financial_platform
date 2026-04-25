from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Set

from finance_platform.models.amortization import AmortizationSchedule
from finance_platform.state_machines.base import StateMachine, StateMachineRegistry


class AmortizationStatus:
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


@StateMachineRegistry.register
class AmortizationStateMachine(StateMachine[AmortizationSchedule]):
    entity_type = "amortization"

    @property
    def state_field(self) -> str:
        return "status"

    @property
    def transitions(self) -> Dict[str, Set[str]]:
        return {
            AmortizationStatus.DRAFT: {AmortizationStatus.ACTIVE, AmortizationStatus.CANCELLED},
            AmortizationStatus.ACTIVE: {AmortizationStatus.COMPLETED, AmortizationStatus.SUSPENDED, AmortizationStatus.CANCELLED},
            AmortizationStatus.SUSPENDED: {AmortizationStatus.ACTIVE, AmortizationStatus.CANCELLED},
            AmortizationStatus.COMPLETED: set(),
            AmortizationStatus.CANCELLED: set(),
        }

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: AmortizationSchedule,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if to_state == AmortizationStatus.ACTIVE and from_state == AmortizationStatus.DRAFT:
            from datetime import date
            if not entity.entries:
                from finance_platform.state_machines.base import StateTransitionError
                raise StateTransitionError(
                    from_state,
                    to_state,
                    self.entity_type,
                    "Cannot activate an amortization schedule with no entries",
                )
