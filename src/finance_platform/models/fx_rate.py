from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Optional

from pydantic import Field

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    CurrencyCode,
)


class FxRateSnapshot(TimestampMixin):
    base_currency: CurrencyCode
    snapshot_date: date
    source: str = "ecb"
    rates: Dict[str, float] = Field(default_factory=dict)


class FxRate(BaseModel):
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    rate: float = Field(..., gt=0)
    inverse_rate: Optional[float] = None
    date: date
    source: str = "ecb"
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid: Optional[float] = None

    def convert(self, amount: float) -> float:
        return amount * self.rate

    def convert_back(self, amount: float) -> float:
        if self.inverse_rate is not None:
            return amount * self.inverse_rate
        if self.rate != 0:
            return amount / self.rate
        return 0.0
