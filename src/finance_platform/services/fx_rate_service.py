from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from finance_platform.errors.exceptions import NotFoundError, FxRateNotFoundError, FxConversionError
from finance_platform.models.base import CurrencyCode
from finance_platform.models.fx_rate import FxRate, FxRateSnapshot


class FxRateService:
    def __init__(self) -> None:
        self._rates: Dict[str, FxRate] = {}
        self._snapshots: Dict[str, FxRateSnapshot] = {}

    def _rate_key(self, from_currency: CurrencyCode, to_currency: CurrencyCode, rate_date: date) -> str:
        return f"{from_currency.value}_{to_currency.value}_{rate_date.isoformat()}"

    def set_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate: float,
        rate_date: Optional[date] = None,
        source: str = "manual",
        bid: Optional[float] = None,
        ask: Optional[float] = None,
    ) -> FxRate:
        rate_date = rate_date or date.today()
        inverse = round(1.0 / rate, 6) if rate != 0 else None
        fx_rate = FxRate(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            inverse_rate=inverse,
            date=rate_date,
            source=source,
            bid=bid,
            ask=ask,
            mid=round((bid + ask) / 2, 6) if bid is not None and ask is not None else None,
        )
        key = self._rate_key(from_currency, to_currency, rate_date)
        self._rates[key] = fx_rate
        return fx_rate

    def get_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate_date: Optional[date] = None,
    ) -> FxRate:
        rate_date = rate_date or date.today()
        if from_currency == to_currency:
            return FxRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=1.0,
                inverse_rate=1.0,
                date=rate_date,
                source="identity",
            )
        key = self._rate_key(from_currency, to_currency, rate_date)
        rate = self._rates.get(key)
        if rate is None:
            inverted_key = self._rate_key(to_currency, from_currency, rate_date)
            inverted = self._rates.get(inverted_key)
            if inverted:
                return FxRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=round(1.0 / inverted.rate, 6),
                    inverse_rate=inverted.rate,
                    date=rate_date,
                    source=inverted.source,
                )
            raise FxRateNotFoundError(
                f"FX rate not found for {from_currency.value}->{to_currency.value} on {rate_date}"
            )
        return rate

    def convert(
        self,
        amount: float,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate_date: Optional[date] = None,
    ) -> float:
        rate = self.get_rate(from_currency, to_currency, rate_date)
        return round(rate.convert(amount), 2)

    def list_rates(
        self,
        from_currency: Optional[CurrencyCode] = None,
        to_currency: Optional[CurrencyCode] = None,
        rate_date: Optional[date] = None,
    ) -> List[FxRate]:
        results = list(self._rates.values())
        if from_currency:
            results = [r for r in results if r.from_currency == from_currency]
        if to_currency:
            results = [r for r in results if r.to_currency == to_currency]
        if rate_date:
            results = [r for r in results if r.date == rate_date]
        return results

    def create_snapshot(
        self,
        base_currency: CurrencyCode,
        snapshot_date: Optional[date] = None,
        source: str = "manual",
    ) -> FxRateSnapshot:
        snapshot_date = snapshot_date or date.today()
        rates: Dict[str, float] = {}
        for code in CurrencyCode:
            if code == base_currency:
                continue
            try:
                rate = self.get_rate(base_currency, code, snapshot_date)
                rates[code.value] = rate.rate
            except FxRateNotFoundError:
                continue
        snapshot = FxRateSnapshot(
            base_currency=base_currency,
            snapshot_date=snapshot_date,
            source=source,
            rates=rates,
        )
        self._snapshots[snapshot.id] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> FxRateSnapshot:
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            raise NotFoundError(f"FxRateSnapshot {snapshot_id} not found", resource_type="FxRateSnapshot", resource_id=snapshot_id)
        return snapshot

    def list_snapshots(self, base_currency: Optional[CurrencyCode] = None) -> List[FxRateSnapshot]:
        results = list(self._snapshots.values())
        if base_currency:
            results = [s for s in results if s.base_currency == base_currency]
        results.sort(key=lambda s: s.created_at, reverse=True)
        return results

    def delete_rate(self, from_currency: CurrencyCode, to_currency: CurrencyCode, rate_date: Optional[date] = None) -> None:
        rate_date = rate_date or date.today()
        key = self._rate_key(from_currency, to_currency, rate_date)
        if key in self._rates:
            del self._rates[key]
