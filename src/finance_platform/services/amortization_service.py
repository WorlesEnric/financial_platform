from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.errors.exceptions import (
    NotFoundError,
    BusinessRuleError,
    AmortizationCalculationError,
    AmortizationScheduleError,
)
from finance_platform.models.amortization import AmortizationEntry, AmortizationRule, AmortizationSchedule
from finance_platform.models.base import AmortizationMethod, CurrencyCode
from finance_platform.state_machines.amortization import AmortizationStateMachine, AmortizationStatus


class AmortizationService:
    def __init__(self) -> None:
        self._schedules: Dict[str, AmortizationSchedule] = {}

    def create_schedule(
        self,
        entity_type: str,
        entity_id: str,
        total_amount: float,
        currency: CurrencyCode,
        method: AmortizationMethod,
        total_periods: int,
        start_date: date,
        period_unit: str = "month",
        description: Optional[str] = None,
        residual_value: float = 0.0,
        acceleration_factor: Optional[float] = None,
        custom_schedule: Optional[Dict[int, float]] = None,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AmortizationSchedule:
        rule = AmortizationRule(
            method=method,
            total_periods=total_periods,
            period_unit=period_unit,
            start_date=start_date,
            residual_value=residual_value,
            acceleration_factor=acceleration_factor,
            custom_schedule=custom_schedule,
        )
        schedule = AmortizationSchedule(
            entity_type=entity_type,
            entity_id=entity_id,
            total_amount=total_amount,
            remaining_amount=total_amount,
            currency=currency,
            rule=rule,
            description=description,
            cost_center=cost_center,
            department=department,
            tags=tags or [],
            metadata=metadata or {},
        )
        schedule.entries = self._generate_entries(schedule)
        self._schedules[schedule.id] = schedule
        return schedule

    def _generate_entries(self, schedule: AmortizationSchedule) -> List[AmortizationEntry]:
        rule = schedule.rule
        amounts = self._compute_amortization_amounts(
            total=schedule.total_amount,
            method=rule.method,
            periods=rule.total_periods,
            residual=rule.residual_value,
            acceleration=rule.acceleration_factor,
            custom=rule.custom_schedule,
        )
        entries: List[AmortizationEntry] = []
        cursor = rule.start_date
        for i in range(rule.total_periods):
            period_num = i + 1
            period_start = cursor
            if rule.period_unit == "month":
                month = cursor.month + 1
                year = cursor.year + (month - 1) // 12
                month = ((month - 1) % 12) + 1
                try:
                    period_end = cursor.replace(year=year, month=month, day=1)
                except ValueError:
                    period_end = date(year, month, 1)
                from dateutil.relativedelta import relativedelta
                period_end = period_end - relativedelta(days=1)
            elif rule.period_unit == "quarter":
                from dateutil.relativedelta import relativedelta
                period_end = cursor + relativedelta(months=3) - relativedelta(days=1)
            else:
                from dateutil.relativedelta import relativedelta
                period_end = cursor + relativedelta(years=1) - relativedelta(days=1)
            scheduled = amounts[i] if i < len(amounts) else 0.0
            entries.append(AmortizationEntry(
                period_number=period_num,
                period_start=cursor,
                period_end=period_end,
                scheduled_amount=round(scheduled, 2),
            ))
            if rule.period_unit == "month":
                from dateutil.relativedelta import relativedelta
                cursor = cursor + relativedelta(months=1)
            elif rule.period_unit == "quarter":
                from dateutil.relativedelta import relativedelta
                cursor = cursor + relativedelta(months=3)
            else:
                cursor = date(cursor.year + 1, cursor.month, cursor.day)
        return entries

    def _compute_amortization_amounts(
        self,
        total: float,
        method: AmortizationMethod,
        periods: int,
        residual: float = 0.0,
        acceleration: Optional[float] = None,
        custom: Optional[Dict[int, float]] = None,
    ) -> List[float]:
        amortizable = total - residual
        if amortizable < 0:
            raise AmortizationCalculationError("Total amount must be greater than residual value")
        if method == AmortizationMethod.STRAIGHT_LINE:
            per_period = round(amortizable / periods, 2)
            amounts = [per_period] * periods
            diff = round(amortizable - sum(amounts), 2)
            if abs(diff) > 0.001:
                amounts[-1] = round(amounts[-1] + diff, 2)
            return amounts
        elif method == AmortizationMethod.DECLINING_BALANCE:
            rate = acceleration if acceleration is not None else 2.0 / periods
            amounts: List[float] = []
            remaining = amortizable
            for i in range(periods):
                if i == periods - 1:
                    amounts.append(round(remaining, 2))
                else:
                    amount = round(remaining * rate, 2)
                    amounts.append(amount)
                    remaining -= amount
            return amounts
        elif method == AmortizationMethod.SUM_OF_YEARS_DIGITS:
            total_digits = periods * (periods + 1) / 2
            amounts = []
            for i in range(periods):
                year_factor = (periods - i) / total_digits
                amounts.append(round(amortizable * year_factor, 2))
            diff = round(amortizable - sum(amounts), 2)
            if abs(diff) > 0.001:
                amounts[-1] = round(amounts[-1] + diff, 2)
            return amounts
        elif method in (AmortizationMethod.CUSTOM, AmortizationMethod.MANUAL):
            if not custom:
                raise AmortizationCalculationError("Custom schedule required for CUSTOM method")
            amounts = []
            for i in range(periods):
                amounts.append(round(custom.get(i + 1, 0.0), 2))
            return amounts
        raise AmortizationCalculationError(f"Unknown amortization method: {method}")

    def get_schedule(self, schedule_id: str) -> AmortizationSchedule:
        schedule = self._schedules.get(schedule_id)
        if not schedule or schedule.is_deleted:
            raise AmortizationScheduleError(f"Schedule {schedule_id} not found")
        return schedule

    def list_schedules(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        is_completed: Optional[bool] = None,
    ) -> List[AmortizationSchedule]:
        results = [s for s in self._schedules.values() if not s.is_deleted]
        if entity_type:
            results = [s for s in results if s.entity_type == entity_type]
        if entity_id:
            results = [s for s in results if s.entity_id == entity_id]
        if is_completed is not None:
            results = [s for s in results if s.is_completed == is_completed]
        return results

    def activate_schedule(self, schedule_id: str) -> AmortizationSchedule:
        schedule = self.get_schedule(schedule_id)
        sm = AmortizationStateMachine(schedule)
        sm.transition(AmortizationStatus.ACTIVE)
        schedule.touch()
        return schedule

    def complete_schedule(self, schedule_id: str) -> AmortizationSchedule:
        schedule = self.get_schedule(schedule_id)
        sm = AmortizationStateMachine(schedule)
        sm.transition(AmortizationStatus.COMPLETED)
        schedule.is_completed = True
        schedule.completed_at = datetime.now()
        schedule.touch()
        return schedule

    def suspend_schedule(self, schedule_id: str) -> AmortizationSchedule:
        schedule = self.get_schedule(schedule_id)
        sm = AmortizationStateMachine(schedule)
        sm.transition(AmortizationStatus.SUSPENDED)
        schedule.touch()
        return schedule

    def cancel_schedule(self, schedule_id: str) -> AmortizationSchedule:
        schedule = self.get_schedule(schedule_id)
        sm = AmortizationStateMachine(schedule)
        sm.transition(AmortizationStatus.CANCELLED)
        schedule.touch()
        return schedule

    def mark_entry_paid(
        self,
        schedule_id: str,
        period_number: int,
        actual_amount: Optional[float] = None,
        payment_reference: Optional[str] = None,
    ) -> AmortizationSchedule:
        schedule = self.get_schedule(schedule_id)
        for entry in schedule.entries:
            if entry.period_number == period_number:
                entry.is_paid = True
                entry.paid_at = datetime.now()
                entry.payment_reference = payment_reference
                if actual_amount is not None:
                    entry.actual_amount = actual_amount
                    schedule.amortized_amount = round(schedule.amortized_amount + actual_amount, 2)
                else:
                    schedule.amortized_amount = round(schedule.amortized_amount + entry.scheduled_amount, 2)
                schedule.remaining_amount = round(schedule.total_amount - schedule.amortized_amount, 2)
                if schedule.remaining_amount < 0.001:
                    schedule.remaining_amount = 0.0
                    schedule.is_completed = True
                    schedule.completed_at = datetime.now()
                schedule.touch()
                return schedule
        raise NotFoundError(f"Entry period {period_number} not found in schedule {schedule_id}")

    def get_forecast(
        self,
        schedule_id: str,
        forecast_periods: int = 12,
    ) -> List[Dict[str, Any]]:
        schedule = self.get_schedule(schedule_id)
        forecast: List[Dict[str, Any]] = []
        for entry in schedule.entries:
            forecast.append({
                "period_number": entry.period_number,
                "period_start": entry.period_start.isoformat(),
                "period_end": entry.period_end.isoformat(),
                "scheduled_amount": entry.scheduled_amount,
                "remaining": entry.remaining,
                "is_paid": entry.is_paid,
                "is_overdue": entry.is_overdue,
            })
        return forecast

    def get_schedule_summary(self, schedule_id: str) -> Dict[str, Any]:
        schedule = self.get_schedule(schedule_id)
        return {
            "id": schedule.id,
            "entity_type": schedule.entity_type,
            "entity_id": schedule.entity_id,
            "total_amount": schedule.total_amount,
            "amortized_amount": schedule.amortized_amount,
            "remaining_amount": schedule.remaining_amount,
            "progress_pct": schedule.progress_pct,
            "method": schedule.rule.method.value,
            "total_periods": schedule.rule.total_periods,
            "paid_entries": len(schedule.paid_entries),
            "overdue_entries": len(schedule.overdue_entries),
            "upcoming_entries": len(schedule.upcoming_entries),
            "is_completed": schedule.is_completed,
        }

    def list_schedules_by_entity(self, entity_type: str, entity_id: str) -> List[AmortizationSchedule]:
        return self.list_schedules(entity_type=entity_type, entity_id=entity_id)
