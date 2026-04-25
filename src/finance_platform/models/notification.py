from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    NotificationType,
)


class NotificationPreference(BaseModel):
    user_id: str
    email: bool = True
    push: bool = True
    sms: bool = False
    in_app: bool = True
    digest_frequency: str = "instant"  # instant, daily, weekly
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    muted_types: list[NotificationType] = Field(default_factory=list)


class Notification(TimestampMixin):
    user_id: str
    notification_type: NotificationType
    title: str = Field(..., max_length=256)
    body: str = Field(..., max_length=4096)
    is_read: bool = False
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    sender_id: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=100)
    channel: str = "in_app"  # in_app, email, push, sms
    delivery_status: str = "pending"  # pending, sent, delivered, failed
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_read(self) -> None:
        self.is_read = True
        self.read_at = datetime.now()

    def mark_delivered(self) -> None:
        self.delivery_status = "delivered"
        self.delivered_at = datetime.now()
