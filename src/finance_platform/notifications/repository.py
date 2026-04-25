from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from finance_platform.notifications.models import (
    DeliveryStatus,
    NotificationChannel,
    NotificationEvent,
    NotificationPriority,
    NotificationTemplate,
)


class NotificationRepository:
    def __init__(self) -> None:
        self._templates: Dict[str, NotificationTemplate] = {}
        self._events: Dict[str, NotificationEvent] = {}
        self._user_events: Dict[str, List[str]] = {}
        self._user_unread_count: Dict[str, int] = {}

    def save_template(self, template: NotificationTemplate) -> NotificationTemplate:
        self._templates[template.name] = template
        return template

    def get_template(self, name: str) -> Optional[NotificationTemplate]:
        return self._templates.get(name)

    def get_template_by_type(self, notification_type: str) -> List[NotificationTemplate]:
        return [
            t for t in self._templates.values()
            if t.notification_type == notification_type and t.is_active
        ]

    def list_templates(self, active_only: bool = True) -> List[NotificationTemplate]:
        if active_only:
            return [t for t in self._templates.values() if t.is_active]
        return list(self._templates.values())

    def save_event(self, event: NotificationEvent) -> NotificationEvent:
        self._events[event.id] = event
        uid = event.user_id
        if uid not in self._user_events:
            self._user_events[uid] = []
        self._user_events[uid].append(event.id)
        if event.channel == NotificationChannel.IN_APP and event.delivery_status != DeliveryStatus.READ:
            self._user_unread_count[uid] = self._user_unread_count.get(uid, 0) + 1
        return event

    def get_event(self, event_id: str) -> Optional[NotificationEvent]:
        return self._events.get(event_id)

    def get_user_events(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        channel: Optional[NotificationChannel] = None,
        unread_only: bool = False,
    ) -> List[NotificationEvent]:
        event_ids = self._user_events.get(user_id, [])
        events: List[NotificationEvent] = []
        for eid in reversed(event_ids):
            ev = self._events[eid]
            if channel and ev.channel != channel:
                continue
            if unread_only and ev.delivery_status == DeliveryStatus.READ:
                continue
            events.append(ev)
            if len(events) >= offset + limit:
                break
        return events[offset:offset + limit]

    def get_unread_count(self, user_id: str) -> int:
        return self._user_unread_count.get(user_id, 0)

    def mark_read(self, event_id: str, user_id: str) -> Optional[NotificationEvent]:
        ev = self._events.get(event_id)
        if ev is None or ev.user_id != user_id:
            return None
        if ev.delivery_status != DeliveryStatus.READ:
            ev.mark_read()
            uid = ev.user_id
            current = self._user_unread_count.get(uid, 0)
            if current > 0:
                self._user_unread_count[uid] = current - 1
        return ev

    def mark_all_read(self, user_id: str) -> int:
        event_ids = self._user_events.get(user_id, [])
        count = 0
        for eid in event_ids:
            ev = self._events[eid]
            if ev.channel == NotificationChannel.IN_APP and ev.delivery_status != DeliveryStatus.READ:
                ev.mark_read()
                count += 1
        self._user_unread_count[user_id] = 0
        return count

    def get_pending_deliveries(
        self,
        channel: Optional[NotificationChannel] = None,
        limit: int = 100,
    ) -> List[NotificationEvent]:
        pending: List[NotificationEvent] = []
        for ev in self._events.values():
            if ev.delivery_status == DeliveryStatus.PENDING:
                if channel and ev.channel != channel:
                    continue
                pending.append(ev)
                if len(pending) >= limit:
                    break
        return pending

    def get_failed_deliveries(
        self,
        channel: Optional[NotificationChannel] = None,
        limit: int = 100,
    ) -> List[NotificationEvent]:
        failed: List[NotificationEvent] = []
        for ev in self._events.values():
            if ev.delivery_status == DeliveryStatus.FAILED and ev.should_retry():
                if channel and ev.channel != channel:
                    continue
                failed.append(ev)
                if len(failed) >= limit:
                    break
        return failed

    def delete_event(self, event_id: str) -> bool:
        ev = self._events.pop(event_id, None)
        if ev is None:
            return False
        uid = ev.user_id
        if uid in self._user_events:
            self._user_events[uid] = [eid for eid in self._user_events[uid] if eid != event_id]
        return True

    def count_events_since(
        self,
        user_id: str,
        since: datetime,
        notification_type: Optional[str] = None,
    ) -> int:
        event_ids = self._user_events.get(user_id, [])
        count = 0
        for eid in event_ids:
            ev = self._events[eid]
            if ev.created_at.replace(tzinfo=timezone.utc) >= since:
                if notification_type and ev.notification_type != notification_type:
                    continue
                count += 1
        return count
