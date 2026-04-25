from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.errors.exceptions import (
    NotFoundError,
    BusinessRuleError,
    CarryForwardError,
    CarryForwardPeriodError,
)
from finance_platform.models.base import CurrencyCode, TimestampMixin


class CarryForwardBucket(TimestampMixin):
    source_year: int
    target_year: int
    source_entity_type: str
    source_entity_id: str
    total_amount: float = 0.0
    used_amount: float = 0.0
    expired_amount: float = 0.0
    currency: CurrencyCode = CurrencyCode.USD
    max_carry_pct: float = 100.0
    expiry_date: Optional[date] = None
    description: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

    @property
    def remaining_amount(self) -> float:
        return round(self.total_amount - self.used_amount - self.expired_amount, 2)

    @property
    def is_exhausted(self) -> bool:
        return self.remaining_amount <= 0.0

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return self.expiry_date < date.today()

    @property
    def usage_pct(self) -> float:
        if self.total_amount == 0:
            return 0.0
        return round((self.used_amount / self.total_amount) * 100, 2)


class CarryForwardEntry(TimestampMixin):
    bucket_id: str
    source_entity_type: str
    source_entity_id: str
    original_amount: float = 0.0
    carried_amount: float = 0.0
    adjustment_reason: Optional[str] = None
    applied_to_entity_type: Optional[str] = None
    applied_to_entity_id: Optional[str] = None
    applied_date: Optional[date] = None
    is_expired: bool = False
    expired_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

    @property
    def is_applied(self) -> bool:
        return self.applied_to_entity_id is not None


class CarryForwardService:
    def __init__(self) -> None:
        self._buckets: Dict[str, CarryForwardBucket] = {}
        self._entries: Dict[str, CarryForwardEntry] = {}

    def create_bucket(
        self,
        source_year: int,
        target_year: int,
        source_entity_type: str,
        source_entity_id: str,
        total_amount: float,
        currency: CurrencyCode = CurrencyCode.USD,
        max_carry_pct: float = 100.0,
        expiry_date: Optional[date] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CarryForwardBucket:
        if target_year <= source_year:
            raise CarryForwardPeriodError("Target year must be after source year")
        if total_amount < 0:
            raise CarryForwardError("Total amount cannot be negative")
        bucket = CarryForwardBucket(
            source_year=source_year,
            target_year=target_year,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            total_amount=total_amount,
            currency=currency,
            max_carry_pct=max_carry_pct,
            expiry_date=expiry_date,
            description=description,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._buckets[bucket.id] = bucket
        return bucket

    def get_bucket(self, bucket_id: str) -> CarryForwardBucket:
        bucket = self._buckets.get(bucket_id)
        if not bucket:
            raise NotFoundError(f"CarryForwardBucket {bucket_id} not found", resource_type="CarryForwardBucket", resource_id=bucket_id)
        return bucket

    def list_buckets(
        self,
        source_year: Optional[int] = None,
        target_year: Optional[int] = None,
        source_entity_type: Optional[str] = None,
        source_entity_id: Optional[str] = None,
    ) -> List[CarryForwardBucket]:
        results = list(self._buckets.values())
        if source_year is not None:
            results = [b for b in results if b.source_year == source_year]
        if target_year is not None:
            results = [b for b in results if b.target_year == target_year]
        if source_entity_type:
            results = [b for b in results if b.source_entity_type == source_entity_type]
        if source_entity_id:
            results = [b for b in results if b.source_entity_id == source_entity_id]
        return results

    def create_entry(
        self,
        bucket_id: str,
        source_entity_type: str,
        source_entity_id: str,
        original_amount: float,
        carried_amount: float,
        adjustment_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CarryForwardEntry:
        bucket = self.get_bucket(bucket_id)
        max_carry = round(bucket.total_amount * bucket.max_carry_pct / 100.0, 2)
        if carried_amount > max_carry:
            raise CarryForwardError(
                f"Carried amount {carried_amount} exceeds maximum {max_carry} ({bucket.max_carry_pct}%)"
            )
        entry = CarryForwardEntry(
            bucket_id=bucket_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            original_amount=original_amount,
            carried_amount=carried_amount,
            adjustment_reason=adjustment_reason,
            metadata=metadata or {},
        )
        self._entries[entry.id] = entry
        return entry

    def get_entry(self, entry_id: str) -> CarryForwardEntry:
        entry = self._entries.get(entry_id)
        if not entry:
            raise NotFoundError(f"CarryForwardEntry {entry_id} not found", resource_type="CarryForwardEntry", resource_id=entry_id)
        return entry

    def list_entries(
        self,
        bucket_id: Optional[str] = None,
        is_expired: Optional[bool] = None,
        is_applied: Optional[bool] = None,
    ) -> List[CarryForwardEntry]:
        results = list(self._entries.values())
        if bucket_id:
            results = [e for e in results if e.bucket_id == bucket_id]
        if is_expired is not None:
            results = [e for e in results if e.is_expired == is_expired]
        if is_applied is not None:
            results = [e for e in results if e.is_applied == is_applied]
        return results

    def apply_entry(
        self,
        entry_id: str,
        applied_to_entity_type: str,
        applied_to_entity_id: str,
    ) -> CarryForwardEntry:
        entry = self.get_entry(entry_id)
        if entry.is_applied:
            raise CarryForwardError(f"Entry {entry_id} has already been applied")
        bucket = self.get_bucket(entry.bucket_id)
        if bucket.is_expired:
            raise CarryForwardError(f"Bucket {entry.bucket_id} has expired")
        remaining = bucket.remaining_amount
        if entry.carried_amount > remaining:
            raise CarryForwardError(
                f"Entry amount {entry.carried_amount} exceeds bucket remaining {remaining}"
            )
        entry.applied_to_entity_type = applied_to_entity_type
        entry.applied_to_entity_id = applied_to_entity_id
        entry.applied_date = date.today()
        bucket.used_amount = round(bucket.used_amount + entry.carried_amount, 2)
        bucket.touch()
        entry.touch()
        return entry

    def expire_entry(self, entry_id: str) -> CarryForwardEntry:
        entry = self.get_entry(entry_id)
        if entry.is_expired:
            raise CarryForwardError(f"Entry {entry_id} is already expired")
        bucket = self.get_bucket(entry.bucket_id)
        entry.is_expired = True
        entry.expired_at = datetime.now(timezone.utc)
        bucket.expired_amount = round(bucket.expired_amount + entry.carried_amount, 2)
        bucket.touch()
        entry.touch()
        return entry

    def expire_bucket_entries(self, bucket_id: str) -> List[CarryForwardEntry]:
        bucket = self.get_bucket(bucket_id)
        expired: List[CarryForwardEntry] = []
        for entry in self.list_entries(bucket_id=bucket_id, is_expired=False, is_applied=False):
            entry.is_expired = True
            entry.expired_at = datetime.now(timezone.utc)
            bucket.expired_amount = round(bucket.expired_amount + entry.carried_amount, 2)
            entry.touch()
            expired.append(entry)
        bucket.touch()
        return expired

    def get_bucket_summary(self, bucket_id: str) -> Dict[str, Any]:
        bucket = self.get_bucket(bucket_id)
        entries = self.list_entries(bucket_id=bucket_id)
        return {
            "bucket_id": bucket.id,
            "source_year": bucket.source_year,
            "target_year": bucket.target_year,
            "source_entity_type": bucket.source_entity_type,
            "source_entity_id": bucket.source_entity_id,
            "total_amount": bucket.total_amount,
            "used_amount": bucket.used_amount,
            "expired_amount": bucket.expired_amount,
            "remaining_amount": bucket.remaining_amount,
            "usage_pct": bucket.usage_pct,
            "is_exhausted": bucket.is_exhausted,
            "is_expired": bucket.is_expired,
            "total_entries": len(entries),
            "applied_entries": sum(1 for e in entries if e.is_applied),
            "expired_entries": sum(1 for e in entries if e.is_expired),
        }

    def compute_carry_forward(
        self,
        source_year: int,
        target_year: int,
        source_entity_type: str,
        source_entity_id: str,
        current_balance: float,
        max_carry_pct: float = 100.0,
        expiry_date: Optional[date] = None,
    ) -> CarryForwardBucket:
        carry_amount = round(current_balance * max_carry_pct / 100.0, 2)
        bucket = self.create_bucket(
            source_year=source_year,
            target_year=target_year,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            total_amount=carry_amount,
            max_carry_pct=max_carry_pct,
            expiry_date=expiry_date,
            description=f"Auto carry-forward from {source_year} to {target_year}",
        )
        self.create_entry(
            bucket_id=bucket.id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            original_amount=current_balance,
            carried_amount=carry_amount,
            adjustment_reason="Auto-computed carry forward",
        )
        return bucket
