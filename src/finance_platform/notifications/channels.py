from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.notifications.models import (
    NotificationChannel,
    NotificationEvent,
    NotificationPriority,
)


class ChannelRouter:
    def __init__(self) -> None:
        self._channels: Dict[str, NotificationChannel] = {}

    def register(self, name: str, channel: NotificationChannel) -> None:
        self._channels[name] = channel

    def route(self, event: NotificationEvent, preferred: List[str]) -> List[NotificationChannel]:
        channels: List[NotificationChannel] = []
        for pref in preferred:
            ch = self._channels.get(pref)
            if ch and ch == event.channel:
                channels.append(ch)
        if not channels:
            channels.append(event.channel)
        return channels


class InAppChannel:
    def deliver(self, event: NotificationEvent) -> bool:
        event.delivery_status = "delivered"  # type: ignore
        event.delivered_at = datetime.now(timezone.utc)
        return True


class EmailChannel:
    def deliver(self, event: NotificationEvent) -> bool:
        event.delivery_status = "sent"  # type: ignore
        event.delivered_at = datetime.now(timezone.utc)
        return True


class PushChannel:
    def deliver(self, event: NotificationEvent) -> bool:
        event.delivery_status = "sent"  # type: ignore
        event.delivered_at = datetime.now(timezone.utc)
        return True


class SmsChannel:
    def deliver(self, event: NotificationEvent) -> bool:
        event.delivery_status = "sent"  # type: ignore
        event.delivered_at = datetime.now(timezone.utc)
        return True
