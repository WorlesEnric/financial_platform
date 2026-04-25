from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.errors.exceptions import (
    NotFoundError,
    NotificationError,
    ValidationError,
)
from finance_platform.models.base import NotificationType
from finance_platform.models.notification import Notification, NotificationPreference


class NotificationService:
    def __init__(self) -> None:
        self._notifications: Dict[str, Notification] = {}
        self._preferences: Dict[str, NotificationPreference] = {}

    def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        priority: int = 0,
        channel: str = "in_app",
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        prefs = self.get_preferences(user_id)
        if notification_type in prefs.muted_types:
            raise NotificationError(f"Notification type {notification_type.value} is muted for user {user_id}")
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            reference_type=reference_type,
            reference_id=reference_id,
            sender_id=sender_id,
            priority=priority,
            channel=channel,
            action_url=action_url,
            metadata=metadata or {},
        )
        self._notifications[notification.id] = notification
        return notification

    def get_notification(self, notification_id: str) -> Notification:
        notification = self._notifications.get(notification_id)
        if not notification:
            raise NotFoundError(
                f"Notification {notification_id} not found",
                resource_type="Notification",
                resource_id=notification_id,
            )
        return notification

    def list_notifications(
        self,
        user_id: Optional[str] = None,
        notification_type: Optional[NotificationType] = None,
        is_read: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Notification]:
        results = list(self._notifications.values())
        if user_id:
            results = [n for n in results if n.user_id == user_id]
        if notification_type:
            results = [n for n in results if n.notification_type == notification_type]
        if is_read is not None:
            results = [n for n in results if n.is_read == is_read]
        results.sort(key=lambda n: n.created_at, reverse=True)
        return results[offset:offset + limit]

    def mark_as_read(self, notification_id: str) -> Notification:
        notification = self.get_notification(notification_id)
        notification.mark_read()
        return notification

    def mark_all_as_read(self, user_id: str) -> int:
        count = 0
        for notification in self._notifications.values():
            if notification.user_id == user_id and not notification.is_read:
                notification.mark_read()
                count += 1
        return count

    def mark_delivered(self, notification_id: str) -> Notification:
        notification = self.get_notification(notification_id)
        notification.mark_delivered()
        return notification

    def delete_notification(self, notification_id: str) -> None:
        notification = self.get_notification(notification_id)
        del self._notifications[notification_id]

    def set_preferences(self, user_id: str, **prefs: Any) -> NotificationPreference:
        existing = self._preferences.get(user_id)
        if existing:
            for key, value in prefs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return existing
        preference = NotificationPreference(user_id=user_id)
        for key, value in prefs.items():
            if hasattr(preference, key):
                setattr(preference, key, value)
        self._preferences[user_id] = preference
        return preference

    def get_preferences(self, user_id: str) -> NotificationPreference:
        prefs = self._preferences.get(user_id)
        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            self._preferences[user_id] = prefs
        return prefs

    def mute_notification_type(self, user_id: str, notification_type: NotificationType) -> NotificationPreference:
        prefs = self.get_preferences(user_id)
        if notification_type not in prefs.muted_types:
            prefs.muted_types.append(notification_type)
        return prefs

    def unmute_notification_type(self, user_id: str, notification_type: NotificationType) -> NotificationPreference:
        prefs = self.get_preferences(user_id)
        if notification_type in prefs.muted_types:
            prefs.muted_types.remove(notification_type)
        return prefs

    def send_bulk_notifications(
        self,
        user_ids: List[str],
        notification_type: NotificationType,
        title: str,
        body: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        sent_ids: List[str] = []
        for user_id in user_ids:
            try:
                notification = self.send_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    body=body,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    sender_id=sender_id,
                    metadata=metadata,
                )
                sent_ids.append(notification.id)
            except NotificationError:
                continue
        return sent_ids

    def get_unread_count(self, user_id: str) -> int:
        return sum(1 for n in self._notifications.values() if n.user_id == user_id and not n.is_read)

    def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        notifications = self._notifications.values()
        if user_id:
            notifications = [n for n in notifications if n.user_id == user_id]
        total = len(notifications)
        read = sum(1 for n in notifications if n.is_read)
        by_type: Dict[str, int] = {}
        for n in notifications:
            by_type[n.notification_type.value] = by_type.get(n.notification_type.value, 0) + 1
        return {
            "total": total,
            "read": read,
            "unread": total - read,
            "by_type": by_type,
        }
