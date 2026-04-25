from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.errors.exceptions import (
    NotFoundError,
    BusinessRuleError,
    SettlementError,
    SettlementReconciliationError,
)
from finance_platform.models.base import CurrencyCode, SettlementStatus
from finance_platform.models.settlement import Settlement, SettlementAllocation, SettlementRun
from finance_platform.state_machines.settlement import SettlementStateMachine, SettlementRunStateMachine


class SettlementService:
    def __init__(self) -> None:
        self._runs: Dict[str, SettlementRun] = {}
        self._settlements: Dict[str, Settlement] = {}

    def create_settlement_run(
        self,
        description: Optional[str] = None,
        currency: CurrencyCode = CurrencyCode.USD,
        triggered_by: Optional[str] = None,
        is_automatic: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SettlementRun:
        run = SettlementRun(
            description=description,
            currency=currency,
            triggered_by=triggered_by,
            is_automatic=is_automatic,
            metadata=metadata or {},
        )
        self._runs[run.id] = run
        return run

    def get_settlement_run(self, run_id: str) -> SettlementRun:
        run = self._runs.get(run_id)
        if not run or run.is_deleted:
            raise NotFoundError(f"SettlementRun {run_id} not found", resource_type="SettlementRun", resource_id=run_id)
        return run

    def list_settlement_runs(
        self,
        status: Optional[SettlementStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[SettlementRun]:
        results = [r for r in self._runs.values() if not r.is_deleted]
        if status:
            results = [r for r in results if r.status == status]
        if date_from:
            results = [r for r in results if r.run_date >= date_from]
        if date_to:
            results = [r for r in results if r.run_date <= date_to]
        return results

    def start_settlement_run(self, run_id: str) -> SettlementRun:
        run = self.get_settlement_run(run_id)
        sm = SettlementRunStateMachine(run)
        sm.transition(SettlementStatus.PROCESSING)
        run.touch()
        return run

    def complete_settlement_run(self, run_id: str) -> SettlementRun:
        run = self.get_settlement_run(run_id)
        sm = SettlementRunStateMachine(run)
        sm.transition(SettlementStatus.COMPLETED)
        run.touch()
        return run

    def fail_settlement_run(self, run_id: str, error_message: str) -> SettlementRun:
        run = self.get_settlement_run(run_id)
        sm = SettlementRunStateMachine(run)
        sm.transition(SettlementStatus.FAILED, context={"error_message": error_message})
        run.touch()
        return run

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        run = self.get_settlement_run(run_id)
        settlements = [s for s in self._settlements.values() if s.settlement_run_id == run_id]
        total = sum(s.settled_amount for s in settlements)
        by_status: Dict[str, int] = {}
        for s in settlements:
            by_status[s.status.value] = by_status.get(s.status.value, 0) + 1
        return {
            "run_id": run.id,
            "status": run.status.value,
            "total_settled": run.total_settled,
            "settlement_count": len(settlements),
            "settled_total": round(total, 2),
            "by_status": by_status,
            "run_date": run.run_date.isoformat(),
            "is_automatic": run.is_automatic,
        }

    def create_settlement(
        self,
        entity_type: str,
        entity_id: str,
        total_amount: float,
        settled_amount: float,
        currency: CurrencyCode = CurrencyCode.USD,
        settlement_run_id: Optional[str] = None,
        payment_method: Optional[str] = None,
        bank_account_ref: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Settlement:
        remaining = round(total_amount - settled_amount, 2)
        settlement = Settlement(
            settlement_run_id=settlement_run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            total_amount=total_amount,
            settled_amount=settled_amount,
            remaining_amount=remaining,
            currency=currency,
            payment_method=payment_method,
            bank_account_ref=bank_account_ref,
            notes=notes,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._settlements[settlement.id] = settlement
        if settlement_run_id:
            run = self.get_settlement_run(settlement_run_id)
            run.total_settled = round(run.total_settled + settled_amount, 2)
        return settlement

    def get_settlement(self, settlement_id: str) -> Settlement:
        settlement = self._settlements.get(settlement_id)
        if not settlement or settlement.is_deleted:
            raise NotFoundError(f"Settlement {settlement_id} not found", resource_type="Settlement", resource_id=settlement_id)
        return settlement

    def list_settlements(
        self,
        run_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: Optional[SettlementStatus] = None,
    ) -> List[Settlement]:
        results = [s for s in self._settlements.values() if not s.is_deleted]
        if run_id:
            results = [s for s in results if s.settlement_run_id == run_id]
        if entity_type:
            results = [s for s in results if s.entity_type == entity_type]
        if entity_id:
            results = [s for s in results if s.entity_id == entity_id]
        if status:
            results = [s for s in results if s.status == status]
        return results

    def add_allocation(
        self,
        settlement_id: str,
        entity_type: str,
        entity_id: str,
        allocated_amount: float,
        currency: CurrencyCode = CurrencyCode.USD,
        notes: Optional[str] = None,
    ) -> Settlement:
        settlement = self.get_settlement(settlement_id)
        allocation = SettlementAllocation(
            entity_type=entity_type,
            entity_id=entity_id,
            allocated_amount=allocated_amount,
            currency=currency,
            notes=notes,
        )
        settlement.allocations.append(allocation)
        settlement.touch()
        return settlement

    def process_settlement(
        self,
        settlement_id: str,
        payment_method: str,
        payment_reference: Optional[str] = None,
        approved_by: Optional[str] = None,
    ) -> Settlement:
        settlement = self.get_settlement(settlement_id)
        sm = SettlementStateMachine(settlement)
        sm.transition(SettlementStatus.COMPLETED, context={
            "payment_method": payment_method,
            "payment_reference": payment_reference,
            "approved_by": approved_by,
        })
        settlement.touch()
        return settlement

    def reverse_settlement(self, settlement_id: str) -> Settlement:
        settlement = self.get_settlement(settlement_id)
        sm = SettlementStateMachine(settlement)
        sm.transition(SettlementStatus.REVERSED)
        settlement.touch()
        return settlement

    def reconcile_settlements(self, run_id: str) -> Dict[str, Any]:
        run = self.get_settlement_run(run_id)
        settlements = self.list_settlements(run_id=run_id)
        total_allocated = sum(s.settled_amount for s in settlements)
        expected = run.total_settled
        difference = round(abs(total_allocated - expected), 2)
        if difference > 0.01:
            raise SettlementReconciliationError(
                f"Settlement run {run_id} has imbalance: allocated={total_allocated}, expected={expected}"
            )
        return {
            "run_id": run_id,
            "total_allocated": round(total_allocated, 2),
            "expected": expected,
            "difference": difference,
            "is_balanced": difference <= 0.01,
            "settlement_count": len(settlements),
        }

    def bulk_create_settlements(
        self,
        run_id: str,
        items: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        succeeded: List[str] = []
        failed: List[str] = []
        for item in items:
            try:
                settlement = self.create_settlement(
                    entity_type=item["entity_type"],
                    entity_id=item["entity_id"],
                    total_amount=item["total_amount"],
                    settled_amount=item["settled_amount"],
                    currency=CurrencyCode(item.get("currency", "USD")),
                    settlement_run_id=run_id,
                    payment_method=item.get("payment_method"),
                    notes=item.get("notes"),
                )
                succeeded.append(settlement.id)
            except Exception:
                failed.append(item.get("entity_id", "unknown"))
        return succeeded, failed
