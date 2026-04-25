from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.notifications.channels import ChannelRouter, InAppChannel, EmailChannel
from finance_platform.notifications.models import (
    DeliveryStatus,
    NotificationChannel,
    NotificationEvent,
    NotificationPriority,
    NotificationTemplate,
    TemplateVariable,
)
from finance_platform.notifications.repository import NotificationRepository
from finance_platform.notifications.templates import TemplateEngine


class NotificationService:
    def __init__(
        self,
        repository: Optional[NotificationRepository] = None,
        template_engine: Optional[TemplateEngine] = None,
        channel_router: Optional[ChannelRouter] = None,
    ) -> None:
        self._repository = repository or NotificationRepository()
        self._template_engine = template_engine or TemplateEngine()
        self._channel_router = channel_router or ChannelRouter()
        self._in_app = InAppChannel()
        self._email = EmailChannel()

    def send_notification(
        self,
        user_id: str,
        notification_type: str,
        template_name: str,
        variables: Dict[str, str],
        channel: NotificationChannel = NotificationChannel.IN_APP,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        company_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
    ) -> NotificationEvent:
        template = self._template_engine.render(template_name, variables)
        event = NotificationEvent(
            user_id=user_id,
            notification_type=notification_type,
            template_name=template_name,
            channel=channel,
            priority=priority,
            title=template.get("title", ""),
            body=template.get("body", ""),
            variables=variables,
            company_id=company_id,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self._repository.save_event(event)
        return event

    def deliver(self, event: NotificationEvent) -> bool:
        if event.channel == NotificationChannel.IN_APP:
            return self._in_app.deliver(event)
        elif event.channel == NotificationChannel.EMAIL:
            return self._email.deliver(event)
        return False

    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> List[NotificationEvent]:
        return self._repository.get_user_events(
            user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
        )

    def mark_read(self, event_id: str, user_id: str) -> Optional[NotificationEvent]:
        return self._repository.mark_read(event_id, user_id)

    def mark_all_read(self, user_id: str) -> int:
        return self._repository.mark_all_read(user_id)

    def get_unread_count(self, user_id: str) -> int:
        return self._repository.get_unread_count(user_id)

    def send_month_end_reminder(
        self,
        user_id: str,
        company_id: str,
        pending_count: int,
    ) -> NotificationEvent:
        return self.send_notification(
            user_id=user_id,
            notification_type="month_end_reminder",
            template_name="month_end_reminder",
            variables={"pending_count": str(pending_count), "company_id": company_id},
            priority=NotificationPriority.HIGH,
            company_id=company_id,
        )

    def send_approval_result(
        self,
        user_id: str,
        expense_id: str,
        result: str,
        reviewer_name: str,
        company_id: str,
    ) -> NotificationEvent:
        return self.send_notification(
            user_id=user_id,
            notification_type="approval_result",
            template_name="approval_result",
            variables={
                "expense_id": expense_id,
                "result": result,
                "reviewer_name": reviewer_name,
            },
            company_id=company_id,
            reference_type="expense",
            reference_id=expense_id,
        )

    def send_discrepancy_alert(
        self,
        user_id: str,
        expense_id: str,
        discrepancy_detail: str,
        company_id: str,
    ) -> NotificationEvent:
        return self.send_notification(
            user_id=user_id,
            notification_type="discrepancy",
            template_name="discrepancy_alert",
            variables={
                "expense_id": expense_id,
                "discrepancy_detail": discrepancy_detail,
            },
            priority=NotificationPriority.URGENT,
            company_id=company_id,
            reference_type="expense",
            reference_id=expense_id,
        )

    def send_high_priority_debt_alert(
        self,
        user_id: str,
        debt_amount: str,
        counterparty: str,
        company_id: str,
    ) -> NotificationEvent:
        return self.send_notification(
            user_id=user_id,
            notification_type="high_priority_debt",
            template_name="high_priority_debt",
            variables={
                "debt_amount": debt_amount,
                "counterparty": counterparty,
            },
            priority=NotificationPriority.URGENT,
            company_id=company_id,
        )
