"""Audit subpackage — re-export façade.

The build centralized audit logic under ``models/audit_log.py``,
``services/audit_service.py``, and ``routes/audit_routes.py``. The
original stub re-exported from non-existent siblings (``audit.models``,
``audit.service``, ``audit.routes``, ``audit.repository``,
``audit.schemas``). This file re-exports from the real central
locations. Symbols the stub claimed that were never shipped anywhere
(DomainEvent, DomainEventStatus, AuditAction, *Create/*Response
schemas, AuditRepository) are dropped. See ../../../problem.md.
"""

from finance_platform.models.audit_log import AuditLog
from finance_platform.services.audit_service import AuditService
from finance_platform.routes.audit_routes import router as audit_router

__all__ = [
    "AuditLog",
    "AuditService",
    "audit_router",
]
