from __future__ import annotations

from typing import Dict, List, Set, Tuple

from finance_platform.amortization.models import AmortizationStatus


class AmortizationStateMachine:
    _TRANSITIONS: Dict[AmortizationStatus, Set[AmortizationStatus]] = {
        AmortizationStatus.DRAFT: {
            AmortizationStatus.ACTIVE,
            AmortizationStatus.CANCELLED,
        },
        AmortizationStatus.ACTIVE: {
            AmortizationStatus.PAUSED,
            AmortizationStatus.COMPLETED,
            AmortizationStatus.CANCELLED,
        },
        AmortizationStatus.PAUSED: {
            AmortizationStatus.ACTIVE,
            AmortizationStatus.CANCELLED,
        },
        AmortizationStatus.COMPLETED: set(),
        AmortizationStatus.CANCELLED: set(),
        AmortizationStatus.ARCHIVED: set(),
    }

    def can_transition(self, current: AmortizationStatus, target: AmortizationStatus) -> bool:
        allowed = self._TRANSITIONS.get(current, set())
        return target in allowed

    def get_allowed_transitions(self, current: AmortizationStatus) -> List[AmortizationStatus]:
        return sorted(self._TRANSITIONS.get(current, set()), key=lambda s: s.value)

    def validate_transition(self, current: AmortizationStatus, target: AmortizationStatus) -> None:
        if not self.can_transition(current, target):
            from finance_platform.state_machines.base import StateTransitionError

            raise StateTransitionError(
                current_state=current.value,
                target_state=target.value,
                message=f"Cannot transition from {current.value} to {target.value}",
            )
