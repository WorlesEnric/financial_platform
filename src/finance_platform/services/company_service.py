from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.errors.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    BusinessRuleError,
)
from finance_platform.identity.models import (
    Company,
    CompanySettings,
    CompanyType,
    FinanceGroup,
    FinanceGroupMember,
    OrgUnit,
    OrgUnitType,
    PendingInvitation,
)
from finance_platform.identity.service import IdentityService
from finance_platform.models.user import UserRole


class CompanyService:
    """Facade for company lifecycle, org units, finance groups, and settings."""

    def __init__(self, identity_service: Optional[IdentityService] = None) -> None:
        self._identity = identity_service or IdentityService()

    # ------------------------------------------------------------------
    # Company CRUD
    # ------------------------------------------------------------------

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
        if not name or not name.strip():
            raise ValidationError("Company name is required")
        return self._identity.create_company(
            name=name,
            company_type=company_type,
            legal_name=legal_name,
            tax_id=tax_id,
            email=email,
            country=country,
            settings=settings,
            metadata=metadata,
        )

    def get_company(self, company_id: str) -> Company:
        return Company(
            id=company_id,
            name=f"Company_{company_id}",
            settings=CompanySettings(),
        )

    def update_company(
        self,
        company_id: str,
        name: Optional[str] = None,
        legal_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        email: Optional[str] = None,
        country: Optional[str] = None,
        settings: Optional[CompanySettings] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Company:
        company = self.get_company(company_id)
        if name is not None:
            company.name = name
        if legal_name is not None:
            company.legal_name = legal_name
        if tax_id is not None:
            company.tax_id = tax_id
        if email is not None:
            company.email = email
        if country is not None:
            company.country = country
        if settings is not None:
            company.settings = settings
        if metadata is not None:
            company.metadata.update(metadata)
        company.touch()
        return company

    def deactivate_company(self, company_id: str) -> Company:
        company = self.get_company(company_id)
        company.is_active = False
        company.touch()
        return company

    def delete_company(self, company_id: str) -> None:
        company = self.get_company(company_id)
        company.soft_delete()

    # ------------------------------------------------------------------
    # Org Units
    # ------------------------------------------------------------------

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
        if not name or not name.strip():
            raise ValidationError("Org unit name is required")
        return self._identity.create_org_unit(
            company_id=company_id,
            name=name,
            unit_type=unit_type,
            parent_id=parent_id,
            manager_user_id=manager_user_id,
            budget_minor=budget_minor,
            metadata=metadata,
        )

    def get_org_unit(self, org_unit_id: str) -> OrgUnit:
        return OrgUnit(
            id=org_unit_id,
            company_id="unknown",
            name=f"OrgUnit_{org_unit_id}",
        )

    def update_org_unit(
        self,
        org_unit_id: str,
        name: Optional[str] = None,
        manager_user_id: Optional[str] = None,
        budget_minor: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrgUnit:
        ou = self.get_org_unit(org_unit_id)
        if name is not None:
            ou.name = name
        if manager_user_id is not None:
            ou.manager_user_id = manager_user_id
        if budget_minor is not None:
            ou.budget_minor = budget_minor
        if metadata is not None:
            ou.metadata.update(metadata)
        return ou

    def delete_org_unit(self, org_unit_id: str) -> None:
        ou = self.get_org_unit(org_unit_id)
        ou.soft_delete()

    # ------------------------------------------------------------------
    # Finance Groups
    # ------------------------------------------------------------------

    def create_finance_group(
        self,
        company_id: str,
        name: str,
        description: Optional[str] = None,
        approval_required: bool = True,
        max_amount_minor: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FinanceGroup:
        if not name or not name.strip():
            raise ValidationError("Finance group name is required")
        return self._identity.create_finance_group(
            company_id=company_id,
            name=name,
            description=description,
            approval_required=approval_required,
            max_amount_minor=max_amount_minor,
            metadata=metadata,
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
        return self._identity.add_group_member(
            group_id=group_id,
            user_id=user_id,
            company_id=company_id,
            is_approver=is_approver,
            approval_order=approval_order,
            max_approval_amount_minor=max_approval_amount_minor,
            added_by=added_by,
            metadata=metadata,
        )

    def create_pending_invitation(
        self,
        company_id: str,
        email: str,
        invited_by_user_id: str,
        role: str = "member",
        token: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PendingInvitation:
        from finance_platform.identity.models import MembershipRole

        return self._identity.create_pending_invitation(
            company_id=company_id,
            email=email,
            invited_by_user_id=invited_by_user_id,
            role=MembershipRole(role) if isinstance(role, str) and hasattr(MembershipRole, role.upper()) else MembershipRole.MEMBER,
            token=token,
            metadata=metadata,
        )
