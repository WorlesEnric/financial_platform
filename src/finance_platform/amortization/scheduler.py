from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from finance_platform.amortization.domain_events import (
    AmortizationCompletedEvent,
    AmortizationEntryPaidEvent,
)
from finance_platform.amortization.models import (
    AmortizationEntry,
    AmortizationEntryStatus,
    AmortizationRecord,
    AmortizationStatus,
)
from finance_platform.amortization.repository import AmortizationRepository


class AmortizationScheduler:
    def __init__(self, repository: AmortizationRepository) -> None:
        self._repository = repository

    def process_due_entries(self, company_id: str) -> list[AmortizationEntry]:
        records = self._repository.get_records_by_company(company_id)
        due_entries: list[AmortizationEntry] = []
        for record in records:
            if record.status != AmortizationStatus.ACTIVE:
                continue
            entries = self._repository.get_entries_by_record(record.id)
            for entry in entries:
                if entry.status == AmortizationEntryStatus.SCHEDULED and entry.period_start <= date.today():
                    entry.status = AmortizationEntryStatus.DUE
                    self._repository.update_entry(entry)
                    due_entries.append(entry)
        return due_entries

    def process_overdue_entries(self, company_id: str) -> list[AmortizationEntry]:
        overdue = self._repository.get_overdue_entries(company_id)
        for entry in overdue:
            if entry.status == AmortizationEntryStatus.DUE:
                entry.status = AmortizationEntryStatus.OVERDUE
                self._repository.update_entry(entry)
        return overdue

    def auto_complete_records(self, company_id: str) -> list[AmortizationRecord]:
        completed: list[AmortizationRecord] = []
        records = self._repository.get_records_by_company(company_id)
        for record in records:
            if record.status not in (AmortizationStatus.ACTIVE,):
                continue
            if record.remaining_amount_minor <= 0:
                record.status = AmortizationStatus.COMPLETED
                record.completed_at = datetime.now(timezone.utc)
                self._repository.update_record(record)
                completed.append(record)
            else:
                entries = self._repository.get_entries_by_record(record.id)
                if all(
                    e.status in (AmortizationEntryStatus.PAID, AmortizationEntryStatus.WAIVED)
                    for e in entries
                ):
                    record.status = AmortizationStatus.COMPLETED
                    record.completed_at = datetime.now(timezone.utc)
                    self._repository.update_record(record)
                    completed.append(record)
        return completed

    def run_monthly_close(self, company_id: str) -> dict:
        due = self.process_due_entries(company_id)
        overdue = self.process_overdue_entries(company_id)
        completed = self.auto_complete_records(company_id)
        return {
            "company_id": company_id,
            "entries_marked_due": len(due),
            "entries_marked_overdue": len(overdue),
            "records_completed": len(completed),
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
