from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.amortization.calculator import AmortizationCalculator
from finance_platform.amortization.domain_events import (
    AmortizationAdjustedEvent,
    AmortizationCompletedEvent,
    AmortizationCreatedEvent,
    AmortizationEntryPaidEvent,
    AmortizationForecastGeneratedEvent,
    AmortizationUpdatedEvent,
)
from finance_platform.amortization.exceptions import (
    AmortizationAlreadyCompletedError,
    AmortizationCalculationError,
    AmortizationDuplicateError,
    AmortizationNotFoundError,
    AmortizationStateError,
    AmortizationValidationError,
)
from finance_platform.amortization.models import (
    AmortizationAdjustment,
    AmortizationEntry,
    AmortizationEntryStatus,
    AmortizationForecast,
    AmortizationRecord,
    AmortizationRule,
    AmortizationStatus,
)
from finance_platform.amortization.repository import AmortizationRepository
from finance_platform.amortization.schemas import (
    AmortizationBulkCreateRequest,
    AmortizationBulkCreateResponse,
    AmortizationEntryDeferRequest,
    AmortizationEntryPaymentRequest,
    AmortizationEntryResponse,
    AmortizationEntryWaiveRequest,
    AmortizationForecastResponse,
    AmortizationListResponse,
    AmortizationRecordCreate,
    AmortizationRecordResponse,
    AmortizationRecordUpdate,
    AmortizationSummaryResponse,
)
from finance_platform.amortization.state_machine import AmortizationStateMachine


class AmortizationService:
    def __init__(
        self,
        repository: Optional[AmortizationRepository] = None,
        calculator: Optional[AmortizationCalculator] = None,
        state_machine: Optional[AmortizationStateMachine] = None,
    ) -> None:
        self._repository = repository or AmortizationRepository()
        self._calculator = calculator or AmortizationCalculator()
        self._state_machine = state_machine or AmortizationStateMachine()

    def create_record(self, data: AmortizationRecordCreate) -> AmortizationRecordResponse:
        existing = self._repository.get_records_by_entity(data.entity_type, data.entity_id)
        if existing:
            raise AmortizationDuplicateError(entity_type=data.entity_type, entity_id=data.entity_id)
        entries = self._calculator.calculate_schedule(
            total_amount_minor=data.total_amount_minor,
            method=data.method,
            frequency=data.frequency,
            total_periods=data.total_periods,
            start_date=data.start_date,
            residual_amount_minor=data.residual_amount_minor or 0,
            acceleration_factor=data.acceleration_factor,
            interest_rate=data.interest_rate,
            deferral_days=data.deferral_days or 0,
        )
        record = AmortizationRecord(
            company_id=data.company_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            description=data.description,
            total_amount_minor=data.total_amount_minor,
            remaining_amount_minor=data.total_amount_minor,
            currency=data.currency,
            method=data.method,
            frequency=data.frequency,
            total_periods=data.total_periods,
            start_date=data.start_date,
            end_date=data.end_date,
            residual_amount_minor=data.residual_amount_minor or 0,
            acceleration_factor=data.acceleration_factor,
            interest_rate=data.interest_rate,
            deferral_days=data.deferral_days or 0,
            cost_center=data.cost_center,
            department=data.department,
            project_code=data.project_code,
            budget_code=data.budget_code,
            fiscal_year=data.fiscal_year,
            tags=data.tags,
            metadata=data.metadata,
        )
        saved = self._repository.save_record(record)
        for entry in entries:
            entry.record_id = saved.id
        self._repository.save_entries(entries)
        return self._to_response(saved, entries)

    def get_record(self, record_id: str) -> AmortizationRecordResponse:
        record = self._repository.get_record(record_id)
        entries = self._repository.get_entries_by_record(record_id)
        return self._to_response(record, entries)

    def update_record(self, record_id: str, data: AmortizationRecordUpdate) -> AmortizationRecordResponse:
        record = self._repository.get_record(record_id)
        if record.status == AmortizationStatus.COMPLETED:
            raise AmortizationAlreadyCompletedError(record_id=record_id)
        changes: Dict[str, Any] = {}
        for field in data.model_fields_set:
            if field == "id":
                continue
            val = getattr(data, field, None)
            if val is not None:
                setattr(record, field, val)
                changes[field] = val
        record.touch()
        self._repository.update_record(record)
        return self._to_response(record, self._repository.get_entries_by_record(record_id))

    def delete_record(self, record_id: str) -> bool:
        record = self._repository.get_record(record_id)
        if record.status == AmortizationStatus.ACTIVE:
            raise AmortizationStateError(
                "Cannot delete an active amortization record",
                current_status=record.status.value,
                target_status="deleted",
            )
        return self._repository.delete_record(record_id)

    def update_status(self, record_id: str, new_status: AmortizationStatus, reason: Optional[str] = None) -> AmortizationRecordResponse:
        record = self._repository.get_record(record_id)
        old_status = record.status
        if not self._state_machine.can_transition(old_status, new_status):
            raise AmortizationStateError(
                current_status=old_status.value,
                target_status=new_status.value,
            )
        record.status = new_status
        if new_status == AmortizationStatus.COMPLETED:
            record.completed_at = datetime.now(timezone.utc)
        elif new_status == AmortizationStatus.CANCELLED:
            record.cancelled_at = datetime.now(timezone.utc)
            record.cancellation_reason = reason
        elif new_status == AmortizationStatus.ACTIVE:
            record.approved_at = datetime.now(timezone.utc)
        record.touch()
        self._repository.update_record(record)
        return self._to_response(record, self._repository.get_entries_by_record(record_id))

    def pay_entry(self, entry_id: str, data: AmortizationEntryPaymentRequest) -> AmortizationEntryResponse:
        entry = self._repository.get_entry(entry_id)
        record = self._repository.get_record(entry.record_id)
        entry.actual_amount_minor = data.actual_amount_minor
        entry.status = AmortizationEntryStatus.PAID
        entry.is_paid = True
        entry.paid_at = datetime.now(timezone.utc)
        entry.paid_by = data.paid_by
        entry.payment_reference = data.payment_reference
        entry.invoice_reference = data.invoice_reference
        entry.notes = data.notes
        self._repository.update_entry(entry)
        record.amortized_amount_minor += data.actual_amount_minor
        record.remaining_amount_minor = max(0, record.total_amount_minor - record.amortized_amount_minor)
        record.completed_periods += 1
        self._repository.update_record(record)
        return self._entry_to_response(entry)

    def defer_entry(self, entry_id: str, data: AmortizationEntryDeferRequest) -> AmortizationEntryResponse:
        entry = self._repository.get_entry(entry_id)
        entry.status = AmortizationEntryStatus.DEFERRED
        entry.deferral_date = data.deferral_date
        entry.notes = data.reason
        self._repository.update_entry(entry)
        return self._entry_to_response(entry)

    def waive_entry(self, entry_id: str, data: AmortizationEntryWaiveRequest) -> AmortizationEntryResponse:
        entry = self._repository.get_entry(entry_id)
        entry.status = AmortizationEntryStatus.WAIVED
        entry.waiver_reason = data.reason
        self._repository.update_entry(entry)
        return self._entry_to_response(entry)

    def list_records(self, company_id: str, page: int = 1, page_size: int = 20) -> AmortizationListResponse:
        records = self._repository.get_records_by_company(company_id)
        total = len(records)
        start = (page - 1) * page_size
        end = start + page_size
        page_records = records[start:end]
        items = [self._to_response(r, self._repository.get_entries_by_record(r.id)) for r in page_records]
        return AmortizationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, (total + page_size - 1) // page_size),
        )

    def bulk_create(self, data: AmortizationBulkCreateRequest) -> AmortizationBulkCreateResponse:
        created: list[AmortizationRecordResponse] = []
        failed: list[Dict[str, Any]] = []
        for item in data.items:
            try:
                resp = self.create_record(item)
                created.append(resp)
            except Exception as e:
                failed.append({"entity_id": item.entity_id, "error": str(e)})
        return AmortizationBulkCreateResponse(
            created=created,
            failed=failed,
            total_requested=len(data.items),
            total_created=len(created),
            total_failed=len(failed),
        )

    def get_entries(self, record_id: str) -> list[AmortizationEntryResponse]:
        entries = self._repository.get_entries_by_record(record_id)
        return [self._entry_to_response(e) for e in entries]

    def get_summary(self, company_id: str, fiscal_year: str) -> AmortizationSummaryResponse:
        summary = self._repository.get_summary(company_id, fiscal_year)
        return AmortizationSummaryResponse(
            company_id=summary.company_id,
            fiscal_year=summary.fiscal_year,
            total_active_records=summary.total_active_records,
            total_completed_records=summary.total_completed_records,
            total_amount_minor=summary.total_amount_minor,
            total_amortized_minor=summary.total_amortized_minor,
            total_remaining_minor=summary.total_remaining_minor,
            total_amount=str(summary.total_amount),
            total_amortized=str(summary.total_amortized),
            total_remaining=str(summary.total_remaining),
            total_overdue_entries=summary.total_overdue_entries,
            total_overdue_amount_minor=summary.total_overdue_amount_minor,
            total_overdue_amount=str(summary.total_overdue_amount),
            overall_progress_pct=summary.overall_progress_pct,
            records_by_method=summary.records_by_method,
            records_by_department=summary.records_by_department,
            generated_at=summary.generated_at,
        )

    def generate_forecast(self, record_id: str) -> AmortizationForecastResponse:
        record = self._repository.get_record(record_id)
        if record.total_periods == 0:
            raise AmortizationCalculationError("Cannot forecast a record with zero periods")
        entries = self._repository.get_entries_by_record(record_id)
        paid_entries = [e for e in entries if e.status == AmortizationEntryStatus.PAID]
        remaining_entries = [e for e in entries if e.status in (AmortizationEntryStatus.SCHEDULED, AmortizationEntryStatus.DUE)]
        projected_remaining = sum(e.scheduled_amount_minor for e in remaining_entries)
        remaining_periods = len(remaining_entries)
        if paid_entries:
            last_paid = max(e.paid_at or datetime.min for e in paid_entries)
        else:
            last_paid = datetime.min
        forecast = AmortizationForecast(
            record_id=record_id,
            forecast_date=date.today(),
            projected_end_date=record.expected_completion_date or date.today(),
            projected_total_amount_minor=record.total_amount_minor,
            projected_remaining_amount_minor=projected_remaining,
            projected_periods_remaining=remaining_periods,
            projected_period_amount_minor=record.period_amount_minor if remaining_periods > 0 else 0,
            confidence_score=0.8 if remaining_periods > 0 else 1.0,
        )
        self._repository.save_forecast(forecast)
        return AmortizationForecastResponse(
            record_id=forecast.record_id,
            forecast_date=forecast.forecast_date,
            projected_end_date=forecast.projected_end_date,
            projected_total_amount_minor=forecast.projected_total_amount_minor,
            projected_remaining_amount_minor=forecast.projected_remaining_amount_minor,
            projected_periods_remaining=forecast.projected_periods_remaining,
            projected_period_amount_minor=forecast.projected_period_amount_minor,
            projected_total_amount=str(forecast.projected_total_amount),
            projected_remaining_amount=str(forecast.projected_remaining_amount),
            projected_period_amount=str(forecast.projected_period_amount),
            confidence_score=forecast.confidence_score,
            assumptions=forecast.assumptions,
            scenarios=forecast.scenarios,
        )

    def _to_response(self, record: AmortizationRecord, entries: list[AmortizationEntry]) -> AmortizationRecordResponse:
        return AmortizationRecordResponse(
            id=record.id,
            company_id=record.company_id,
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            description=record.description,
            total_amount_minor=record.total_amount_minor,
            amortized_amount_minor=record.amortized_amount_minor,
            remaining_amount_minor=record.remaining_amount_minor,
            total_amount=str(record.total_amount),
            amortized_amount=str(record.amortized_amount),
            remaining_amount=str(record.remaining_amount),
            currency=record.currency,
            status=record.status,
            method=record.method,
            frequency=record.frequency,
            total_periods=record.total_periods,
            completed_periods=record.completed_periods,
            start_date=record.start_date,
            end_date=record.end_date,
            residual_amount_minor=record.residual_amount_minor,
            period_amount_minor=record.period_amount_minor,
            period_amount=str(record.period_amount),
            progress_pct=record.progress_pct,
            acceleration_factor=record.acceleration_factor,
            interest_rate=record.interest_rate,
            is_active=record.is_active,
            is_completed=record.is_completed,
            deferral_days=record.deferral_days,
            cost_center=record.cost_center,
            department=record.department,
            project_code=record.project_code,
            budget_code=record.budget_code,
            fiscal_year=record.fiscal_year,
            approved_by=record.approved_by,
            approved_at=record.approved_at,
            cancelled_by=record.cancelled_by,
            cancelled_at=record.cancelled_at,
            cancellation_reason=record.cancellation_reason,
            completed_at=record.completed_at,
            expected_completion_date=record.expected_completion_date,
            entries=[self._entry_to_response(e) for e in entries],
            tags=record.tags,
            created_at=record.created_at,
            updated_at=record.updated_at,
            metadata=record.metadata,
        )

    def _entry_to_response(self, entry: AmortizationEntry) -> AmortizationEntryResponse:
        return AmortizationEntryResponse(
            id=entry.id,
            record_id=entry.record_id,
            period_number=entry.period_number,
            period_start=entry.period_start,
            period_end=entry.period_end,
            scheduled_amount_minor=entry.scheduled_amount_minor,
            actual_amount_minor=entry.actual_amount_minor,
            scheduled_amount=str(entry.scheduled_amount),
            actual_amount=str(entry.actual_amount) if entry.actual_amount is not None else None,
            status=entry.status,
            is_paid=entry.is_paid,
            paid_at=entry.paid_at,
            paid_by=entry.paid_by,
            payment_reference=entry.payment_reference,
            is_overdue=entry.is_overdue,
            is_due=entry.is_due,
            remaining=str(entry.remaining),
            notes=entry.notes,
            metadata=entry.metadata,
        )
