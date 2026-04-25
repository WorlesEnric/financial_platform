from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PolicyScope(str, Enum):
    GLOBAL = "global"
    COMPANY = "company"
    DEPARTMENT = "department"
    DOCUMENT_TYPE = "document_type"
    USER = "user"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE = "require"
    WARN = "warn"
    LOG = "log"


@dataclass
class PolicyRule:
    id: str = ""
    name: str = ""
    description: str = ""
    action: PolicyAction = PolicyAction.ALLOW
    conditions: dict[str, str] = field(default_factory=dict)
    priority: int = 0
    active: bool = True


@dataclass
class WatermarkPolicy:
    id: str = ""
    name: str = ""
    description: str = ""
    scope: PolicyScope = PolicyScope.GLOBAL
    scope_id: str = ""
    watermark_types: list[str] = field(default_factory=lambda: [t.value for t in []])

    required_positions: list[str] = field(default_factory=list)
    min_opacity: float = 0.0
    max_opacity: float = 1.0
    require_verification: bool = False
    require_expiry: bool = False
    max_expiry_days: Optional[int] = None
    allowed_mime_types: list[str] = field(default_factory=list)
    disallowed_mime_types: list[str] = field(default_factory=list)
    max_watermarks_per_document: int = 10
    require_checksum: bool = True
    audit_on_apply: bool = True
    audit_on_verify: bool = True
    audit_on_revoke: bool = True
    rules: list[PolicyRule] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = field(default_factory=dict)

    def applies_to(self, company_id: str, department: str = "", document_type: str = "") -> bool:
        if not self.active:
            return False
        if self.scope == PolicyScope.GLOBAL:
            return True
        if self.scope == PolicyScope.COMPANY:
            return self.scope_id == company_id
        if self.scope == PolicyScope.DEPARTMENT:
            return self.scope_id == department
        if self.scope == PolicyScope.DOCUMENT_TYPE:
            return self.scope_id == document_type
        return False

    def is_type_allowed(self, watermark_type: str) -> bool:
        if not self.watermark_types:
            return True
        return watermark_type in self.watermark_types

    def is_position_allowed(self, position: str) -> bool:
        if not self.required_positions:
            return True
        return position in self.required_positions

    def is_mime_type_allowed(self, mime_type: str) -> bool:
        if self.disallowed_mime_types and mime_type in self.disallowed_mime_types:
            return False
        if self.allowed_mime_types:
            return mime_type in self.allowed_mime_types
        return True

    def evaluate_rules(self, context: dict[str, str]) -> list[tuple[PolicyRule, bool]]:
        results: list[tuple[PolicyRule, bool]] = []
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if not rule.active:
                continue
            matched = all(
                context.get(key) == value for key, value in rule.conditions.items()
            )
            results.append((rule, matched))
        return results


class WatermarkPolicyManager:
    def __init__(self) -> None:
        self._policies: dict[str, WatermarkPolicy] = {}
        self._default_policy = self._create_default_policy()

    def _create_default_policy(self) -> WatermarkPolicy:
        return WatermarkPolicy(
            id="default-global-policy",
            name="Default Global Policy",
            description="Default watermark policy applied to all companies",
            scope=PolicyScope.GLOBAL,
            min_opacity=0.2,
            max_opacity=1.0,
            require_verification=False,
            require_expiry=False,
            max_watermarks_per_document=10,
            require_checksum=True,
            audit_on_apply=True,
            audit_on_verify=True,
            audit_on_revoke=True,
            allowed_mime_types=[
                "application/pdf",
                "image/png",
                "image/jpeg",
                "image/tiff",
            ],
        )

    def add_policy(self, policy: WatermarkPolicy) -> WatermarkPolicy:
        policy.updated_at = datetime.now(timezone.utc)
        self._policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: str) -> Optional[WatermarkPolicy]:
        return self._policies.get(policy_id)

    def get_policy_or_default(self, policy_id: str) -> WatermarkPolicy:
        return self._policies.get(policy_id) or self._default_policy

    def get_applicable_policies(
        self,
        company_id: str,
        department: str = "",
        document_type: str = "",
    ) -> list[WatermarkPolicy]:
        applicable: list[WatermarkPolicy] = []
        for policy in self._policies.values():
            if policy.applies_to(company_id, department, document_type):
                applicable.append(policy)
        applicable.append(self._default_policy)
        return applicable

    def remove_policy(self, policy_id: str) -> bool:
        return self._policies.pop(policy_id, None) is not None

    def update_policy(self, policy_id: str, updates: dict) -> Optional[WatermarkPolicy]:
        policy = self._policies.get(policy_id)
        if policy is None:
            return None
        for key, value in updates.items():
            if hasattr(policy, key) and key not in ("id", "created_at"):
                setattr(policy, key, value)
        policy.updated_at = datetime.now(timezone.utc)
        return policy

    def list_policies(
        self,
        scope: Optional[PolicyScope] = None,
        active_only: bool = True,
    ) -> list[WatermarkPolicy]:
        results = list(self._policies.values())
        if scope is not None:
            results = [p for p in results if p.scope == scope]
        if active_only:
            results = [p for p in results if p.active]
        return results

    def validate_against_policies(
        self,
        watermark_type: str,
        position: str,
        mime_type: str,
        company_id: str,
        opacity: float = 0.5,
    ) -> list[str]:
        violations: list[str] = []
        policies = self.get_applicable_policies(company_id)
        for policy in policies:
            if not policy.is_type_allowed(watermark_type):
                violations.append(
                    f"Watermark type '{watermark_type}' not allowed by policy '{policy.name}'"
                )
            if not policy.is_position_allowed(position):
                violations.append(
                    f"Position '{position}' not allowed by policy '{policy.name}'"
                )
            if not policy.is_mime_type_allowed(mime_type):
                violations.append(
                    f"MIME type '{mime_type}' not allowed by policy '{policy.name}'"
                )
            if opacity < policy.min_opacity or opacity > policy.max_opacity:
                violations.append(
                    f"Opacity {opacity} outside allowed range "
                    f"[{policy.min_opacity}, {policy.max_opacity}] for policy '{policy.name}'"
                )
        return violations

    def get_default_policy(self) -> WatermarkPolicy:
        return self._default_policy
