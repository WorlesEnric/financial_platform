from __future__ import annotations

import inspect
from typing import Any, Optional

import structlog


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    if name is None:
        frame = inspect.currentframe()
        if frame:
            frame = frame.f_back
        if frame:
            name = frame.f_globals.get("__name__", "finance_platform")
        else:
            name = "finance_platform"
    return structlog.get_logger(name)


class AuditLogger:
    def __init__(self, logger_name: str = "finance_platform.audit") -> None:
        self._logger = get_logger(logger_name)

    def log_event(
        self,
        event_type: str,
        entity_id: str,
        actor_id: str,
        company_id: str,
        entity_type: str = "unknown",
        details: dict[str, Any] | None = None,
        outcome: str = "success",
    ) -> None:
        self._logger.info(
            "audit_event",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            company_id=company_id,
            outcome=outcome,
            details=details or {},
        )

    def log_access(
        self,
        actor_id: str,
        resource: str,
        action: str,
        company_id: str,
        allowed: bool,
        reason: str | None = None,
    ) -> None:
        self._logger.info(
            "audit_access",
            actor_id=actor_id,
            resource=resource,
            action=action,
            company_id=company_id,
            allowed=allowed,
            reason=reason,
        )

    def log_change(
        self,
        entity_type: str,
        entity_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        actor_id: str,
        company_id: str,
    ) -> None:
        self._logger.info(
            "audit_change",
            entity_type=entity_type,
            entity_id=entity_id,
            field=field,
            old_value=str(old_value),
            new_value=str(new_value),
            actor_id=actor_id,
            company_id=company_id,
        )

    def log_financial_event(
        self,
        event_type: str,
        entity_id: str,
        amount_minor: int,
        currency: str,
        actor_id: str,
        company_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._logger.info(
            "audit_financial",
            event_type=event_type,
            entity_id=entity_id,
            amount_minor=amount_minor,
            currency=currency,
            actor_id=actor_id,
            company_id=company_id,
            details=details or {},
        )


class SecurityLogger:
    def __init__(self, logger_name: str = "finance_platform.security") -> None:
        self._logger = get_logger(logger_name)

    def log_login_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        company_id: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> None:
        self._logger.info(
            "security_login",
            username=username,
            ip_address=ip_address,
            success=success,
            company_id=company_id,
            failure_reason=failure_reason,
        )

    def log_authorization_failure(
        self,
        user_id: str,
        required_role: str,
        resource: str,
        company_id: Optional[str] = None,
    ) -> None:
        self._logger.warning(
            "security_auth_failure",
            user_id=user_id,
            required_role=required_role,
            resource=resource,
            company_id=company_id,
        )

    def log_permission_change(
        self,
        target_user_id: str,
        changed_by: str,
        role: str,
        action: str,
        company_id: str,
    ) -> None:
        self._logger.info(
            "security_permission_change",
            target_user_id=target_user_id,
            changed_by=changed_by,
            role=role,
            action=action,
            company_id=company_id,
        )

    def log_suspicious_activity(
        self,
        user_id: str,
        activity_type: str,
        description: str,
        ip_address: str,
        company_id: Optional[str] = None,
    ) -> None:
        self._logger.warning(
            "security_suspicious",
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            company_id=company_id,
        )

    def log_token_action(
        self,
        user_id: str,
        action: str,
        token_type: str,
        company_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        self._logger.info(
            "security_token",
            user_id=user_id,
            action=action,
            token_type=token_type,
            company_id=company_id,
            reason=reason,
        )
