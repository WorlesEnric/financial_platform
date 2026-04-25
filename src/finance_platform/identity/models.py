from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import EmailStr, Field, field_validator, model_validator

from finance_platform.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, VersionMixin


class CompanyType(str, Enum):
    CORPORATION = "corporation"
    LLC = "llc"
    PARTNERSHIP = "partnership"
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    NON_PROFIT = "non_profit"
    GOVERNMENT = "government"
    OTHER = "other"


class MembershipRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    FINANCE_ADMIN = "finance_admin"
    MANAGER = "manager"
    APPROVER = "approver"
    MEMBER = "member"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class OrgUnitType(str, Enum):
    DEPARTMENT = "department"
    DIVISION = "division"
    TEAM = "team"
    PROJECT = "project"
    BRANCH = "branch"
    REGION = "region"
    COST_CENTER = "cost_center"


class IdentityDocumentType(str, Enum):
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    TAX_ID = "tax_id"
    COMPANY_REGISTRATION = "company_registration"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    OTHER = "other"


class IdentityDocumentStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class VerificationMethod(str, Enum):
    MANUAL = "manual"
    OCR = "ocr"
    IDP = "idp"
    EMAIL = "email"
    SMS = "sms"
    TOTP = "totp"
    BIOMETRIC = "biometric"


class LeaveType(str, Enum):
    ANNUAL = "annual"
    SICK = "sick"
    PERSONAL = "personal"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    BEREAVEMENT = "bereavement"
    UNPAID = "unpaid"
    OTHER = "other"


class LeaveRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    WITHDRAWN = "withdrawn"


class IdentityProvider(str, Enum):
    INTERNAL = "internal"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    KEYCLOAK = "keycloak"
    CUSTOM_SAML = "custom_saml"
    CUSTOM_OIDC = "custom_oidc"


class CompanySettings(BaseModel):
    expense_approval_required: bool = True
    expense_max_amount_minor: int = 1_000_00
    expense_auto_approve_up_to_minor: int = 100_00
    reimbursement_processing_delay_days: int = 3
    require_receipt_above_minor: int = 25_00
    default_currency: str = "USD"
    fiscal_year_start_month: int = 1
    fiscal_year_start_day: int = 1
    timezone: str = "UTC"
    locale: str = "en-US"
    max_users: int = 1000
    allow_multi_currency: bool = True
    allow_carry_forward: bool = False
    carry_forward_expiry_days: int = 90
    approval_chain_required: bool = True
    max_approval_steps: int = 5
    audit_log_retention_days: int = 2555
    auto_lock_inactive_days: int = 90
    session_timeout_minutes: int = 60
    mfa_required: bool = False
    allowed_idp_providers: List[str] = Field(default_factory=lambda: ["internal"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Company(TimestampMixin, SoftDeleteMixin, VersionMixin):
    name: str = Field(..., min_length=1, max_length=512)
    legal_name: Optional[str] = None
    company_type: CompanyType = CompanyType.CORPORATION
    tax_id: Optional[str] = None
    registration_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    settings: CompanySettings = Field(default_factory=CompanySettings)
    is_active: bool = True
    is_verified: bool = False
    logo_url: Optional[str] = None
    domain: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.legal_name or self.name

    @property
    def full_address(self) -> Optional[str]:
        parts = [p for p in [self.address_line1, self.address_line2, self.city, self.state, self.postal_code, self.country] if p]
        return ", ".join(parts) if parts else None


class Membership(TimestampMixin, SoftDeleteMixin, VersionMixin):
    user_id: str = Field(..., min_length=1)
    company_id: str = Field(..., min_length=1)
    role: MembershipRole = MembershipRole.MEMBER
    is_active: bool = True
    is_default: bool = False
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_user_id: Optional[str] = None
    title: Optional[str] = None
    employee_id: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    permissions_override: Dict[str, bool] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_manager(self) -> bool:
        return self.role in (MembershipRole.OWNER, MembershipRole.ADMIN, MembershipRole.MANAGER)

    def has_permission(self, permission: str) -> bool:
        return self.permissions_override.get(permission, False)


class OrgUnit(TimestampMixin, SoftDeleteMixin, VersionMixin):
    company_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=256)
    unit_type: OrgUnitType = OrgUnitType.DEPARTMENT
    parent_id: Optional[str] = None
    manager_user_id: Optional[str] = None
    budget_minor: int = 0
    currency: str = "USD"
    is_active: bool = True
    external_id: Optional[str] = None
    cost_center_code: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def budget_formatted(self) -> str:
        return f"{self.budget_minor / 100:.2f} {self.currency}"


class FinanceGroup(TimestampMixin, SoftDeleteMixin, VersionMixin):
    company_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    is_active: bool = True
    approval_required: bool = True
    max_amount_minor: int = 0
    currency: str = "USD"
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FinanceGroupMember(TimestampMixin, SoftDeleteMixin, VersionMixin):
    group_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    company_id: str = Field(..., min_length=1)
    is_approver: bool = False
    is_observer: bool = False
    approval_order: int = 0
    max_approval_amount_minor: Optional[int] = None
    added_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def can_approve(self) -> bool:
        return self.is_approver and not self.is_observer

    def can_approve_amount(self, amount_minor: int) -> bool:
        if self.max_approval_amount_minor is None:
            return self.can_approve
        return self.can_approve and amount_minor <= self.max_approval_amount_minor


class PendingInvitation(TimestampMixin, VersionMixin):
    company_id: str = Field(..., min_length=1)
    email: EmailStr
    invited_by_user_id: str = Field(..., min_length=1)
    role: MembershipRole = MembershipRole.MEMBER
    is_accepted: bool = False
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    accepted_at: Optional[datetime] = None
    token: str = Field(..., min_length=32, max_length=256)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_accepted and not self.is_expired


class UserRegistration(TimestampMixin):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=128)
    password_hash: str = Field(..., min_length=1)
    verification_token: str = Field(..., min_length=32, max_length=256)
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    token_expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24))
    idp_provider: IdentityProvider = IdentityProvider.INTERNAL
    idp_user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_token_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.token_expires_at

    def verify(self) -> None:
        self.is_verified = True
        self.verified_at = datetime.now(timezone.utc)


class IdentityDocument(TimestampMixin, SoftDeleteMixin, VersionMixin):
    user_id: str = Field(..., min_length=1)
    company_id: str = Field(..., min_length=1)
    document_type: IdentityDocumentType
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    status: IdentityDocumentStatus = IdentityDocumentStatus.PENDING
    file_url: Optional[str] = None
    file_hash: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return date.today() > self.expires_at

    @property
    def is_verified(self) -> bool:
        return self.status == IdentityDocumentStatus.VERIFIED


class IdentityVerification(TimestampMixin, VersionMixin):
    user_id: str = Field(..., min_length=1)
    company_id: str = Field(..., min_length=1)
    method: VerificationMethod
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=5, ge=1)
    last_attempt_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    verification_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_locked(self) -> bool:
        return self.attempt_count >= self.max_attempts

    @property
    def remaining_attempts(self) -> int:
        return max(0, self.max_attempts - self.attempt_count)

    def record_attempt(self, success: bool, reason: Optional[str] = None) -> None:
        self.attempt_count += 1
        self.last_attempt_at = datetime.now(timezone.utc)
        if success:
            self.is_verified = True
            self.verified_at = datetime.now(timezone.utc)
            self.failure_reason = None
        else:
            self.failure_reason = reason

    def reset_attempts(self) -> None:
        self.attempt_count = 0
        self.last_attempt_at = None
        self.failure_reason = None


class LeaveEntitlement(TimestampMixin, SoftDeleteMixin, VersionMixin):
    user_id: str = Field(..., min_length=1)
    company_id: str = Field(..., min_length=1)
    leave_type: LeaveType
    fiscal_year: int
    total_days: float = Field(default=0.0, ge=0)
    used_days: float = Field(default=0.0, ge=0)
    pending_days: float = Field(default=0.0, ge=0)
    carried_forward_days: float = Field(default=0.0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def remaining_days(self) -> float:
        return self.total_days + self.carried_forward_days - self.used_days - self.pending_days

    @field_validator("used_days", "pending_days")
    @classmethod
    def days_not_exceed_total(cls, v: float, info: Any) -> float:
        return v

    @model_validator(mode="after")
    def validate_days(self) -> LeaveEntitlement:
        total = self.total_days + self.carried_forward_days
        consumed = self.used_days + self.pending_days
        if consumed > total + 0.01:
            raise ValueError(f"Used + pending days ({consumed}) exceeds total ({total})")
        return self


class LeaveRequest(TimestampMixin, SoftDeleteMixin, VersionMixin):
    user_id: str = Field(..., min_length=1)
    company_id: str = Field(..., min_length=1)
    leave_type: LeaveType
    status: LeaveRequestStatus = LeaveRequestStatus.PENDING
    start_date: date
    end_date: date
    total_days: float = Field(default=0.0, ge=0)
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    work_handover_to: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info: Any) -> date:
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must be on or after start_date")
        return v

    @property
    def is_approved(self) -> bool:
        return self.status == LeaveRequestStatus.APPROVED

    @property
    def is_pending(self) -> bool:
        return self.status == LeaveRequestStatus.PENDING

    def approve(self, approver_id: str) -> None:
        self.status = LeaveRequestStatus.APPROVED
        self.approved_by = approver_id
        self.approved_at = datetime.now(timezone.utc)

    def reject(self, approver_id: str, reason: str) -> None:
        self.status = LeaveRequestStatus.REJECTED
        self.approved_by = approver_id
        self.approved_at = datetime.now(timezone.utc)
        self.rejection_reason = reason

    def cancel(self) -> None:
        self.status = LeaveRequestStatus.CANCELLED

    def withdraw(self) -> None:
        self.status = LeaveRequestStatus.WITHDRAWN


class CurrentContext(BaseModel):
    user_id: str
    company_id: str
    membership_role: MembershipRole = MembershipRole.MEMBER
    membership_id: str
    is_impersonated: bool = False
    impersonated_by: Optional[str] = None
    permissions: Dict[str, bool] = Field(default_factory=dict)
    token_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.membership_role in (MembershipRole.OWNER, MembershipRole.ADMIN)

    @property
    def is_finance_admin(self) -> bool:
        return self.membership_role in (MembershipRole.FINANCE_ADMIN, MembershipRole.ADMIN, MembershipRole.OWNER)

    def has_permission(self, permission: str) -> bool:
        if self.is_admin:
            return True
        return self.permissions.get(permission, False)
