from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from finance_platform.approvals.models import (
    Approval,
    ApprovalPolicy,
    ApprovalStatus,
    ApprovalStep,
    ApprovalType,
    PolicyRule,
    StepStatus,
)


class ApprovalRepository:
    """In-memory repository for approvals. In production this would be replaced
    with a database-backed implementation."""

    def __init__(self) -> None:
        self._approvals: dict[str, Approval] = {}
        self._policies: dict[str, ApprovalPolicy] = {}
        self._delegations: dict[str, dict] = {}

    # --- Approvals ---

    def save_approval(self, approval: Approval) -> Approval:
        approval.updated_at = datetime.now(timezone.utc)
        self._approvals[approval.id] = approval
        return approval

    def get_approval(self, approval_id: str) -> Optional[Approval]:
        return self._approvals.get(approval_id)

    def get_approval_or_raise(self, approval_id: str) -> Approval:
        approval = self.get_approval(approval_id)
        if approval is None:
            from finance_platform.approvals.exceptions import ApprovalNotFoundError

            raise ApprovalNotFoundError(approval_id)
        return approval

    def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        approval_type: Optional[ApprovalType] = None,
        requester_id: Optional[str] = None,
        approver_id: Optional[str] = None,
        reference_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Approval], int]:
        results = list(self._approvals.values())

        if status is not None:
            results = [a for a in results if a.status == status]
        if approval_type is not None:
            results = [a for a in results if a.approval_type == approval_type]
        if requester_id is not None:
            results = [a for a in results if a.requester_id == requester_id]
        if approver_id is not None:
            results = [
                a
                for a in results
                if any(s.approver_id == approver_id for s in a.steps)
            ]
        if reference_id is not None:
            results = [a for a in results if a.reference_id == reference_id]

        results.sort(key=lambda a: a.created_at, reverse=True)
        total = len(results)

        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return paginated, total

    def delete_approval(self, approval_id: str) -> bool:
        return self._approvals.pop(approval_id, None) is not None

    # --- Steps ---

    def save_step(self, step: ApprovalStep) -> ApprovalStep:
        parent = self._approvals.get(step.approval_id)
        if parent is not None:
            for i, s in enumerate(parent.steps):
                if s.id == step.id:
                    parent.steps[i] = step
                    break
            parent.updated_at = datetime.now(timezone.utc)
        return step

    def get_step(self, step_id: str) -> Optional[ApprovalStep]:
        for approval in self._approvals.values():
            for step in approval.steps:
                if step.id == step_id:
                    return step
        return None

    def get_step_or_raise(self, step_id: str) -> ApprovalStep:
        step = self.get_step(step_id)
        if step is None:
            from finance_platform.approvals.exceptions import ApprovalStepNotFoundError

            raise ApprovalStepNotFoundError(step_id)
        return step

    def get_pending_steps_for_approver(
        self, approver_id: str
    ) -> list[ApprovalStep]:
        pending: list[ApprovalStep] = []
        for approval in self._approvals.values():
            if approval.status not in (
                ApprovalStatus.PENDING,
                ApprovalStatus.IN_PROGRESS,
            ):
                continue
            current = approval.current_step
            if current and current.approver_id == approver_id and current.status == StepStatus.PENDING:
                pending.append(current)
        return pending

    # --- Policies ---

    def save_policy(self, policy: ApprovalPolicy) -> ApprovalPolicy:
        policy.updated_at = datetime.now(timezone.utc)
        self._policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: str) -> Optional[ApprovalPolicy]:
        return self._policies.get(policy_id)

    def list_policies(
        self, approval_type: Optional[ApprovalType] = None, active_only: bool = True
    ) -> list[ApprovalPolicy]:
        results = list(self._policies.values())
        if active_only:
            results = [p for p in results if p.active]
        if approval_type is not None:
            results = [p for p in results if p.approval_type == approval_type]
        return results

    def delete_policy(self, policy_id: str) -> bool:
        return self._policies.pop(policy_id, None) is not None

    # --- Delegations ---

    def save_delegation(self, delegation: dict) -> dict:
        self._delegations[delegation["id"]] = delegation
        return delegation

    def get_delegation(self, delegation_id: str) -> Optional[dict]:
        return self._delegations.get(delegation_id)

    def list_delegations(
        self,
        delegator_id: Optional[str] = None,
        delegate_id: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict]:
        results = list(self._delegations.values())
        now = datetime.now(timezone.utc)
        if active_only:
            results = [
                d
                for d in results
                if d.get("active", False)
                and d["start_date"] <= now
                and (d.get("end_date") is None or d["end_date"] >= now)
            ]
        if delegator_id is not None:
            results = [d for d in results if d["delegator_id"] == delegator_id]
        if delegate_id is not None:
            results = [d for d in results if d["delegate_id"] == delegate_id]
        return results

    def get_active_delegation(
        self, delegator_id: str, role: str
    ) -> Optional[dict]:
        now = datetime.now(timezone.utc)
        for d in self._delegations.values():
            if (
                d["delegator_id"] == delegator_id
                and d["role"] == role
                and d.get("active", False)
                and d["start_date"] <= now
                and (d.get("end_date") is None or d["end_date"] >= now)
            ):
                return d
        return None

    def deactivate_delegation(self, delegation_id: str) -> Optional[dict]:
        delegation = self._delegations.get(delegation_id)
        if delegation:
            delegation["active"] = False
        return delegation

    # --- Stats ---

    def get_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        total = len(self._approvals)
        if total == 0:
            return {
                "total_pending": 0,
                "total_approved": 0,
                "total_rejected": 0,
                "total_escalated": 0,
                "total_expired": 0,
                "average_approval_time_hours": 0.0,
                "pending_approvals_by_type": {},
            }

        pending = sum(1 for a in self._approvals.values() if a.is_pending)
        approved = sum(1 for a in self._approvals.values() if a.is_approved)
        rejected = sum(1 for a in self._approvals.values() if a.is_rejected)
        escalated = sum(
            1 for a in self._approvals.values() if a.status == ApprovalStatus.ESCALATED
        )
        expired = sum(
            1 for a in self._approvals.values() if a.status == ApprovalStatus.EXPIRED
        )

        completed = [
            a
            for a in self._approvals.values()
            if a.completed_at is not None and a.created_at is not None
        ]
        total_hours = sum(
            (a.completed_at - a.created_at).total_seconds() / 3600
            for a in completed
            if a.completed_at and a.created_at
        )
        avg_hours = total_hours / len(completed) if completed else 0.0

        type_counts: dict[str, int] = {}
        for a in self._approvals.values():
            if a.is_pending:
                type_counts[a.approval_type.value] = (
                    type_counts.get(a.approval_type.value, 0) + 1
                )

        return {
            "total_pending": pending,
            "total_approved": approved,
            "total_rejected": rejected,
            "total_escalated": escalated,
            "total_expired": expired,
            "average_approval_time_hours": round(avg_hours, 2),
            "pending_approvals_by_type": type_counts,
        }
