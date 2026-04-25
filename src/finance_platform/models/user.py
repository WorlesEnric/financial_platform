from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, EmailStr

from finance_platform.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, VersionMixin


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    FINANCE = "finance"
    ADMIN = "admin"
    APPROVER = "approver"
    AUDITOR = "auditor"
    SYSTEM = "system"


class UserProfile(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=256)
    department: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en-US"


class UserSettings(BaseModel):
    notification_email: bool = True
    notification_push: bool = True
    notification_sms: bool = False
    weekly_digest: bool = True
    expense_auto_submit: bool = False
    default_currency: str = "USD"
    max_approval_amount: Optional[float] = None
    two_factor_enabled: bool = False
    language: str = "en"


class User(TimestampMixin, SoftDeleteMixin, VersionMixin):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=128)
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True
    is_verified: bool = False
    profile: UserProfile = Field(default_factory=UserProfile)
    settings: UserSettings = Field(default_factory=UserSettings)
    external_id: Optional[str] = None
    idp_provider: Optional[str] = None
    last_login_at: Optional[datetime] = None
    approved_spending_limit: float = 0.0
    roles_override: List[UserRole] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def has_role(self, role: UserRole) -> bool:
        return self.role == role or role in self.roles_override

    def can_approve_amount(self, amount: float) -> bool:
        if self.settings.max_approval_amount is None:
            return True
        return amount <= self.settings.max_approval_amount

    @property
    def display_name(self) -> str:
        return self.profile.full_name or self.username

    @property
    def is_manager(self) -> bool:
        return self.role in (UserRole.MANAGER, UserRole.ADMIN)
