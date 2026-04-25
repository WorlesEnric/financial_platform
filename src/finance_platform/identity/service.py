from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.identity.company_switch import CompanySwitchManager, CompanySwitchResult
from finance_platform.identity.leave_check import LeaveCheckResult, LeaveCheckService
from finance_platform.identity.models import (
    Company,
    CompanySettings,
    CompanyType,
    CurrentContext,
    FinanceGroup,
    FinanceGroupMember,
    IdentityDocument,
    IdentityDocumentStatus,
    IdentityDocumentType,
    IdentityProvider,
    IdentityVerification,
    LeaveEntitlement,
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
    Membership,
    MembershipRole,
    OrgUnit,
    OrgUnitType,
    PendingInvitation,
    UserRegistration,
    VerificationMethod,
)
from finance_platform.identity.token_manager import TokenManager, TokenPayload
from finance_platform.identity.verification import VerificationService


class IdentityService:
    def __init__(
        self,
        token_manager: TokenManager,
        verification_service: Optional[VerificationService] = None,
        company_switch_manager: Optional[CompanySwitchManager] = None,
        leave_check_service: Optional[LeaveCheckService] = None,
    ) -> None:
        self.token_manager = token_manager
        self.verification_service = verification_service or VerificationService()
        self.company_switch_manager = company_switch_manager or CompanySwitchManager()
        self.leave_check_service = leave_check_service or LeaveCheckService()

    def create_user_registration(
        self,
        email: str,
        username: str,
        password_hash: str,
        verification_token: str,
        idp_provider: IdentityProvider = IdentityProvider.INTERNAL,
        idp_user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserRegistration:
        return UserRegistration(
            email=email,
            username=username,
            password_hash=password_hash,
            verification_token=verification_token,
            idp_provider=idp_provider,
            idp_user_id=idp_user_id,
            metadata=metadata or {},
        )

    def create_company(
        self,
        name: str,
        company_type: CompanyType = CompanyType.CORPORATION,
        legal_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        email: Optional[str] = None,
        country: Optional[str] = None,
        settings: Optional[CompanySettings] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Company:
        return Company(
            name=name,
            legal_name=legal_name,
            company_type=company_type,
            tax_id=tax_id,
            email=email,
            country=country,
            settings=settings or CompanySettings(),
            metadata=metadata or {},
        )

    def create_membership(
        self,
        user_id: str,
        company_id: str,
        role: MembershipRole = MembershipRole.MEMBER,
        department: Optional[str] = None,
        title: Optional[str] = None,
        manager_user_id: Optional[str] = None,
        is_default: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Membership:
        return Membership(
            user_id=user_id,
            company_id=company_id,
            role=role,
            department=department,
            title=title,
            manager_user_id=manager_user_id,
            is_default=is_default,
            metadata=metadata or {},
        )

    def create_org_unit(
        self,
        company_id: str,
        name: str,
        unit_type: OrgUnitType = OrgUnitType.DEPARTMENT,
        parent_id: Optional[str] = None,
        manager_user_id: Optional[str] = None,
        budget_minor: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrgUnit:
        return OrgUnit(
            company_id=company_id,
            name=name,
            unit_type=unit_type,
            parent_id=parent_id,
            manager_user_id=manager_user_id,
            budget_minor=budget_minor,
            metadata=metadata or {},
        )

    def create_finance_group(
        self,
        company_id: str,
        name: str,
        description: Optional[str] = None,
        approval_required: bool = True,
        max_amount_minor: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FinanceGroup:
        return FinanceGroup(
            company_id=company_id,
            name=name,
            description=description,
            approval_required=approval_required,
            max_amount_minor=max_amount_minor,
            metadata=metadata or {},
        )

    def add_group_member(
        self,
        group_id: str,
        user_id: str,
        company_id: str,
        is_approver: bool = False,
        approval_order: int = 0,
        max_approval_amount_minor: Optional[int] = None,
        added_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FinanceGroupMember:
        return FinanceGroupMember(
            group_id=group_id,
            user_id=user_id,
            company_id=company_id,
            is_approver=is_approver,
            approval_order=approval_order,
            max_approval_amount_minor=max_approval_amount_minor,
            added_by=added_by,
            metadata=metadata or {},
        )

    def create_pending_invitation(
        self,
        company_id: str,
        email: str,
        invited_by_user_id: str,
        role: MembershipRole = MembershipRole.MEMBER,
        token: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PendingInvitation:
        return PendingInvitation(
            company_id=company_id,
            email=email,
            invited_by_user_id=invited_by_user_id,
            role=role,
            token=token,
            metadata=metadata or {},
        )

    def create_identity_document(
        self,
        user_id: str,
        company_id: str,
        document_type: IdentityDocumentType,
        document_number: Optional[str] = None,
        issuing_country: Optional[str] = None,
        file_url: Optional[str] = None,
        file_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IdentityDocument:
        return IdentityDocument(
            user_id=user_id,
            company_id=company_id,
            document_type=document_type,
            document_number=document_number,
            issuing_country=issuing_country,
            file_url=file_url,
            file_hash=file_hash,
            metadata=metadata or {},
        )

    def create_identity_verification(
        self,
        user_id: str,
        company_id: str,
        method: VerificationMethod,
        max_attempts: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IdentityVerification:
        return IdentityVerification(
            user_id=user_id,
            company_id=company_id,
            method=method,
            max_attempts=max_attempts,
            metadata=metadata or {},
        )

    def create_leave_entitlement(
        self,
        user_id: str,
        company_id: str,
        leave_type: LeaveType,
        fiscal_year: int,
        total_days: float,
        carried_forward_days: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LeaveEntitlement:
        return LeaveEntitlement(
            user_id=user_id,
            company_id=company_id,
            leave_type=leave_type,
            fiscal_year=fiscal_year,
            total_days=total_days,
            carried_forward_days=carried_forward_days,
            metadata=metadata or {},
        )

    def create_leave_request(
        self,
        user_id: str,
        company_id: str,
        leave_type: LeaveType,
        start_date: Any,
        end_date: Any,
        total_days: float,
        reason: Optional[str] = None,
        work_handover_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LeaveRequest:
        return LeaveRequest(
            user_id=user_id,
            company_id=company_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            work_handover_to=work_handover_to,
            metadata=metadata or {},
        )

    def authenticate(
        self,
        user_id: str,
        company_id: str,
        membership_id: str,
        membership_role: MembershipRole,
        permissions: Optional[Dict[str, bool]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        payload = TokenPayload(
            user_id=user_id,
            company_id=company_id,
            membership_id=membership_id,
            membership_role=membership_role,
            permissions=permissions or {},
            metadata=metadata or {},
        )
        return self.token_manager.create_token_pair(payload)

    def verify_token(self, token: str) -> Optional[CurrentContext]:
        payload = self.token_manager.verify(token)
        if payload is None:
            return None
        return CurrentContext(
            user_id=payload.user_id,
            company_id=payload.company_id,
            membership_role=payload.membership_role,
            membership_id=payload.membership_id,
            permissions=payload.permissions,
            token_id=payload.token_id,
        )

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        return self.token_manager.refresh_access_token(refresh_token)

    def revoke_token(self, token: str) -> bool:
        return self.token_manager.revoke(token)

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
        return self.company_switch_manager.switch_company(
            user_id=user_id,
            current_context=current_context,
            target_company_id=target_company_id,
            memberships=memberships,
            companies=companies,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def check_leave_eligibility(
        self,
        user_id: str,
        company_id: str,
        leave_type: LeaveType,
        start_date: Any,
        end_date: Any,
        entitlements: List[LeaveEntitlement],
        existing_requests: List[LeaveRequest],
    ) -> LeaveCheckResult:
        return self.leave_check_service.check_eligibility(
            user_id=user_id,
            company_id=company_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            entitlements=entitlements,
            existing_requests=existing_requests,
        )

    def get_leave_balances(
        self,
        user_id: str,
        company_id: str,
        entitlements: List[LeaveEntitlement],
    ) -> Dict[str, Any]:
        balances = self.leave_check_service.get_leave_balances(user_id, company_id, entitlements)
        return {k: v.__dict__ for k, v in balances.items()}
