from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from finance_platform.models.settlement import Settlement, SettlementAllocation, SettlementRun
from finance_platform.models.base import SettlementStatus, CurrencyCode
from finance_platform.settlements.allocator import SettlementAllocator, AllocationResult
from finance_platform.settlements.exceptions import (
    SettlementAlreadyCompletedError,
    SettlementAlreadyReversedError,
    SettlementOverRegistrationError,
    SettlementNotFoundError,
    SettlementRunNotFoundError,
    SettlementRunInProgressError,
    SettlementValidationError,
    SettlementPaymentError,
    SettlementReconciliationFailedError,
)
from finance_platform.settlements.models import (
    EntityType,
    SettlementOrder,
    SettlementPayment,
    SettlementBatch,
    SettlementBatchStatus,
    SettlementFilter,
    SettlementPriority,
    SettlementSummary,
    PaymentMethod,
    PaymentStatus,
)
from finance_platform.settlements.repository import SettlementRepository
from finance_platform.settlements.state_machine import (
    SettlementStateMachine,
    SettlementState,
    SettlementEvent,
)


class SettlementService:
    def __init__(self, repository: Optional[SettlementRepository] = None) -> None:
        self.repository = repository or SettlementRepository()
        self.allocator = SettlementAllocator()

    # --- Settlement CRUD ---

    def create_settlement(
        self,
        entity_type: str,
        entity_id: str,
        total_amount: float,
        currency: str = "USD",
        priority: SettlementPriority = SettlementPriority.NORMAL,
        description: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        due_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Settlement:
        settlement = Settlement(
            entity_type=entity_type,
            entity_id=entity_id,
            total_amount=total_amount,
            settled_amount=0.0,
            remaining_amount=total_amount,
            currency=CurrencyCode(currency.upper()) if isinstance(currency, str) else currency,
            status=SettlementStatus.PENDING,
            tags=tags or [],
            metadata=metadata or {},
        )
        if description:
            settlement.notes = description
        self.repository.save(settlement)
        return settlement

    def get_settlement(self, settlement_id: str) -> Settlement:
        return self.repository.get_or_raise(settlement_id)

    def update_settlement(
        self,
        settlement_id: str,
        total_amount: Optional[float] = None,
        currency: Optional[str] = None,
        priority: Optional[SettlementPriority] = None,
        description: Optional[str] = None,
        department: Optional[str] = None,
        cost_center: Optional[str] = None,
        due_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> Settlement:
        settlement = self.repository.get_or_raise(settlement_id)
        self._check_not_terminal(settlement)

        if total_amount is not None:
            settlement.total_amount = total_amount
            settlement.remaining_amount = max(0.0, total_amount - settlement.settled_amount)
        if currency is not None:
            settlement.currency = CurrencyCode(currency.upper())
        if description is not None:
            settlement.notes = description
        if tags is not None:
            settlement.tags = tags
        if metadata is not None:
            settlement.metadata = metadata
        if notes is not None:
            settlement.notes = notes
        if due_date is not None:
            pass
        if reference_number is not None:
            pass

        self.repository.save(settlement)
        return settlement

    def delete_settlement(self, settlement_id: str) -> bool:
        settlement = self.repository.get_or_raise(settlement_id)
        self._check_not_terminal(settlement)
        return self.repository.delete(settlement_id)

    def soft_delete_settlement(self, settlement_id: str) -> Optional[Settlement]:
        settlement = self.repository.get_or_raise(settlement_id)
        return self.repository.soft_delete(settlement_id)

    def list_settlements(
        self,
        filter_obj: Optional[SettlementFilter] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Settlement], int]:
        return self.repository.list(filter_obj, page, page_size, sort_by, sort_order)

    # --- State Management ---

    def transition_settlement(
        self,
        settlement_id: str,
        event: SettlementEvent,
    ) -> Settlement:
        settlement = self.repository.get_or_raise(settlement_id)
        fsm = SettlementStateMachine(SettlementState(settlement.status))
        new_state = fsm.apply(event)
        settlement.status = new_state.value
        settlement.updated_at = datetime.now(timezone.utc)

        if event == SettlementEvent.COMPLETE:
            settlement.settlement_date = date.today()
        elif event == SettlementEvent.REVERSE:
            settlement.settlement_date = None

        self.repository.save(settlement)
        return settlement

    def approve_settlement(self, settlement_id: str, approved_by: str) -> Settlement:
        settlement = self.repository.get_or_raise(settlement_id)
        fsm = SettlementStateMachine(SettlementState(settlement.status))
        fsm.apply(SettlementEvent.APPROVE)
        settlement.status = SettlementState.APPROVED.value
        settlement.approved_by = approved_by
        settlement.approved_at = datetime.now(timezone.utc)
        self.repository.save(settlement)
        return settlement

    def complete_settlement(self, settlement_id: str) -> Settlement:
        return self.transition_settlement(settlement_id, SettlementEvent.COMPLETE)

    def fail_settlement(self, settlement_id: str, error_message: str = "") -> Settlement:
        settlement = self.repository.get_or_raise(settlement_id)
        fsm = SettlementStateMachine(SettlementState(settlement.status))
        fsm.apply(SettlementEvent.FAIL)
        settlement.status = SettlementState.FAILED.value
        if error_message:
            settlement.notes = (settlement.notes or "") + f"\nFAILED: {error_message}"
        self.repository.save(settlement)
        return settlement

    def reverse_settlement(self, settlement_id: str) -> Settlement:
        return self.transition_settlement(settlement_id, SettlementEvent.REVERSE)

    def cancel_settlement(self, settlement_id: str) -> Settlement:
        return self.transition_settlement(settlement_id, SettlementEvent.CANCEL)

    def hold_settlement(self, settlement_id: str) -> Settlement:
        return self.transition_settlement(settlement_id, SettlementEvent.HOLD)

    def resume_settlement(self, settlement_id: str) -> Settlement:
        return self.transition_settlement(settlement_id, SettlementEvent.RESUME)

    # --- Allocations ---

    def create_allocation(
        self,
        settlement_id: str,
        entity_type: str,
        entity_id: str,
        allocated_amount: float,
        currency: str = "USD",
        fx_rate: Optional[float] = None,
        fx_from_currency: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Settlement:
        settlement = self.repository.get_or_raise(settlement_id)
        self._check_not_terminal(settlement)

        self.allocator.validate_allocation(
            EntityType(entity_type),
            entity_id,
            allocated_amount,
            settlement.remaining_amount,
        )

        allocation = SettlementAllocation(
            entity_type=entity_type,
            entity_id=entity_id,
            allocated_amount=allocated_amount,
            currency=CurrencyCode(currency.upper()),
            fx_rate_applied=fx_rate,
            fx_from_currency=CurrencyCode(fx_from_currency.upper()) if fx_from_currency else None,
            notes=notes,
        )

        current_allocations = list(settlement.allocations)
        current_allocations.append(allocation)
        settlement.allocations = current_allocations

        new_settled = settlement.settled_amount + allocated_amount
        new_remaining = settlement.total_amount - new_settled
        settlement.settled_amount = new_settled
        settlement.remaining_amount = max(0.0, new_remaining)

        if abs(settlement.remaining_amount) < 0.001:
            settlement.status = SettlementStatus.COMPLETED.value
            settlement.settlement_date = date.today()

        self.repository.save(settlement)
        return settlement

    # --- G24: Settlements clear HIGH-priority carry-forward first, then FIFO; over-registration rejected ---

    def allocate_funds(
        self,
        available_funds: float,
        pending_settlements: list[Settlement],
        currency: str = "USD",
    ) -> list[AllocationResult]:
        orders: list[SettlementOrder] = []
        for s in pending_settlements:
            priority = SettlementPriority.HIGH if self._is_high_priority(s) else SettlementPriority.NORMAL
            orders.append(
                SettlementOrder(
                    entity_type=EntityType(s.entity_type),
                    entity_id=s.entity_id,
                    amount=s.remaining_amount,
                    currency=s.currency,
                    priority=priority,
                    created_at=s.created_at or datetime.now(timezone.utc),
                )
            )

        high = [o for o in orders if o.priority == SettlementPriority.HIGH]
        normal = [o for o in orders if o.priority == SettlementPriority.NORMAL]

        return self.allocator.allocate_with_priority(
            available_funds=available_funds,
            high_priority_orders=high,
            normal_orders=normal,
            currency=currency,
        )

    def process_settlement_batch(
        self,
        available_funds: float,
        pending_settlements: list[Settlement],
        currency: str = "USD",
    ) -> tuple[list[Settlement], list[AllocationResult]]:
        high_priority = [
            s for s in pending_settlements
            if self._is_high_priority(s) and s.remaining_amount > 0
        ]
        normal_priority = [
            s for s in pending_settlements
            if not self._is_high_priority(s) and s.remaining_amount > 0
        ]

        high_priority.sort(key=lambda s: s.created_at or datetime.min)
        normal_priority.sort(key=lambda s: s.created_at or datetime.min)

        all_items = high_priority + normal_priority
        results = self.allocate_funds(available_funds, all_items, currency)

        updated: list[Settlement] = []
        for result in results:
            matched = [
                s for s in pending_settlements
                if s.entity_id == result.entity_id
                and s.entity_type == result.entity_type
            ]
            for settlement in matched:
                if result.allocated_amount > 0:
                    if result.allocated_amount > settlement.remaining_amount:
                        raise SettlementOverRegistrationError(
                            entity_type=settlement.entity_type,
                            entity_id=settlement.entity_id,
                            amount=result.allocated_amount,
                            available=settlement.remaining_amount,
                        )
                    settlement.settled_amount += result.allocated_amount
                    settlement.remaining_amount = max(0.0, settlement.remaining_amount - result.allocated_amount)
                    settlement.updated_at = datetime.now(timezone.utc)

                    if abs(settlement.remaining_amount) < 0.001:
                        settlement.status = SettlementStatus.COMPLETED.value
                        settlement.settlement_date = date.today()

                    self.repository.save(settlement)
                    if settlement not in updated:
                        updated.append(settlement)

        return updated, results

    def _is_high_priority(self, settlement: Settlement) -> bool:
        if settlement.entity_type == EntityType.CARRY_FORWARD.value:
            return True
        if settlement.metadata and settlement.metadata.get("priority") == "high":
            return True
        if settlement.entity_type == EntityType.REIMBURSEMENT.value:
            return False
        if hasattr(settlement, 'tags') and settlement.tags:
            if any(t.lower() in ("high", "urgent", "critical") for t in settlement.tags):
                return True
        return False

    def register_for_settlement(
        self,
        entity_type: str,
        entity_id: str,
        amount: float,
        currency: str = "USD",
    ) -> Settlement:
        existing = self.repository.find_by_entity(entity_type, entity_id)
        active = [
            s for s in existing
            if s.status in (SettlementStatus.PENDING.value, SettlementStatus.PROCESSING.value)
        ]
        if active:
            total_registered = sum(s.total_amount for s in active)
            if total_registered + amount > max(s.total_amount for s in active) * 1.5:
                raise SettlementOverRegistrationError(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    amount=amount,
                    available=0.0,
                )

        return self.create_settlement(
            entity_type=entity_type,
            entity_id=entity_id,
            total_amount=amount,
            currency=currency,
        )

    # --- Settlement Runs ---

    def create_run(
        self,
        description: Optional[str] = None,
        currency: str = "USD",
        is_automatic: bool = False,
        settlement_ids: Optional[list[str]] = None,
        scheduled_date: Optional[date] = None,
        triggered_by: Optional[str] = None,
    ) -> SettlementRun:
        active = self.repository.get_active_run()
        if active:
            raise SettlementRunInProgressError(active.id)

        run = SettlementRun(
            description=description,
            currency=CurrencyCode(currency.upper()),
            status=SettlementStatus.PENDING,
            is_automatic=is_automatic,
            triggered_by=triggered_by,
        )
        self.repository.save_run(run)

        if settlement_ids:
            for sid in settlement_ids:
                try:
                    settlement = self.repository.get_or_raise(sid)
                    settlement.settlement_run_id = run.id
                    settlement.status = SettlementStatus.PROCESSING.value
                    self.repository.save(settlement)
                except SettlementNotFoundError:
                    pass

        return run

    def start_run(self, run_id: str) -> SettlementRun:
        run = self.repository.get_run_or_raise(run_id)
        if run.status != SettlementStatus.PENDING.value:
            raise SettlementRunInProgressError(run_id)

        run.status = SettlementStatus.PROCESSING.value
        run.started_at = datetime.now(timezone.utc)
        self.repository.save_run(run)

        pending = self.repository.list(
            SettlementFilter(status=SettlementStatus.PENDING.value),
            page_size=1000,
        )[0]
        for settlement in pending:
            settlement.settlement_run_id = run_id
            settlement.status = SettlementStatus.PROCESSING.value
            self.repository.save(settlement)

        return run

    def complete_run(
        self,
        run_id: str,
        error_message: Optional[str] = None,
    ) -> SettlementRun:
        run = self.repository.get_run_or_raise(run_id)
        if error_message:
            run.status = SettlementStatus.FAILED.value
            run.error_message = error_message
        else:
            run.status = SettlementStatus.COMPLETED.value

        run.completed_at = datetime.now(timezone.utc)
        run.total_settled = self._calculate_run_total(run_id)
        self.repository.save_run(run)
        return run

    def fail_run(self, run_id: str, error_message: str) -> SettlementRun:
        return self.complete_run(run_id, error_message=error_message)

    def get_run(self, run_id: str) -> SettlementRun:
        return self.repository.get_run_or_raise(run_id)

    def list_runs(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SettlementRun], int]:
        return self.repository.list_runs(status, page, page_size)

    # --- Payments ---

    def create_payment(
        self,
        settlement_id: str,
        amount: float,
        currency: str = "USD",
        payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER,
        bank_account_ref: Optional[str] = None,
        beneficiary_name: Optional[str] = None,
        beneficiary_account: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> SettlementPayment:
        settlement = self.repository.get_or_raise(settlement_id)
        if settlement.status == SettlementStatus.COMPLETED.value:
            raise SettlementAlreadyCompletedError(settlement_id, settlement.status)

        payment = SettlementPayment(
            id=str(uuid.uuid4()),
            settlement_id=settlement_id,
            run_id=settlement.settlement_run_id or "",
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            bank_account_ref=bank_account_ref or "",
            beneficiary_name=beneficiary_name or "",
            beneficiary_account=beneficiary_account or "",
            notes=notes or "",
        )
        self.repository.save_payment(payment)
        return payment

    def confirm_payment(self, payment_id: str, payment_reference: str) -> SettlementPayment:
        payment = self.repository.get_payment(payment_id)
        if payment is None:
            raise SettlementPaymentError(payment_id, "Payment not found")

        payment.status = PaymentStatus.CONFIRMED
        payment.payment_reference = payment_reference
        payment.confirmed_at = datetime.now(timezone.utc)
        payment.paid_at = payment.confirmed_at
        self.repository.save_payment(payment)

        settlement = self.repository.get(payment.settlement_id)
        if settlement and settlement.status == SettlementStatus.PROCESSING.value:
            settlement.settled_amount += payment.amount
            settlement.remaining_amount = max(0.0, settlement.remaining_amount - payment.amount)
            if abs(settlement.remaining_amount) < 0.001:
                settlement.status = SettlementStatus.COMPLETED.value
                settlement.settlement_date = date.today()
            self.repository.save(settlement)

        return payment

    def fail_payment(self, payment_id: str, error_message: str) -> SettlementPayment:
        payment = self.repository.get_payment(payment_id)
        if payment is None:
            raise SettlementPaymentError(payment_id, "Payment not found")

        payment.status = PaymentStatus.FAILED
        payment.notes = (payment.notes or "") + f"\nFAILED: {error_message}"
        self.repository.save_payment(payment)
        return payment

    def list_payments(
        self,
        settlement_id: Optional[str] = None,
        run_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SettlementPayment], int]:
        return self.repository.list_payments(settlement_id, run_id, status, page, page_size)

    # --- Batches ---

    def create_batch(
        self,
        run_id: str,
        name: str,
        settlement_ids: list[str],
        currency: str = "USD",
    ) -> SettlementBatch:
        run = self.repository.get_run_or_raise(run_id)
        batch = SettlementBatch(
            id=str(uuid.uuid4()),
            run_id=run_id,
            name=name,
            currency=currency,
            item_count=len(settlement_ids),
            total_amount=sum(
                self.repository.get_or_raise(sid).remaining_amount
                for sid in settlement_ids
            ),
        )
        self.repository.save_batch(batch)
        return batch

    def complete_batch(self, batch_id: str) -> SettlementBatch:
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch '{batch_id}' not found")
        batch.status = SettlementBatchStatus.COMPLETED
        batch.completed_at = datetime.now(timezone.utc)
        self.repository.save_batch(batch)
        return batch

    def fail_batch(self, batch_id: str, error_message: str) -> SettlementBatch:
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise ValueError(f"Batch '{batch_id}' not found")
        batch.status = SettlementBatchStatus.FAILED
        batch.error_message = error_message
        batch.completed_at = datetime.now(timezone.utc)
        self.repository.save_batch(batch)
        return batch

    def list_batches(
        self,
        run_id: Optional[str] = None,
        status: Optional[SettlementBatchStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[SettlementBatch], int]:
        return self.repository.list_batches(run_id, status, page, page_size)

    # --- Reconciliation ---

    def reconcile_run(self, run_id: str) -> dict[str, Any]:
        run = self.repository.get_run_or_raise(run_id)
        settlements = self.repository.list(
            SettlementFilter(run_id=run_id),
            page_size=10000,
        )[0]

        total_expected = sum(s.total_amount for s in settlements)
        total_settled = sum(s.settled_amount for s in settlements)
        total_remaining = sum(s.remaining_amount for s in settlements)

        discrepancy = abs(total_expected - total_settled - total_remaining)
        if discrepancy > 0.01:
            raise SettlementReconciliationFailedError(run_id, total_expected, total_settled)

        payments, _ = self.repository.list_payments(run_id=run_id, page_size=10000)
        total_paid = sum(p.amount for p in payments if p.status == PaymentStatus.CONFIRMED)

        return {
            "run_id": run_id,
            "total_expected": round(total_expected, 2),
            "total_settled": round(total_settled, 2),
            "total_remaining": round(total_remaining, 2),
            "total_paid": round(total_paid, 2),
            "settlement_count": len(settlements),
            "payment_count": len(payments),
            "discrepancy": round(discrepancy, 4),
            "reconciled": discrepancy <= 0.01,
        }

    # --- Summary ---

    def get_summary(self) -> SettlementSummary:
        return self.repository.get_summary()

    # --- Internal Helpers ---

    def _check_not_terminal(self, settlement: Settlement) -> None:
        terminal_states = {
            SettlementStatus.COMPLETED.value,
            SettlementStatus.REVERSED.value,
        }
        if settlement.status in terminal_states:
            raise SettlementAlreadyCompletedError(settlement.id, settlement.status)

    def _check_not_reversed(self, settlement: Settlement) -> None:
        if settlement.status == SettlementStatus.REVERSED.value:
            raise SettlementAlreadyReversedError(settlement.id)

    def _calculate_run_total(self, run_id: str) -> float:
        settlements = self.repository.list(
            SettlementFilter(run_id=run_id),
            page_size=10000,
        )[0]
        return round(sum(s.settled_amount for s in settlements), 2)
