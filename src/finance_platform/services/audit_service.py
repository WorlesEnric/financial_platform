from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.errors.exceptions import (
    NotFoundError,
    AuditError,
    AuditTrailError,
)
from finance_platform.models.audit_log import AuditLog
from finance_platform.models.base import AuditAction


class AuditService:
    def __init__(self) -> None:
        self._logs: Dict[str, AuditLog] = {}
        self._sequence: int = 0

    def _log(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        actor_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        previous_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        source: Optional[str] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor_id=actor_id,
            actor_name=actor_name,
            changes=changes or {},
            previous_values=previous_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            correlation_id=correlation_id,
            session_id=session_id,
            source=source,
            notes=notes,
            metadata=metadata or {},
        )
        self._logs[log.id] = log
        self._sequence += 1
        return log

    def log_create(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        new_values: Optional[Dict[str, Any]] = None,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.CREATE,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            new_values=new_values or {},
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
            source=source,
        )

    def log_update(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        changes: Dict[str, Any],
        previous_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.UPDATE,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            changes=changes,
            previous_values=previous_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def log_delete(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        previous_values: Optional[Dict[str, Any]] = None,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.DELETE,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            previous_values=previous_values or {},
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def log_approve(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        actor_name: Optional[str] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.APPROVE,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            notes=notes,
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def log_reject(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        reason: Optional[str] = None,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.REJECT,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            notes=reason,
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def log_submit(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.SUBMIT,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def log_pay(
        self,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        amount: Optional[float] = None,
        actor_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.PAY,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_name=actor_name,
            changes={"amount": amount} if amount is not None else {},
            ip_address=ip_address,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def log_login(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.LOGIN,
            entity_type="user",
            entity_id=user_id,
            actor_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            correlation_id=correlation_id,
            session_id=session_id,
            metadata=metadata,
        )

    def log_logout(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AuditLog:
        return self._log(
            action=AuditAction.LOGOUT,
            entity_type="user",
            entity_id=user_id,
            actor_id=user_id,
            ip_address=ip_address,
            request_id=request_id,
            session_id=session_id,
        )

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        results = [
            log
            for log in self._logs.values()
            if log.entity_type == entity_type and log.entity_id == entity_id
        ]
        results.sort(key=lambda l: l.created_at, reverse=True)
        return results[offset:offset + limit]

    def get_actor_history(
        self,
        actor_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        results = [
            log for log in self._logs.values() if log.actor_id == actor_id
        ]
        results.sort(key=lambda l: l.created_at, reverse=True)
        return results[offset:offset + limit]

    def get_timeline(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        results = list(self._logs.values())
        if entity_type:
            results = [l for l in results if l.entity_type == entity_type]
        if entity_id:
            results = [l for l in results if l.entity_id == entity_id]
        if actor_id:
            results = [l for l in results if l.actor_id == actor_id]
        if action:
            results = [l for l in results if l.action == action]
        if date_from:
            results = [l for l in results if l.created_at >= date_from]
        if date_to:
            results = [l for l in results if l.created_at <= date_to]
        results.sort(key=lambda l: l.created_at, reverse=True)
        return results[:limit]

    def verify_trail_integrity(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        logs = self.get_entity_history(entity_type, entity_id)
        if not logs:
            return {"verified": True, "checks": 0, "issues": []}
        issues: List[str] = []
        sorted_logs = sorted(logs, key=lambda l: l.created_at)
        for i in range(1, len(sorted_logs)):
            prev = sorted_logs[i - 1]
            curr = sorted_logs[i]
            if curr.created_at < prev.created_at:
                issues.append(
                    f"Timestamp anomaly between log {prev.id} and {curr.id}"
                )
        return {
            "verified": len(issues) == 0,
            "checks": len(logs),
            "issues": issues,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

    def get_statistics(
        self,
        entity_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        logs = list(self._logs.values())
        if entity_type:
            logs = [l for l in logs if l.entity_type == entity_type]
        if actor_id:
            logs = [l for l in logs if l.actor_id == actor_id]
        if date_from:
            logs = [l for l in logs if l.created_at >= date_from]
        if date_to:
            logs = [l for l in logs if l.created_at <= date_to]
        by_action: Dict[str, int] = {}
        by_entity: Dict[str, int] = {}
        for log in logs:
            by_action[log.action.value] = by_action.get(log.action.value, 0) + 1
            by_entity[log.entity_type] = by_entity.get(log.entity_type, 0) + 1
        return {
            "total_logs": len(logs),
            "by_action": by_action,
            "by_entity_type": by_entity,
            "unique_actors": len(set(l.actor_id for l in logs)),
        }
