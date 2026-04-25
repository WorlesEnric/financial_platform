from __future__ import annotations

from typing import Dict, List, Optional

from finance_platform.notifications.models import (
    DigestFrequency,
    NotificationChannel,
    NotificationEvent,
    NotificationPriority,
)


class PreferenceManager:
    def __init__(self) -> None:
        self._user_channels: Dict[str, List[NotificationChannel]] = {}
        self._user_digest: Dict[str, DigestFrequency] = {}

    def set_channels(self, user_id: str, channels: List[NotificationChannel]) -> None:
        self._user_channels[user_id] = channels

    def get_channels(self, user_id: str) -> List[NotificationChannel]:
        return self._user_channels.get(user_id, [NotificationChannel.IN_APP])

    def set_digest_frequency(self, user_id: str, frequency: DigestFrequency) -> None:
        self._user_digest[user_id] = frequency

    def get_digest_frequency(self, user_id: str) -> DigestFrequency:
        return self._user_digest.get(user_id, DigestFrequency.INSTANT)

    def should_notify(self, user_id: str, event: NotificationEvent) -> bool:
        channels = self.get_channels(user_id)
        return event.channel in channels
