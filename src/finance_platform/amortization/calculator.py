from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.amortization.exceptions import AmortizationCalculationError
from finance_platform.amortization.models import (
    AmortizationEntry,
    AmortizationEntryStatus,
    AmortizationFrequency,
    AmortizationMethod,
    AmortizationRecord,
    AmortizationStatus,
)


class AmortizationCalculator:
    def calculate_schedule(
        self,
        total_amount_minor: int,
        method: AmortizationMethod,
        frequency: AmortizationFrequency,
        total_periods: int,
        start_date: date,
        residual_amount_minor: int = 0,
        acceleration_factor: Optional[float] = None,
        interest_rate: Optional[float] = None,
        deferral_days: int = 0,
    ) -> list[AmortizationEntry]:
        if total_periods < 1:
            raise AmortizationCalculationError("total_periods must be >= 1")
        if total_amount_minor <= 0:
            raise AmortizationCalculationError("total_amount_minor must be > 0")
        if residual_amount_minor >= total_amount_minor:
            raise AmortizationCalculationError(
                "residual_amount_minor must be less than total_amount_minor"
            )

        amortizable = total_amount_minor - residual_amount_minor

        if method == AmortizationMethod.STRAIGHT_LINE:
            amounts = self._straight_line(amortizable, total_periods)
        elif method == AmortizationMethod.DECLINING_BALANCE:
            factor = acceleration_factor or 2.0
            amounts = self._declining_balance(amortizable, total_periods, factor)
        elif method == AmortizationMethod.SUM_OF_YEARS_DIGITS:
            amounts = self._sum_of_years_digits(amortizable, total_periods)
        elif method == AmortizationMethod.DOUBLE_DECLINING:
            amounts = self._double_declining(amortizable, total_periods)
        else:
            amounts = self._straight_line(amortizable, total_periods)

        self._reconcile(amounts, amortizable)

        entries: list[AmortizationEntry] = []
        period_start = start_date
        for i, amount in enumerate(amounts):
            period_end = self._period_end(period_start, frequency)
            entry = AmortizationEntry(
                record_id="",
                period_number=i + 1,
                period_start=period_start,
                period_end=period_end,
                scheduled_amount_minor=amount,
                status=AmortizationEntryStatus.SCHEDULED,
            )
            entries.append(entry)
            period_start = period_end + timedelta(days=1)

        return entries

    def _straight_line(self, amortizable: int, periods: int) -> list[int]:
        base = amortizable // periods
        remainder = amortizable % periods
        amounts = [base] * periods
        for i in range(remainder):
            amounts[i] += 1
        return amounts

    def _declining_balance(self, amortizable: int, periods: int, factor: float) -> list[int]:
        amounts: list[int] = []
        remaining = float(amortizable)
        rate = factor / periods
        for i in range(periods - 1):
            amount = int(remaining * rate)
            if amount < 1:
                amount = 1
            amounts.append(amount)
            remaining -= amount
        amounts.append(max(1, int(remaining)))
        return amounts

    def _sum_of_years_digits(self, amortizable: int, periods: int) -> list[int]:
        total = periods * (periods + 1) // 2
        amounts: list[int] = []
        remaining = amortizable
        for i in range(periods - 1):
            fraction = (periods - i) / total
            amount = int(amortizable * fraction)
            amounts.append(amount)
            remaining -= amount
        amounts.append(remaining)
        return amounts

    def _double_declining(self, amortizable: int, periods: int) -> list[int]:
        return self._declining_balance(amortizable, periods, 2.0)

    def _reconcile(self, amounts: list[int], target: int) -> None:
        total = sum(amounts)
        diff = target - total
        if diff != 0:
            amounts[-1] += diff

    def _period_end(self, start: date, frequency: AmortizationFrequency) -> date:
        if frequency == AmortizationFrequency.MONTHLY:
            month = start.month + 1
            year = start.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(start.day, 28)
            return date(year, month, day)
        elif frequency == AmortizationFrequency.QUARTERLY:
            return start + timedelta(days=90)
        elif frequency == AmortizationFrequency.SEMI_ANNUALLY:
            return start + timedelta(days=180)
        elif frequency == AmortizationFrequency.ANNUALLY:
            return date(start.year + 1, start.month, min(start.day, 28))
        elif frequency == AmortizationFrequency.WEEKLY:
            return start + timedelta(days=7)
        elif frequency == AmortizationFrequency.BI_WEEKLY:
            return start + timedelta(days=14)
        return start + timedelta(days=30)

    @staticmethod
    def calculate_record_progress(record: AmortizationRecord) -> float:
        if record.total_amount_minor == 0:
            return 100.0
        return round((record.amortized_amount_minor / record.total_amount_minor) * 100, 2)

    @staticmethod
    def estimate_completion(
        amortized_minor: int,
        total_minor: int,
        elapsed_periods: int,
    ) -> int:
        if elapsed_periods == 0 or amortized_minor == 0:
            return 0
        rate = amortized_minor / elapsed_periods
        remaining = total_minor - amortized_minor
        if rate <= 0:
            return 0
        return int(remaining / rate)
