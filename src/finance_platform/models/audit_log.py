from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditAction,
)


class AuditLog(TimestampMixin):
    entity_type: str
    entity_id: str
    action: AuditAction
    actor_id: str
    actor_name: Optional[str] = None
    changes: Dict[str, Any] = Field(default_factory=dict)
    previous_values: Dict[str, Any] = Field(default_factory=dict)
    new_values: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def change_summary(self) -> str:
        changed = list(self.changes.keys())
        if not changed:
            return f"{self.action.value} on {self.entity_type}"
        return f"{self.action.value} on {self.entity_type}: {', '.join(changed)}"
