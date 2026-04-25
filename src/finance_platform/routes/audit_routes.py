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


@router.get("/logs")
async def list_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": log_id,
        "action": "expense.submit",
        "entity_type": "expense",
        "entity_id": "expense-123",
        "user_id": ctx.user_id,
        "details": {"status": "submitted"},
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "created_at": datetime.utcnow().isoformat(),
        "company_id": ctx.company_id,
    }


@router.get("/events")
async def list_domain_events(
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/events/{event_id}")
async def get_domain_event(
    event_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": event_id,
        "event_type": "expense.submitted",
        "aggregate_type": "expense",
        "aggregate_id": "expense-123",
        "data": {"status": "submitted", "amount_minor": 150000},
        "status": "published",
        "published_at": datetime.utcnow().isoformat(),
        "company_id": ctx.company_id,
    }


@router.post("/events/{event_id}/retry")
async def retry_domain_event(
    event_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": event_id, "status": "queued", "retried": True, "retried_at": datetime.utcnow().isoformat()}


@router.get("/trail/{entity_type}/{entity_id}")
async def get_audit_trail(
    entity_type: str,
    entity_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entries": [],
        "company_id": ctx.company_id,
    }


@router.get("/summary")
async def get_audit_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_logs": 0,
        "total_events": 0,
        "failed_events": 0,
        "pending_events": 0,
        "company_id": ctx.company_id,
    }
