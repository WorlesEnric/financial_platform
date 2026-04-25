from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.errors.exceptions import NotFoundError, ValidationError
from finance_platform.models.base import CurrencyCode


class ReportService:
    def __init__(self) -> None:
        self._reports: Dict[str, Dict[str, Any]] = {}

    def generate_expense_summary(
        self,
        expenses: List[Dict[str, Any]],
        group_by: str = "category",
        currency: CurrencyCode = CurrencyCode.USD,
    ) -> Dict[str, Any]:
        if not expenses:
            return {"total": 0.0, "count": 0, "groups": {}, "currency": currency.value}
        total = sum(e.get("total_amount", 0) for e in expenses)
        groups: Dict[str, float] = {}
        count_by_group: Dict[str, int] = {}
        for e in expenses:
            key = str(e.get(group_by, "unknown"))
            groups[key] = round(groups.get(key, 0) + e.get("total_amount", 0), 2)
            count_by_group[key] = count_by_group.get(key, 0) + 1
        return {
            "total": round(total, 2),
            "count": len(expenses),
            "average": round(total / len(expenses), 2),
            "groups": groups,
            "count_by_group": count_by_group,
            "group_by": group_by,
            "currency": currency.value,
        }

    def generate_amortization_summary(
        self,
        schedules: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not schedules:
            return {"total_amount": 0.0, "amortized": 0.0, "remaining": 0.0, "count": 0}
        total = sum(s.get("total_amount", 0) for s in schedules)
        amortized = sum(s.get("amortized_amount", 0) for s in schedules)
        by_method: Dict[str, int] = {}
        for s in schedules:
            method = s.get("rule", {}).get("method", "unknown") if isinstance(s.get("rule"), dict) else "unknown"
            by_method[method] = by_method.get(method, 0) + 1
        return {
            "total_amount": round(total, 2),
            "amortized": round(amortized, 2),
            "remaining": round(total - amortized, 2),
            "count": len(schedules),
            "completed": sum(1 for s in schedules if s.get("is_completed")),
            "by_method": by_method,
        }

    def generate_settlement_summary(
        self,
        settlements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not settlements:
            return {"total_settled": 0.0, "count": 0, "by_status": {}}
        total = sum(s.get("settled_amount", 0) for s in settlements)
        by_status: Dict[str, int] = {}
        for s in settlements:
            status = s.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "total_settled": round(total, 2),
            "count": len(settlements),
            "by_status": by_status,
            "fully_settled": sum(1 for s in settlements if s.get("remaining_amount", 0) < 0.001),
        }

    def generate_debt_summary(
        self,
        debts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not debts:
            return {"total_original": 0.0, "total_outstanding": 0.0, "count": 0}
        original = sum(d.get("original_amount", 0) for d in debts)
        outstanding = sum(d.get("outstanding_amount", 0) for d in debts)
        by_status: Dict[str, int] = {}
        for d in debts:
            status = d.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
        return {
            "total_original": round(original, 2),
            "total_outstanding": round(outstanding, 2),
            "total_paid": round(original - outstanding, 2),
            "count": len(debts),
            "by_status": by_status,
            "overdue": sum(1 for d in debts if d.get("is_overdue")),
        }

    def generate_approval_summary(
        self,
        chains: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not chains:
            return {"count": 0, "by_state": {}, "avg_approval_time_hours": 0.0}
        by_state: Dict[str, int] = {}
        total_time_hours: float = 0.0
        resolved_count: int = 0
        for c in chains:
            state = c.get("state", "unknown")
            by_state[state] = by_state.get(state, 0) + 1
            if state in ("approved", "rejected", "cancelled"):
                resolved_at = c.get("resolved_at")
                initiated_at = c.get("initiated_at")
                if resolved_at and initiated_at:
                    try:
                        resolved_dt = datetime.fromisoformat(resolved_at) if isinstance(resolved_at, str) else resolved_at
                        initiated_dt = datetime.fromisoformat(initiated_at) if isinstance(initiated_at, str) else initiated_at
                        delta = (resolved_dt - initiated_dt).total_seconds() / 3600
                        total_time_hours += delta
                        resolved_count += 1
                    except (ValueError, TypeError):
                        pass
        return {
            "count": len(chains),
            "by_state": by_state,
            "avg_approval_time_hours": round(total_time_hours / resolved_count, 2) if resolved_count else 0.0,
            "pending": by_state.get("pending", 0),
            "approved": by_state.get("approved", 0),
            "rejected": by_state.get("rejected", 0),
        }

    def generate_audit_summary(
        self,
        logs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not logs:
            return {"count": 0, "by_action": {}, "by_entity": {}, "unique_actors": 0}
        by_action: Dict[str, int] = {}
        by_entity: Dict[str, int] = {}
        actors: set = set()
        for log in logs:
            action = log.get("action", "unknown")
            by_action[action] = by_action.get(action, 0) + 1
            entity = log.get("entity_type", "unknown")
            by_entity[entity] = by_entity.get(entity, 0) + 1
            actor = log.get("actor_id")
            if actor:
                actors.add(actor)
        return {
            "count": len(logs),
            "by_action": by_action,
            "by_entity": by_entity,
            "unique_actors": len(actors),
        }

    def save_report(self, report_type: str, data: Dict[str, Any]) -> str:
        report_id = str(datetime.now(timezone.utc).timestamp())
        self._reports[report_id] = {
            "id": report_id,
            "type": report_type,
            "data": data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return report_id

    def get_report(self, report_id: str) -> Dict[str, Any]:
        report = self._reports.get(report_id)
        if not report:
            raise NotFoundError(f"Report {report_id} not found", resource_type="Report", resource_id=report_id)
        return report

    def list_reports(self, report_type: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self._reports.values())
        if report_type:
            results = [r for r in results if r.get("type") == report_type]
        results.sort(key=lambda r: r.get("generated_at", ""), reverse=True)
        return results

    def export_to_csv(self, data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
        if not data:
            return ""
        if columns is None:
            columns = list(data[0].keys())
        header = ",".join(columns)
        rows: List[str] = [header]
        for row in data:
            values = []
            for col in columns:
                val = row.get(col, "")
                if isinstance(val, str) and ("," in val or '"' in val):
                    escaped = val.replace('"', '""')
                    val = f'"{escaped}"'
                values.append(str(val))
            rows.append(",".join(values))
        return "\n".join(rows)
