import uuid
from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()


def format_currency(amount_minor: int, currency: str = "USD") -> str:
    sign = "-" if amount_minor < 0 else ""
    abs_minor = abs(amount_minor)
    major = abs_minor // 100
    cents = abs_minor % 100
    return f"{sign}{currency} {major}.{cents:02d}"
