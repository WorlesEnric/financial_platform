from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.identity.models import (
    Company,
    CurrentContext,
    Membership,
    MembershipRole,
)


class CompanySwitchResult:
    def __init__(
        self,
        success: bool,
        context: Optional[CurrentContext] = None,
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.context = context
        self.error = error


class CompanySwitchManager:
    def __init__(self) -> None:
        self._active_sessions: Dict[str, CurrentContext] = {}

    def switch_company(
        self,
        user_id: str,
        current_context: CurrentContext,
        target_company_id: str,
        memberships: List[Membership],
        companies: List[Company],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> CompanySwitchResult:
        if user_id != current_context.user_id:
            return CompanySwitchResult(
                success=False,
                error="User ID mismatch with current context",
            )

        target_membership: Optional[Membership] = None
        for m in memberships:
            if m.user_id == user_id and m.company_id == target_company_id and m.is_active and not m.is_deleted:
                target_membership = m
                break

        if target_membership is None:
            return CompanySwitchResult(
                success=False,
                error="User is not an active member of the target company",
            )

        target_company: Optional[Company] = None
        for c in companies:
            if c.id == target_company_id and c.is_active and not c.is_deleted:
                target_company = c
                break

        if target_company is None:
            return CompanySwitchResult(
                success=False,
                error="Target company is not active or does not exist",
            )

        new_context = CurrentContext(
            user_id=user_id,
            company_id=target_company_id,
            membership_role=target_membership.role,
            membership_id=target_membership.id,
            is_impersonated=current_context.is_impersonated,
            impersonated_by=current_context.impersonated_by,
            permissions=target_membership.permissions_override,
            token_id=current_context.token_id,
            session_id=current_context.session_id,
            ip_address=ip_address or current_context.ip_address,
            user_agent=user_agent or current_context.user_agent,
        )

        session_key = f"{user_id}:{current_context.session_id or 'default'}"
        self._active_sessions[session_key] = new_context

        return CompanySwitchResult(success=True, context=new_context)

    def get_current_context(
        self,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> Optional[CurrentContext]:
        session_key = f"{user_id}:{session_id or 'default'}"
        return self._active_sessions.get(session_key)

    def clear_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> None:
        session_key = f"{user_id}:{session_id or 'default'}"
        self._active_sessions.pop(session_key, None)

    def list_user_companies(
        self,
        user_id: str,
        memberships: List[Membership],
        companies: List[Company],
    ) -> List[Dict[str, Any]]:
        active_memberships = {
            m.company_id: m
            for m in memberships
            if m.user_id == user_id and m.is_active and not m.is_deleted
        }
        result: List[Dict[str, Any]] = []
        for company in companies:
            if company.id in active_memberships and company.is_active and not company.is_deleted:
                m = active_memberships[company.id]
                result.append({
                    "company_id": company.id,
                    "company_name": company.name,
                    "role": m.role.value,
                    "is_default": m.is_default,
                    "title": m.title,
                    "department": m.department,
                })
        return result
