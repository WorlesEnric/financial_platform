from __future__ import annotations

from enum import Enum
from typing import Optional

from finance_platform.settlements.exceptions import SettlementStateTransitionError


class SettlementState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class SettlementEvent(str, Enum):
    APPROVE = "approve"
    START_PROCESSING = "start_processing"
    COMPLETE = "complete"
    FAIL = "fail"
    REVERSE = "reverse"
    CANCEL = "cancel"
    HOLD = "hold"
    RESUME = "resume"
    RETRY = "retry"


class SettlementStateMachine:
    _transitions: dict[tuple[SettlementState, SettlementEvent], SettlementState] = {
        (SettlementState.PENDING, SettlementEvent.APPROVE): SettlementState.APPROVED,
        (SettlementState.PENDING, SettlementEvent.CANCEL): SettlementState.CANCELLED,
        (SettlementState.PENDING, SettlementEvent.HOLD): SettlementState.ON_HOLD,
        (SettlementState.APPROVED, SettlementEvent.START_PROCESSING): SettlementState.PROCESSING,
        (SettlementState.APPROVED, SettlementEvent.CANCEL): SettlementState.CANCELLED,
        (SettlementState.APPROVED, SettlementEvent.HOLD): SettlementState.ON_HOLD,
        (SettlementState.PROCESSING, SettlementEvent.COMPLETE): SettlementState.COMPLETED,
        (SettlementState.PROCESSING, SettlementEvent.FAIL): SettlementState.FAILED,
        (SettlementState.PROCESSING, SettlementEvent.HOLD): SettlementState.ON_HOLD,
        (SettlementState.COMPLETED, SettlementEvent.REVERSE): SettlementState.REVERSED,
        (SettlementState.FAILED, SettlementEvent.RETRY): SettlementState.PROCESSING,
        (SettlementState.FAILED, SettlementEvent.CANCEL): SettlementState.CANCELLED,
        (SettlementState.FAILED, SettlementEvent.HOLD): SettlementState.ON_HOLD,
        (SettlementState.ON_HOLD, SettlementEvent.RESUME): SettlementState.PENDING,
        (SettlementState.ON_HOLD, SettlementEvent.CANCEL): SettlementState.CANCELLED,
        (SettlementState.REVERSED, SettlementEvent.RETRY): SettlementState.PENDING,
    }

    _terminal_states: set[SettlementState] = {
        SettlementState.COMPLETED,
        SettlementState.REVERSED,
        SettlementState.CANCELLED,
    }

    _allowed_source_states: set[SettlementState] = {
        SettlementState.PENDING,
        SettlementState.APPROVED,
        SettlementState.PROCESSING,
        SettlementState.FAILED,
        SettlementState.ON_HOLD,
    }

    def __init__(self, initial_state: SettlementState = SettlementState.PENDING) -> None:
        self._state: SettlementState = initial_state

    @property
    def state(self) -> SettlementState:
        return self._state

    @property
    def is_terminal(self) -> bool:
        return self._state in self._terminal_states

    @property
    def is_active(self) -> bool:
        return self._state in self._allowed_source_states

    @property
    def allowed_events(self) -> list[SettlementEvent]:
        return [
            event
            for (source, event) in self._transitions
            if source == self._state
        ]

    def can_transition(self, event: SettlementEvent) -> bool:
        return (self._state, event) in self._transitions

    def transition(self, event: SettlementEvent) -> SettlementState:
        key = (self._state, event)
        if key not in self._transitions:
            raise SettlementStateTransitionError(
                current=self._state.value,
                target=event.value,
                reason=f"No transition defined for event '{event.value}' from state '{self._state.value}'",
            )

        target = self._transitions[key]
        self._state = target
        return self._state

    def apply(self, event: SettlementEvent) -> SettlementState:
        return self.transition(event)

    def reset(self, state: SettlementState = SettlementState.PENDING) -> None:
        self._state = state

    @staticmethod
    def get_allowed_transitions() -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for (source, event), target in SettlementStateMachine._transitions.items():
            key = f"{source.value} -> {event.value}"
            result[key] = [source.value, event.value, target.value]
        return result

    @staticmethod
    def transition_matrix() -> dict[str, dict[str, Optional[str]]]:
        states = [s.value for s in SettlementState]
        events = [e.value for e in SettlementEvent]
        matrix: dict[str, dict[str, Optional[str]]] = {}
        for state in states:
            matrix[state] = {}
            for event in events:
                key = (SettlementState(state), SettlementEvent(event))
                if key in SettlementStateMachine._transitions:
                    matrix[state][event] = SettlementStateMachine._transitions[key].value
                else:
                    matrix[state][event] = None
        return matrix

    def describe(self) -> str:
        events = ", ".join(e.value for e in self.allowed_events) or "none"
        return (
            f"SettlementStateMachine(state={self._state.value}, "
            f"terminal={self.is_terminal}, "
            f"allowed_events=[{events}])"
        )
