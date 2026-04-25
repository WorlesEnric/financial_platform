from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel, TimestampMixin


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationPriority(int, Enum):
    LOW = 0
    NORMAL = 25
    HIGH = 50
    URGENT = 75
    CRITICAL = 100


class DigestFrequency(str, Enum):
    INSTANT = "instant"
    DAILY = "daily"
    WEEKLY = "weekly"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    CANCELLED = "cancelled"


class TemplateVariable(BaseModel):
    key: str
    label: str
    required: bool = True
    default_value: Optional[str] = None
    description: Optional[str] = None


class ChannelConfig(BaseModel):
    channel: NotificationChannel
    enabled: bool = True
    template_id: Optional[str] = None
    priority_threshold: NotificationPriority = NotificationPriority.NORMAL
    retry_count: int = 3
    retry_delay_seconds: int = 60
    throttle_per_minute: int = 0


class NotificationTemplate(TimestampMixin):
    name: str
    description: Optional[str] = None
    notification_type: str
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    title_template: str
    body_template: str
    variables: List[TemplateVariable] = Field(default_factory=list)
    default_priority: NotificationPriority = NotificationPriority.NORMAL
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationEvent(TimestampMixin):
    user_id: str
    notification_type: str
    template_name: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    body: str
    variables: Dict[str, str] = Field(default_factory=dict)
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    sender_id: Optional[str] = None
    company_id: Optional[str] = None
    correlation_id: Optional[str] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_delivered(self) -> None:
        self.delivery_status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.now(timezone.utc)

    def mark_read(self) -> None:
        self.delivery_status = DeliveryStatus.READ
        self.read_at = datetime.now(timezone.utc)

    def mark_failed(self, reason: str) -> None:
        self.delivery_status = DeliveryStatus.FAILED
        self.failure_reason = reason

    def should_retry(self, max_retries: int = 3) -> bool:
        return (
            self.delivery_status == DeliveryStatus.FAILED
            and self.retry_count < max_retries
        )
