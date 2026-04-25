from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel


class DomainEvent(BaseModel):
    entity_type: str
    entity_id: str
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)


class AmortizationCreatedEvent(BaseModel):
    record_id: str
    company_id: str
    total_amount_minor: int
    method: str
    total_periods: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_domain_event(self) -> DomainEvent:
        return DomainEvent(
            entity_type="amortization_record",
            entity_id=self.record_id,
            event_type="amortization.created",
            data=self.model_dump(),
        )


class AmortizationUpdatedEvent(BaseModel):
    record_id: str
    company_id: str
    changes: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_domain_event(self) -> DomainEvent:
        return DomainEvent(
            entity_type="amortization_record",
            entity_id=self.record_id,
            event_type="amortization.updated",
            data=self.model_dump(),
        )


class AmortizationCompletedEvent(BaseModel):
    record_id: str
    company_id: str
    total_amortized_minor: int
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    def to_domain_event(self) -> DomainEvent:
        return DomainEvent(
            entity_type="amortization_record",
            entity_id=self.record_id,
            event_type="amortization.completed",
            data=self.model_dump(),
        )


class AmortizationEntryPaidEvent(BaseModel):
    entry_id: str
    record_id: str
    company_id: str
    amount_minor: int
    paid_at: datetime = Field(default_factory=datetime.utcnow)

    def to_domain_event(self) -> DomainEvent:
        return DomainEvent(
            entity_type="amortization_entry",
            entity_id=self.entry_id,
            event_type="amortization.entry_paid",
            data=self.model_dump(),
        )


class AmortizationAdjustedEvent(BaseModel):
    record_id: str
    company_id: str
    adjustment_type: str
    previous_amount_minor: int
    new_amount_minor: int
    reason: str
    adjusted_at: datetime = Field(default_factory=datetime.utcnow)

    def to_domain_event(self) -> DomainEvent:
        return DomainEvent(
            entity_type="amortization_record",
            entity_id=self.record_id,
            event_type="amortization.adjusted",
            data=self.model_dump(),
        )


class AmortizationForecastGeneratedEvent(BaseModel):
    record_id: str
    company_id: str
    projected_completion_date: Optional[str] = None
    confidence_score: float = 1.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_domain_event(self) -> DomainEvent:
        return DomainEvent(
            entity_type="amortization_record",
            entity_id=self.record_id,
            event_type="amortization.forecast_generated",
            data=self.model_dump(),
        )
