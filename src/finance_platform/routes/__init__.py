from __future__ import annotations

from typing import List

from fastapi import APIRouter, FastAPI

from finance_platform.routes.admin_routes import router as admin_router
from finance_platform.routes.amortization_routes import router as amortization_router
from finance_platform.routes.approval_routes import router as approval_router
from finance_platform.routes.audit_routes import router as audit_router
from finance_platform.routes.carry_forward_routes import router as carry_forward_router
from finance_platform.routes.debt_routes import router as debt_router
from finance_platform.routes.expense_routes import router as expense_router
from finance_platform.routes.frontend_routes import router as frontend_router
from finance_platform.routes.fx_routes import router as fx_router
from finance_platform.routes.health_routes import router as health_router
from finance_platform.routes.identity_routes import router as identity_router
from finance_platform.routes.notification_routes import router as notification_router
from finance_platform.routes.ocr_routes import router as ocr_router
from finance_platform.routes.reimbursement_routes import router as reimbursement_router
from finance_platform.routes.settlement_routes import router as settlement_router
from finance_platform.routes.watermark_routes import router as watermark_router

_router_registry: List[tuple] = []


def register_router(router: APIRouter, prefix: str = "", tags: List[str] | None = None):
    _router_registry.append((router, prefix, tags or []))


def mount_all_routes(app: FastAPI) -> None:
    for router, prefix, tags in _router_registry:
        app.include_router(router, prefix=prefix, tags=tags)


def init_routes() -> None:
    # Frontend routes — registered first so "/" serves the dashboard
    register_router(frontend_router, prefix="", tags=["frontend"])

    # API routes
    register_router(health_router, prefix="/health", tags=["health"])
    register_router(identity_router, prefix="/api/v1/identity", tags=["identity"])
    register_router(expense_router, prefix="/api/v1/expenses", tags=["expenses"])
    register_router(amortization_router, prefix="/api/v1/amortization", tags=["amortization"])
    register_router(approval_router, prefix="/api/v1/approvals", tags=["approvals"])
    register_router(settlement_router, prefix="/api/v1/settlements", tags=["settlements"])
    register_router(debt_router, prefix="/api/v1/debts", tags=["debts"])
    register_router(carry_forward_router, prefix="/api/v1/carry-forward", tags=["carry_forward"])
    register_router(fx_router, prefix="/api/v1/fx", tags=["fx"])
    register_router(ocr_router, prefix="/api/v1/ocr", tags=["ocr"])
    register_router(watermark_router, prefix="/api/v1/watermark", tags=["watermark"])
    register_router(notification_router, prefix="/api/v1/notifications", tags=["notifications"])
    register_router(audit_router, prefix="/api/v1/audit", tags=["audit"])
    register_router(reimbursement_router, prefix="/api/v1/reimbursements", tags=["reimbursements"])
    register_router(admin_router, prefix="/api/v1/admin", tags=["admin"])


__all__ = [
    "_router_registry",
    "register_router",
    "mount_all_routes",
    "init_routes",
]
