from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel
from finance_platform.notifications.models import (
    DeliveryStatus,
    NotificationChannel,
    NotificationEvent,
    NotificationPriority,
    NotificationTemplate,
)


class DigestBuilder:
    def __init__(self) -> None:
        self._events: List[NotificationEvent] = []

    def add_event(self, event: NotificationEvent) -> None:
        self._events.append(event)

    def build_digest(self, user_id: str, channel: NotificationChannel) -> Dict[str, Any]:
        unread = [e for e in self._events if e.user_id == user_id and e.delivery_status != DeliveryStatus.READ]
        return {
            "user_id": user_id,
            "channel": channel.value,
            "total_events": len(unread),
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "body": e.body,
                    "notification_type": e.notification_type,
                    "created_at": e.created_at.isoformat(),
                }
                for e in unread[:50]
            ],
            "built_at": datetime.now(timezone.utc).isoformat(),
        }


class DigestJob(BaseModel):
    user_id: str
    channel: NotificationChannel
    frequency: str
    last_sent_at: Optional[datetime] = None
    next_send_at: datetime
    events_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
