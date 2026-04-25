from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Dict, List, Optional

from finance_platform.identity.models import (
    LeaveEntitlement,
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
)


class LeaveBalance:
    def __init__(
        self,
        leave_type: LeaveType,
        total_days: float,
        used_days: float,
        pending_days: float,
        remaining_days: float,
        carried_forward_days: float,
        fiscal_year: int,
    ) -> None:
        self.leave_type = leave_type
        self.total_days = total_days
        self.used_days = used_days
        self.pending_days = pending_days
        self.remaining_days = remaining_days
        self.carried_forward_days = carried_forward_days
        self.fiscal_year = fiscal_year


class LeaveCheckResult:
    def __init__(
        self,
        eligible: bool,
        balance: Optional[LeaveBalance] = None,
        conflicts: List[LeaveRequest] = None,
        reason: Optional[str] = None,
    ) -> None:
        self.eligible = eligible
        self.balance = balance
        self.conflicts = conflicts or []
        self.reason = reason


class LeaveCheckService:
    def __init__(self) -> None:
        pass

    def check_eligibility(
        self,
        user_id: str,
        company_id: str,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        entitlements: List[LeaveEntitlement],
        existing_requests: List[LeaveRequest],
    ) -> LeaveCheckResult:
        requested_days = self._calculate_business_days(start_date, end_date)

        entitlement = self._find_entitlement(entitlements, user_id, company_id, leave_type, start_date.year)
        if entitlement is None:
            return LeaveCheckResult(
                eligible=False,
                reason=f"No leave entitlement found for {leave_type.value} in {start_date.year}",
            )

        balance = LeaveBalance(
            leave_type=leave_type,
            total_days=entitlement.total_days,
            used_days=entitlement.used_days,
            pending_days=entitlement.pending_days,
            remaining_days=entitlement.remaining_days,
            carried_forward_days=entitlement.carried_forward_days,
            fiscal_year=entitlement.fiscal_year,
        )

        conflicts = self._find_date_conflicts(
            user_id, company_id, start_date, end_date, existing_requests
        )

        if requested_days > balance.remaining_days:
            return LeaveCheckResult(
                eligible=False,
                balance=balance,
                conflicts=conflicts,
                reason=f"Insufficient balance: {requested_days} days requested, {balance.remaining_days} remaining",
            )

        if conflicts:
            return LeaveCheckResult(
                eligible=False,
                balance=balance,
                conflicts=conflicts,
                reason=f"Date conflicts with {len(conflicts)} existing leave request(s)",
            )

        return LeaveCheckResult(eligible=True, balance=balance, conflicts=conflicts)

    def get_leave_balances(
        self,
        user_id: str,
        company_id: str,
        entitlements: List[LeaveEntitlement],
    ) -> Dict[str, LeaveBalance]:
        balances: Dict[str, LeaveBalance] = {}
        for ent in entitlements:
            if ent.user_id != user_id or ent.company_id != company_id:
                continue
            if ent.is_deleted:
                continue
            balances[ent.leave_type.value] = LeaveBalance(
                leave_type=ent.leave_type,
                total_days=ent.total_days,
                used_days=ent.used_days,
                pending_days=ent.pending_days,
                remaining_days=ent.remaining_days,
                carried_forward_days=ent.carried_forward_days,
                fiscal_year=ent.fiscal_year,
            )
        return balances

    def consume_leave(
        self,
        entitlement: LeaveEntitlement,
        days: float,
        leave_request: LeaveRequest,
    ) -> LeaveEntitlement:
        entitlement.pending_days += days
        return entitlement

    def confirm_leave(
        self,
        entitlement: LeaveEntitlement,
        days: float,
        leave_request: LeaveRequest,
    ) -> LeaveEntitlement:
        entitlement.pending_days = max(0.0, entitlement.pending_days - days)
        entitlement.used_days += days
        return entitlement

    def cancel_leave(
        self,
        entitlement: LeaveEntitlement,
        days: float,
        leave_request: LeaveRequest,
    ) -> LeaveEntitlement:
        entitlement.pending_days = max(0.0, entitlement.pending_days - days)
        return entitlement

    def _find_entitlement(
        self,
        entitlements: List[LeaveEntitlement],
        user_id: str,
        company_id: str,
        leave_type: LeaveType,
        year: int,
    ) -> Optional[LeaveEntitlement]:
        for ent in entitlements:
            if (
                ent.user_id == user_id
                and ent.company_id == company_id
                and ent.leave_type == leave_type
                and ent.fiscal_year == year
                and not ent.is_deleted
            ):
                return ent
        return None

    def _find_date_conflicts(
        self,
        user_id: str,
        company_id: str,
        start_date: date,
        end_date: date,
        existing_requests: List[LeaveRequest],
    ) -> List[LeaveRequest]:
        conflicts: List[LeaveRequest] = []
        for req in existing_requests:
            if req.user_id != user_id or req.company_id != company_id:
                continue
            if req.is_deleted or req.status in (
                LeaveRequestStatus.CANCELLED,
                LeaveRequestStatus.REJECTED,
                LeaveRequestStatus.WITHDRAWN,
            ):
                continue
            if self._dates_overlap(start_date, end_date, req.start_date, req.end_date):
                conflicts.append(req)
        return conflicts

    def _dates_overlap(self, start1: date, end1: date, start2: date, end2: date) -> bool:
        return start1 <= end2 and start2 <= end1

    def _calculate_business_days(self, start_date: date, end_date: date) -> float:
        from datetime import timedelta

        if start_date > end_date:
            return 0.0

        total = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:
                total += 1
            current += timedelta(days=1)
        return float(total)
