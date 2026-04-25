from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finance_platform.routes.deps import (
    get_company_id,
    paginate,
    resolve_company_context,
)

router = APIRouter()


@router.get("/system/health")
async def admin_system_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "up",
            "cache": "up",
            "storage": "up",
            "queue": "up",
        },
    }


@router.get("/system/config")
async def admin_system_config(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "app_name": "finance-platform",
        "version": "1.0.0",
        "environment": "production",
        "features": {
            "ocr": True,
            "watermark": True,
            "carry_forward": True,
            "amortization": True,
            "multi_company": True,
        },
    }


@router.post("/system/cache/clear")
async def admin_clear_cache(
    ctx: Any = Depends(resolve_company_context),
):
    return {"cleared": True, "cleared_at": datetime.utcnow().isoformat()}


@router.get("/audit-log")
async def admin_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.post("/month-end-close")
async def admin_month_end_close(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "status": "started",
        "fiscal_year": body.get("fiscal_year", "2026"),
        "period": body.get("period", "04"),
        "started_at": datetime.utcnow().isoformat(),
        "started_by": ctx.user_id,
    }


@router.get("/companies")
async def admin_list_all_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return paginate([], 0, page, page_size)


@router.post("/companies")
async def admin_create_company(
    body: Dict[str, Any],
):
    return {"id": "company-id", **body, "created": True}


@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return paginate([], 0, page, page_size)


@router.put("/users/{user_id}/role")
async def admin_update_user_role(
    user_id: str,
    body: Dict[str, Any],
):
    return {"id": user_id, "role": body.get("role"), "updated": True}


@router.post("/migrate")
async def admin_run_migration(
    body: Dict[str, Any],
):
    return {
        "status": "completed",
        "migration": body.get("migration", "latest"),
        "completed_at": datetime.utcnow().isoformat(),
    }
