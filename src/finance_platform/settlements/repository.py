from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from finance_platform.models.settlement import Settlement, SettlementAllocation, SettlementRun
from finance_platform.models.base import SettlementStatus
from finance_platform.settlements.exceptions import (
    SettlementNotFoundError,
    SettlementRunNotFoundError,
)
from finance_platform.settlements.models import (
    EntityType,
    PaymentMethod,
    SettlementPayment,
    SettlementBatch,
    SettlementBatchStatus,
    SettlementFilter,
    SettlementSummary,
    PaymentStatus,
)
from finance_platform.settlements.state_machine import SettlementState


class SettlementRepository:
    def __init__(self) -> None:
        self._settlements: dict[str, Settlement] = {}
        self._runs: dict[str, SettlementRun] = {}
        self._payments: dict[str, SettlementPayment] = {}
        self._batches: dict[str, SettlementBatch] = {}

    # --- Settlements ---

    def save(self, settlement: Settlement) -> Settlement:
        settlement.updated_at = datetime.now(timezone.utc)
        self._settlements[settlement.id] = settlement
        return settlement

    def get(self, settlement_id: str) -> Optional[Settlement]:
        return self._settlements.get(settlement_id)

    def get_or_raise(self, settlement_id: str) -> Settlement:
        settlement = self.get(settlement_id)
        if settlement is None:
            raise SettlementNotFoundError(settlement_id)
        return settlement

    def list(
        self,
        filter_obj: Optional[SettlementFilter] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Settlement], int]:
        results = list(self._settlements.values())

        if filter_obj:
            if filter_obj.entity_type:
                results = [s for s in results if s.entity_type == filter_obj.entity_type.value]
            if filter_obj.entity_id:
                results = [s for s in results if s.entity_id == filter_obj.entity_id]
            if filter_obj.status:
                results = [s for s in results if s.status == filter_obj.status]
            if filter_obj.run_id:
                results = [s for s in results if s.settlement_run_id == filter_obj.run_id]
            if filter_obj.currency:
                results = [s for s in results if s.currency == filter_obj.currency]
            if filter_obj.date_from:
                results = [
                    s for s in results
                    if s.created_at and s.created_at.date() >= filter_obj.date_from
                ]
            if filter_obj.date_to:
                results = [
                    s for s in results
                    if s.created_at and s.created_at.date() <= filter_obj.date_to
                ]
            if filter_obj.tags:
                results = [
                    s for s in results
                    if any(t in s.tags for t in filter_obj.tags)
                ]
            if not filter_obj.is_deleted:
                results = [s for s in results if not getattr(s, 'is_deleted', False)]

        sort_desc = sort_order == "desc"
        if sort_by == "created_at":
            results.sort(key=lambda s: s.created_at or datetime.min, reverse=sort_desc)
        elif sort_by == "updated_at":
            results.sort(key=lambda s: s.updated_at or datetime.min, reverse=sort_desc)
        elif sort_by == "total_amount":
            results.sort(key=lambda s: s.total_amount, reverse=sort_desc)
        elif sort_by == "settled_amount":
            results.sort(key=lambda s: s.settled_amount, reverse=sort_desc)
        else:
            results.sort(key=lambda s: s.created_at or datetime.min, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return paginated, total

    def delete(self, settlement_id: str) -> bool:
        return self._settlements.pop(settlement_id, None) is not None

    def soft_delete(self, settlement_id: str) -> Optional[Settlement]:
        settlement = self.get(settlement_id)
        if settlement and hasattr(settlement, 'soft_delete'):
            settlement.soft_delete()
            return settlement
        return None

    # --- Settlement Runs ---

    def save_run(self, run: SettlementRun) -> SettlementRun:
        run.updated_at = datetime.now(timezone.utc)
        self._runs[run.id] = run
        return run

    def get_run(self, run_id: str) -> Optional[SettlementRun]:
        return self._runs.get(run_id)

    def get_run_or_raise(self, run_id: str) -> SettlementRun:
        run = self.get_run(run_id)
        if run is None:
            raise SettlementRunNotFoundError(run_id)
        return run

    def list_runs(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SettlementRun], int]:
        results = list(self._runs.values())
        if status:
            results = [r for r in results if r.status == status]

        results.sort(key=lambda r: r.run_date if r.run_date else date.min, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], total

    def get_active_run(self) -> Optional[SettlementRun]:
        for run in self._runs.values():
            if run.status in (SettlementStatus.PENDING.value, SettlementStatus.PROCESSING.value):
                return run
        return None

    def delete_run(self, run_id: str) -> bool:
        return self._runs.pop(run_id, None) is not None

    # --- Payments ---

    def save_payment(self, payment: SettlementPayment) -> SettlementPayment:
        payment.updated_at = datetime.now(timezone.utc)
        self._payments[payment.id] = payment
        return payment

    def get_payment(self, payment_id: str) -> Optional[SettlementPayment]:
        return self._payments.get(payment_id)

    def list_payments(
        self,
        settlement_id: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SettlementPayment], int]:
        results = list(self._payments.values())
        if settlement_id:
            results = [p for p in results if p.settlement_id == settlement_id]
        if run_id:
            results = [p for p in results if p.run_id == run_id]
        if status:
            results = [p for p in results if p.status == status]
        results.sort(key=lambda p: p.created_at, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], total

    def delete_payment(self, payment_id: str) -> bool:
        return self._payments.pop(payment_id, None) is not None

    # --- Batches ---

    def save_batch(self, batch: SettlementBatch) -> SettlementBatch:
        batch.updated_at = datetime.now(timezone.utc)
        self._batches[batch.id] = batch
        return batch

    def get_batch(self, batch_id: str) -> Optional[SettlementBatch]:
        return self._batches.get(batch_id)

    def list_batches(
        self,
        run_id: Optional[str] = None,
        status: Optional[SettlementBatchStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SettlementBatch], int]:
        results = list(self._batches.values())
        if run_id:
            results = [b for b in results if b.run_id == run_id]
        if status:
            results = [b for b in results if b.status == status]
        results.sort(key=lambda b: b.created_at, reverse=True)
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        return results[start:end], total

    # --- Summary / Stats ---

    def get_summary(self) -> SettlementSummary:
        summary = SettlementSummary()
        now = datetime.now(timezone.utc)

        for s in self._settlements.values():
            if getattr(s, 'is_deleted', False):
                continue
            if s.status == SettlementStatus.PENDING.value:
                summary.total_pending += 1
                summary.total_amount_pending += s.total_amount
            elif s.status == SettlementStatus.PROCESSING.value:
                summary.total_processing += 1
            elif s.status == SettlementStatus.COMPLETED.value:
                summary.total_completed += 1
                summary.total_amount_settled += s.settled_amount
            elif s.status == SettlementStatus.FAILED.value:
                summary.total_failed += 1
            elif s.status == SettlementStatus.REVERSED.value:
                summary.total_reversed += 1

            summary.pending_by_entity_type[s.entity_type] = (
                summary.pending_by_entity_type.get(s.entity_type, 0) + 1
            )
            summary.amount_by_currency[s.currency] = (
                summary.amount_by_currency.get(s.currency, 0) + s.total_amount
            )

        for s in self._settlements.values():
            if s.status == SettlementStatus.PENDING.value and not getattr(s, 'is_deleted', False):
                allocations_total = sum(a.allocated_amount for a in s.allocations) if s.allocations else 0
                remaining = s.total_amount - allocations_total - s.settled_amount
                if remaining > 0:
                    summary.total_high_priority_pending += 1
                    summary.total_high_priority_amount += remaining

        active_runs = [r for r in self._runs.values()
                       if r.status in (SettlementStatus.PENDING.value, SettlementStatus.PROCESSING.value)]
        summary.active_run_count = len(active_runs)

        completed_runs = [r for r in self._runs.values()
                          if r.status == SettlementStatus.COMPLETED.value and r.run_date]
        if completed_runs:
            latest = max(completed_runs, key=lambda r: r.run_date)
            summary.last_run_date = latest.run_date

        return summary

    def count_by_status(self, status: str) -> int:
        return sum(1 for s in self._settlements.values()
                   if s.status == status and not getattr(s, 'is_deleted', False))

    def total_settled_amount(self, currency: str = "USD") -> float:
        return sum(
            s.settled_amount for s in self._settlements.values()
            if s.currency == currency
            and s.status == SettlementStatus.COMPLETED.value
            and not getattr(s, 'is_deleted', False)
        )

    def find_by_entity(self, entity_type: str, entity_id: str) -> list[Settlement]:
        return [
            s for s in self._settlements.values()
            if s.entity_type == entity_type and s.entity_id == entity_id
        ]
