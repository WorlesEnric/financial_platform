from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from finance_platform.amortization.exceptions import (
    AmortizationEntryNotFoundError,
    AmortizationNotFoundError,
    AmortizationRuleNotFoundError,
)
from finance_platform.amortization.models import (
    AmortizationAdjustment,
    AmortizationEntry,
    AmortizationEntryStatus,
    AmortizationForecast,
    AmortizationRecord,
    AmortizationRule,
    AmortizationStatus,
    AmortizationSummary,
)


class AmortizationRepository:
    def __init__(self) -> None:
        self._records: Dict[str, AmortizationRecord] = {}
        self._entries: Dict[str, AmortizationEntry] = {}
        self._rules: Dict[str, AmortizationRule] = {}
        self._adjustments: Dict[str, AmortizationAdjustment] = {}
        self._forecasts: Dict[str, AmortizationForecast] = {}

    def save_record(self, record: AmortizationRecord) -> AmortizationRecord:
        self._records[record.id] = record
        return record

    def get_record(self, record_id: str) -> AmortizationRecord:
        record = self._records.get(record_id)
        if record is None:
            raise AmortizationNotFoundError(record_id=record_id)
        return record

    def get_records_by_company(self, company_id: str) -> List[AmortizationRecord]:
        return [r for r in self._records.values() if r.company_id == company_id]

    def get_records_by_entity(self, entity_type: str, entity_id: str) -> List[AmortizationRecord]:
        return [
            r
            for r in self._records.values()
            if r.entity_type == entity_type and r.entity_id == entity_id
        ]

    def get_records_by_status(self, status: AmortizationStatus) -> List[AmortizationRecord]:
        return [r for r in self._records.values() if r.status == status]

    def update_record(self, record: AmortizationRecord) -> AmortizationRecord:
        self._records[record.id] = record
        return record

    def delete_record(self, record_id: str) -> bool:
        return self._records.pop(record_id, None) is not None

    def save_entry(self, entry: AmortizationEntry) -> AmortizationEntry:
        self._entries[entry.id] = entry
        return entry

    def save_entries(self, entries: List[AmortizationEntry]) -> List[AmortizationEntry]:
        for entry in entries:
            self._entries[entry.id] = entry
        return entries

    def get_entry(self, entry_id: str) -> AmortizationEntry:
        entry = self._entries.get(entry_id)
        if entry is None:
            raise AmortizationEntryNotFoundError(entry_id=entry_id)
        return entry

    def get_entries_by_record(self, record_id: str) -> List[AmortizationEntry]:
        return [e for e in self._entries.values() if e.record_id == record_id]

    def get_overdue_entries(self, company_id: str) -> List[AmortizationEntry]:
        today = date.today()
        records = self.get_records_by_company(company_id)
        record_ids = {r.id for r in records}
        return [
            e
            for e in self._entries.values()
            if e.record_id in record_ids
            and not e.is_paid
            and e.period_end < today
            and e.status not in (AmortizationEntryStatus.WAIVED, AmortizationEntryStatus.DEFERRED)
        ]

    def update_entry(self, entry: AmortizationEntry) -> AmortizationEntry:
        self._entries[entry.id] = entry
        return entry

    def save_rule(self, rule: AmortizationRule) -> AmortizationRule:
        self._rules[rule.id] = rule
        return rule

    def get_rule(self, rule_id: str) -> AmortizationRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise AmortizationRuleNotFoundError(rule_id=rule_id)
        return rule

    def get_rules_by_company(self, company_id: str) -> List[AmortizationRule]:
        return [r for r in self._rules.values() if r.company_id == company_id]

    def save_adjustment(self, adjustment: AmortizationAdjustment) -> AmortizationAdjustment:
        self._adjustments[adjustment.id] = adjustment
        return adjustment

    def get_adjustments_by_record(self, record_id: str) -> List[AmortizationAdjustment]:
        return [a for a in self._adjustments.values() if a.record_id == record_id]

    def save_forecast(self, forecast: AmortizationForecast) -> AmortizationForecast:
        self._forecasts[forecast.id] = forecast
        return forecast

    def get_forecasts_by_record(self, record_id: str) -> List[AmortizationForecast]:
        return [f for f in self._forecasts.values() if f.record_id == record_id]

    def get_summary(self, company_id: str, fiscal_year: str) -> AmortizationSummary:
        records = [r for r in self._records.values() if r.company_id == company_id]
        active = [r for r in records if r.status == AmortizationStatus.ACTIVE]
        completed = [r for r in records if r.status == AmortizationStatus.COMPLETED]
        overdue_entries = self.get_overdue_entries(company_id)

        summary = AmortizationSummary(
            company_id=company_id,
            fiscal_year=fiscal_year,
            total_active_records=len(active),
            total_completed_records=len(completed),
            total_amount_minor=sum(r.total_amount_minor for r in records),
            total_amortized_minor=sum(r.amortized_amount_minor for r in records),
            total_remaining_minor=sum(r.remaining_amount_minor for r in records),
            total_overdue_entries=len(overdue_entries),
            total_overdue_amount_minor=sum(e.scheduled_amount_minor for e in overdue_entries),
        )
        for r in records:
            method = r.method.value if hasattr(r.method, "value") else str(r.method)
            dept = r.department or "unknown"
            summary.records_by_method[method] = summary.records_by_method.get(method, 0) + 1
            summary.records_by_department[dept] = summary.records_by_department.get(dept, 0) + 1
        return summary
