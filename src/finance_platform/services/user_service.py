from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.errors.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    BusinessRuleError,
)
from finance_platform.identity.company_switch import CompanySwitchManager
from finance_platform.identity.leave_check import LeaveCheckService
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
    LeaveEntitlement,
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
    Membership,
    MembershipRole,
    OrgUnit,
    OrgUnitType,
    PendingInvitation,
)
from finance_platform.identity.service import IdentityService
from finance_platform.identity.token_manager import TokenManager
from finance_platform.identity.verification import VerificationService
from finance_platform.models.user import User, UserProfile, UserRole, UserSettings


class UserService:
    def __init__(
        self,
        identity_service: Optional[IdentityService] = None,
        token_manager: Optional[TokenManager] = None,
    ) -> None:
        self._users: Dict[str, User] = {}
        self._companies: Dict[str, Company] = {}
        self._memberships: Dict[str, Membership] = {}
        self._org_units: Dict[str, OrgUnit] = {}
        self._finance_groups: Dict[str, FinanceGroup] = {}
        self._finance_group_members: Dict[str, FinanceGroupMember] = {}
        self._invitations: Dict[str, PendingInvitation] = {}
        self._identity_docs: Dict[str, IdentityDocument] = {}
        self._leave_entitlements: Dict[str, LeaveEntitlement] = {}
        self._leave_requests: Dict[str, LeaveRequest] = {}
        self._next_membership_idx: int = 0
        token_mgr = token_manager or TokenManager(secret_key="dev-secret-key")
        self.identity = identity_service or IdentityService(token_manager=token_mgr)

    def register_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        role: UserRole = UserRole.EMPLOYEE,
        full_name: Optional[str] = None,
        department: Optional[str] = None,
        manager_id: Optional[str] = None,
    ) -> User:
        for u in self._users.values():
            if u.email == email:
                raise ConflictError(f"User with email {email} already exists")
            if u.username == username:
                raise ConflictError(f"Username {username} already taken")
        user = User(
            email=email,
            username=username,
            role=role,
            profile=UserProfile(
                full_name=full_name or username,
                department=department,
                manager_id=manager_id,
            ),
        )
        self._users[user.id] = user
        return user

    def get_user(self, user_id: str) -> User:
        user = self._users.get(user_id)
        if not user or user.is_deleted:
            raise NotFoundError(f"User {user_id} not found", resource_type="User", resource_id=user_id)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email and not user.is_deleted:
                return user
        return None

    def update_user(self, user_id: str, **updates: Any) -> User:
        user = self.get_user(user_id)
        for key, value in updates.items():
            if hasattr(user, key) and key not in ("id", "email", "created_at"):
                setattr(user, key, value)
        user.touch()
        return user

    def delete_user(self, user_id: str) -> None:
        user = self.get_user(user_id)
        user.soft_delete()

    def list_users(
        self,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        company_id: Optional[str] = None,
    ) -> List[User]:
        results = [u for u in self._users.values() if not u.is_deleted]
        if role:
            results = [u for u in results if u.role == role]
        if is_active is not None:
            results = [u for u in results if u.is_active == is_active]
        if company_id:
            member_ids = {
                m.user_id
                for m in self._memberships.values()
                if m.company_id == company_id and not m.is_deleted
            }
            results = [u for u in results if u.id in member_ids]
        return results

    def create_company(
        self,
        name: str,
        legal_name: Optional[str] = None,
        tax_id: Optional[str] = None,
        email: Optional[str] = None,
        country: Optional[str] = None,
        company_type: CompanyType = CompanyType.CORPORATION,
    ) -> Company:
        company = self.identity.create_company(
            name=name,
            legal_name=legal_name,
            tax_id=tax_id,
            email=email,
            country=country,
            company_type=company_type,
        )
        self._companies[company.id] = company
        return company

    def get_company(self, company_id: str) -> Company:
        company = self._companies.get(company_id)
        if not company or company.is_deleted:
            raise NotFoundError(f"Company {company_id} not found", resource_type="Company", resource_id=company_id)
        return company

    def update_company(self, company_id: str, **updates: Any) -> Company:
        company = self.get_company(company_id)
        for key, value in updates.items():
            if hasattr(company, key) and key not in ("id", "created_at"):
                setattr(company, key, value)
        company.touch()
        return company

    def list_companies(self) -> List[Company]:
        return [c for c in self._companies.values() if not c.is_deleted]

    def add_membership(
        self,
        user_id: str,
        company_id: str,
        role: MembershipRole = MembershipRole.MEMBER,
        department: Optional[str] = None,
        title: Optional[str] = None,
        manager_user_id: Optional[str] = None,
        is_default: bool = False,
    ) -> Membership:
        self.get_user(user_id)
        self.get_company(company_id)
        for m in self._memberships.values():
            if m.user_id == user_id and m.company_id == company_id and not m.is_deleted:
                raise ConflictError(f"User {user_id} is already a member of company {company_id}")
        membership = self.identity.create_membership(
            user_id=user_id,
            company_id=company_id,
            role=role,
            department=department,
            title=title,
            manager_user_id=manager_user_id,
            is_default=is_default,
        )
        self._memberships[membership.id] = membership
        return membership

    def get_membership(self, membership_id: str) -> Membership:
        membership = self._memberships.get(membership_id)
        if not membership or membership.is_deleted:
            raise NotFoundError(f"Membership {membership_id} not found", resource_type="Membership", resource_id=membership_id)
        return membership

    def list_memberships(self, user_id: Optional[str] = None, company_id: Optional[str] = None) -> List[Membership]:
        results = [m for m in self._memberships.values() if not m.is_deleted]
        if user_id:
            results = [m for m in results if m.user_id == user_id]
        if company_id:
            results = [m for m in results if m.company_id == company_id]
        return results

    def remove_membership(self, membership_id: str) -> None:
        membership = self.get_membership(membership_id)
        membership.soft_delete()

    def create_org_unit(
        self,
        company_id: str,
        name: str,
        unit_type: OrgUnitType = OrgUnitType.DEPARTMENT,
        parent_id: Optional[str] = None,
        manager_user_id: Optional[str] = None,
    ) -> OrgUnit:
        self.get_company(company_id)
        org_unit = self.identity.create_org_unit(
            company_id=company_id,
            name=name,
            unit_type=unit_type,
            parent_id=parent_id,
            manager_user_id=manager_user_id,
        )
        self._org_units[org_unit.id] = org_unit
        return org_unit

    def get_org_unit(self, org_unit_id: str) -> OrgUnit:
        org_unit = self._org_units.get(org_unit_id)
        if not org_unit or org_unit.is_deleted:
            raise NotFoundError(f"OrgUnit {org_unit_id} not found", resource_type="OrgUnit", resource_id=org_unit_id)
        return org_unit

    def list_org_units(self, company_id: str) -> List[OrgUnit]:
        return [o for o in self._org_units.values() if o.company_id == company_id and not o.is_deleted]

    def create_finance_group(
        self,
        company_id: str,
        name: str,
        description: Optional[str] = None,
        approval_required: bool = True,
    ) -> FinanceGroup:
        self.get_company(company_id)
        group = self.identity.create_finance_group(
            company_id=company_id,
            name=name,
            description=description,
            approval_required=approval_required,
        )
        self._finance_groups[group.id] = group
        return group

    def add_finance_group_member(
        self,
        group_id: str,
        user_id: str,
        company_id: str,
        is_approver: bool = False,
        approval_order: int = 0,
        max_approval_amount: Optional[float] = None,
    ) -> FinanceGroupMember:
        self.get_user(user_id)
        self.get_company(company_id)
        if group_id not in self._finance_groups:
            raise NotFoundError(f"FinanceGroup {group_id} not found", resource_type="FinanceGroup", resource_id=group_id)
        max_minor = int(max_approval_amount * 100) if max_approval_amount is not None else None
        member = self.identity.add_group_member(
            group_id=group_id,
            user_id=user_id,
            company_id=company_id,
            is_approver=is_approver,
            approval_order=approval_order,
            max_approval_amount_minor=max_minor,
        )
        self._finance_group_members[member.id] = member
        return member

    def list_finance_group_members(self, group_id: str) -> List[FinanceGroupMember]:
        return [m for m in self._finance_group_members.values() if m.group_id == group_id]

    def create_invitation(
        self,
        company_id: str,
        email: str,
        invited_by_user_id: str,
        role: MembershipRole = MembershipRole.MEMBER,
    ) -> PendingInvitation:
        self.get_company(company_id)
        self.get_user(invited_by_user_id)
        invitation = self.identity.create_pending_invitation(
            company_id=company_id,
            email=email,
            invited_by_user_id=invited_by_user_id,
            role=role,
        )
        self._invitations[invitation.id] = invitation
        return invitation

    def create_identity_document(
        self,
        user_id: str,
        company_id: str,
        document_type: IdentityDocumentType,
        document_number: Optional[str] = None,
        issuing_country: Optional[str] = None,
    ) -> IdentityDocument:
        self.get_user(user_id)
        self.get_company(company_id)
        doc = self.identity.create_identity_document(
            user_id=user_id,
            company_id=company_id,
            document_type=document_type,
            document_number=document_number,
            issuing_country=issuing_country,
        )
        self._identity_docs[doc.id] = doc
        return doc

    def authenticate_user(self, user_id: str, company_id: str) -> Dict[str, str]:
        memberships = self.list_memberships(user_id=user_id, company_id=company_id)
        if not memberships:
            raise NotFoundError(f"No membership found for user {user_id} in company {company_id}")
        membership = memberships[0]
        return self.identity.authenticate(
            user_id=user_id,
            company_id=company_id,
            membership_id=membership.id,
            membership_role=membership.role,
        )

    def verify_token(self, token: str) -> Optional[CurrentContext]:
        return self.identity.verify_token(token)

    def seed_demo_data(self) -> Dict[str, List[str]]:
        admin = self.register_user(
            email="admin@demo.com",
            username="admin",
            password_hash="hashed_admin",
            role=UserRole.ADMIN,
            full_name="System Admin",
        )
        manager = self.register_user(
            email="manager@demo.com",
            username="manager",
            password_hash="hashed_manager",
            role=UserRole.MANAGER,
            full_name="Department Manager",
        )
        employee = self.register_user(
            email="employee@demo.com",
            username="employee",
            password_hash="hashed_employee",
            role=UserRole.EMPLOYEE,
            full_name="Jane Employee",
        )
        company = self.create_company(
            name="Demo Corp",
            legal_name="Demo Corporation Ltd",
            tax_id="TAX-12345",
            email="finance@democorp.com",
            country="US",
        )
        for user_id in (admin.id, manager.id, employee.id):
            self.add_membership(
                user_id=user_id,
                company_id=company.id,
                role=MembershipRole.ADMIN if user_id == admin.id else MembershipRole.MANAGER if user_id == manager.id else MembershipRole.MEMBER,
                is_default=True,
            )
        eng_unit = self.create_org_unit(company_id=company.id, name="Engineering", manager_user_id=manager.id)
        self.create_org_unit(company_id=company.id, name="Finance", manager_user_id=admin.id)
        fin_group = self.create_finance_group(company_id=company.id, name="Finance Approvers")
        self.add_finance_group_member(
            group_id=fin_group.id,
            user_id=manager.id,
            company_id=company.id,
            is_approver=True,
            approval_order=1,
            max_approval_amount=50000.0,
        )
        return {
            "user_ids": [admin.id, manager.id, employee.id],
            "company_ids": [company.id],
            "org_unit_ids": [eng_unit.id],
        }

    def close_month(self, company_id: str, year: int, month: int) -> Dict[str, Any]:
        company = self.get_company(company_id)
        summary = {
            "company_id": company_id,
            "company_name": company.name,
            "year": year,
            "month": month,
            "period": f"{year}-{month:02d}",
            "closed_at": datetime.now(timezone.utc).isoformat(),
            "total_users": len(self.list_users(company_id=company_id)),
            "total_memberships": len(self.list_memberships(company_id=company_id)),
        }
        return summary
