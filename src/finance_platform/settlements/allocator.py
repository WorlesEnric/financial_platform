from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from finance_platform.settlements.exceptions import (
    SettlementAllocationError,
    SettlementOverRegistrationError,
    SettlementPriorityError,
)
from finance_platform.settlements.models import (
    EntityType,
    SettlementOrder,
    SettlementPriority,
)


class AllocationResult:
    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        allocated_amount: float,
        remaining_after: float,
        currency: str = "USD",
        fx_rate: Optional[float] = None,
        fx_from_currency: Optional[str] = None,
    ) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.allocated_amount = allocated_amount
        self.remaining_after = remaining_after
        self.currency = currency
        self.fx_rate = fx_rate
        self.fx_from_currency = fx_from_currency
        self.timestamp = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"AllocationResult(entity={self.entity_type}:{self.entity_id}, "
            f"amount={self.allocated_amount}, remaining={self.remaining_after})"
        )


class SettlementAllocator:
    def __init__(self) -> None:
        self._allocation_history: list[AllocationResult] = []

    @property
    def allocation_history(self) -> list[AllocationResult]:
        return list(self._allocation_history)

    def clear_history(self) -> None:
        self._allocation_history.clear()

    def allocate(
        self,
        available_funds: float,
        orders: list[SettlementOrder],
        currency: str = "USD",
    ) -> list[AllocationResult]:
        results: list[AllocationResult] = []
        remaining = available_funds

        sorted_orders = self._sort_by_priority(orders)

        for order in sorted_orders:
            if remaining <= 0:
                break

            if order.currency != currency:
                raise SettlementAllocationError(
                    f"Currency mismatch: order is in {order.currency}, "
                    f"allocator using {currency}"
                )

            if order.amount <= 0:
                continue

            if remaining < order.amount:
                result = AllocationResult(
                    entity_type=order.entity_type.value,
                    entity_id=order.entity_id,
                    allocated_amount=remaining,
                    remaining_after=order.amount - remaining,
                    currency=currency,
                )
                results.append(result)
                self._allocation_history.append(result)
                remaining = 0.0
            else:
                result = AllocationResult(
                    entity_type=order.entity_type.value,
                    entity_id=order.entity_id,
                    allocated_amount=order.amount,
                    remaining_after=0.0,
                    currency=currency,
                )
                results.append(result)
                self._allocation_history.append(result)
                remaining -= order.amount

        return results

    def allocate_fully(
        self,
        orders: list[SettlementOrder],
        currency: str = "USD",
    ) -> list[AllocationResult]:
        total = sum(o.amount for o in orders)
        return self.allocate(total, orders, currency)

    def allocate_with_priority(
        self,
        available_funds: float,
        high_priority_orders: list[SettlementOrder],
        normal_orders: list[SettlementOrder],
        low_priority_orders: list[SettlementOrder] | None = None,
        currency: str = "USD",
    ) -> list[AllocationResult]:
        results: list[AllocationResult] = []
        remaining = available_funds

        high_sorted = self._sort_by_fifo(high_priority_orders)
        high_result = self.allocate(remaining, high_sorted, currency)
        results.extend(high_result)
        allocated = sum(r.allocated_amount for r in high_result)
        remaining -= allocated

        if remaining > 0:
            normal_sorted = self._sort_by_fifo(normal_orders)
            normal_result = self.allocate(remaining, normal_sorted, currency)
            results.extend(normal_result)
            allocated = sum(r.allocated_amount for r in normal_result)
            remaining -= allocated

        if remaining > 0 and low_priority_orders:
            low_sorted = self._sort_by_fifo(low_priority_orders)
            low_result = self.allocate(remaining, low_sorted, currency)
            results.extend(low_result)

        return results

    def validate_allocation(
        self,
        entity_type: EntityType,
        entity_id: str,
        requested_amount: float,
        outstanding_amount: float,
    ) -> None:
        remaining = outstanding_amount
        for alloc in self._allocation_history:
            if alloc.entity_type == entity_type.value and alloc.entity_id == entity_id:
                remaining -= alloc.allocated_amount

        remaining = max(0.0, remaining)

        if requested_amount > remaining:
            raise SettlementOverRegistrationError(
                entity_type=entity_type.value,
                entity_id=entity_id,
                amount=requested_amount,
                available=remaining,
            )

    def compute_remaining_outstanding(
        self,
        original_amount: float,
        settled_amount: float,
    ) -> float:
        return round(max(0.0, original_amount - settled_amount), 2)

    def _sort_by_priority(self, orders: list[SettlementOrder]) -> list[SettlementOrder]:
        return sorted(orders, key=lambda o: o.sort_key)

    def _sort_by_fifo(self, orders: list[SettlementOrder]) -> list[SettlementOrder]:
        return sorted(orders, key=lambda o: o.created_at)

    def get_pending_high_priority(
        self, orders: list[SettlementOrder]
    ) -> list[SettlementOrder]:
        return [o for o in orders if o.priority == SettlementPriority.HIGH]

    def get_pending_normal_priority(
        self, orders: list[SettlementOrder]
    ) -> list[SettlementOrder]:
        return [o for o in orders if o.priority == SettlementPriority.NORMAL]

    def get_pending_low_priority(
        self, orders: list[SettlementOrder]
    ) -> list[SettlementOrder]:
        return [o for o in orders if o.priority == SettlementPriority.LOW]
