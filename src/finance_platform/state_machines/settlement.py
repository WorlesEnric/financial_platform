from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional, Set

from finance_platform.models.base import SettlementStatus
from finance_platform.models.settlement import Settlement, SettlementRun
from finance_platform.state_machines.base import StateMachine, StateMachineRegistry


@StateMachineRegistry.register
class SettlementStateMachine(StateMachine[Settlement]):
    entity_type = "settlement"

    @property
    def state_field(self) -> str:
        return "status"

    @property
    def transitions(self) -> Dict[str, Set[str]]:
        return {
            SettlementStatus.PENDING: {SettlementStatus.PROCESSING, SettlementStatus.FAILED, SettlementStatus.COMPLETED, SettlementStatus.REVERSED},
            SettlementStatus.PROCESSING: {SettlementStatus.COMPLETED, SettlementStatus.FAILED, SettlementStatus.REVERSED},
            SettlementStatus.COMPLETED: {SettlementStatus.REVERSED},
            SettlementStatus.FAILED: {SettlementStatus.PENDING, SettlementStatus.REVERSED},
            SettlementStatus.REVERSED: set(),
        }

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: Settlement,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if to_state == SettlementStatus.COMPLETED:
            entity.settlement_date = date.today()
            if context:
                entity.payment_method = context.get("payment_method")
                entity.payment_reference = context.get("payment_reference")
                entity.approved_by = context.get("approved_by")
                entity.approved_at = datetime.now()


@StateMachineRegistry.register
class SettlementRunStateMachine(StateMachine[SettlementRun]):
    entity_type = "settlement_run"

    @property
    def state_field(self) -> str:
        return "status"

    @property
    def transitions(self) -> Dict[str, Set[str]]:
        return {
            SettlementStatus.PENDING: {SettlementStatus.PROCESSING, SettlementStatus.FAILED, SettlementStatus.COMPLETED},
            SettlementStatus.PROCESSING: {SettlementStatus.COMPLETED, SettlementStatus.FAILED},
            SettlementStatus.COMPLETED: set(),
            SettlementStatus.FAILED: {SettlementStatus.PENDING},
        }

    def _on_before_transition(
        self,
        from_state: str,
        to_state: str,
        entity: SettlementRun,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        if to_state == SettlementStatus.PROCESSING:
            entity.started_at = datetime.now()
        elif to_state == SettlementStatus.COMPLETED:
            entity.completed_at = datetime.now()
        elif to_state == SettlementStatus.FAILED:
            entity.completed_at = datetime.now()
            if context:
                entity.error_message = context.get("error_message")
