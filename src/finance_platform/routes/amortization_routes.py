from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finance_platform.routes.deps import (
    get_company_id,
    paginate,
    resolve_company_context,
)

router = APIRouter()


@router.post("/schedules")
async def create_amortization_schedule(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "schedule-id", "status": "active", "company_id": ctx.company_id, **body}


@router.get("/schedules")
async def list_amortization_schedules(
    status: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    method: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/schedules/{schedule_id}")
async def get_amortization_schedule(
    schedule_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": schedule_id,
        "entity_type": "expense",
        "entity_id": "entity-1",
        "total_amount_minor": 1200000,
        "amortized_amount_minor": 200000,
        "remaining_amount_minor": 1000000,
        "method": "straight_line",
        "total_periods": 12,
        "completed_periods": 2,
        "status": "active",
        "company_id": ctx.company_id,
        "entries": [],
        "created_at": datetime.utcnow().isoformat(),
    }


@router.put("/schedules/{schedule_id}")
async def update_amortization_schedule(
    schedule_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": schedule_id, **body, "updated": True}


@router.delete("/schedules/{schedule_id}")
async def delete_amortization_schedule(
    schedule_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": schedule_id, "deleted": True}


@router.post("/schedules/{schedule_id}/entries")
async def create_amortization_entry(
    schedule_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "entry-id", "schedule_id": schedule_id, **body, "created": True}


@router.get("/schedules/{schedule_id}/entries")
async def list_amortization_entries(
    schedule_id: str,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/schedules/{schedule_id}/entries/{entry_id}")
async def get_amortization_entry(
    schedule_id: str,
    entry_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": entry_id,
        "schedule_id": schedule_id,
        "period_number": 1,
        "scheduled_amount_minor": 100000,
        "status": "pending",
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
    }


@router.post("/schedules/{schedule_id}/entries/{entry_id}/pay")
async def pay_amortization_entry(
    schedule_id: str,
    entry_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": entry_id,
        "schedule_id": schedule_id,
        "paid": True,
        "actual_amount_minor": body.get("amount_minor", 0),
        "paid_by": ctx.user_id,
        "paid_at": datetime.utcnow().isoformat(),
    }


@router.post("/schedules/{schedule_id}/entries/{entry_id}/defer")
async def defer_amortization_entry(
    schedule_id: str,
    entry_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": entry_id,
        "schedule_id": schedule_id,
        "deferred": True,
        "reason": body.get("reason", ""),
    }


@router.post("/schedules/{schedule_id}/entries/{entry_id}/waive")
async def waive_amortization_entry(
    schedule_id: str,
    entry_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": entry_id,
        "schedule_id": schedule_id,
        "waived": True,
        "reason": body.get("reason", ""),
    }


@router.post("/schedules/{schedule_id}/adjust")
async def adjust_amortization_schedule(
    schedule_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": schedule_id,
        "adjusted": True,
        "new_amount_minor": body.get("new_amount_minor", 0),
        "reason": body.get("reason", ""),
    }


@router.post("/schedules/{schedule_id}/complete")
async def complete_amortization_schedule(
    schedule_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": schedule_id, "status": "completed", "completed_at": datetime.utcnow().isoformat()}


@router.get("/schedules/{schedule_id}/forecast")
async def forecast_amortization_schedule(
    schedule_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": schedule_id,
        "projected_end_date": "2026-12-31",
        "projected_remaining_amount_minor": 1000000,
        "projected_periods_remaining": 10,
        "confidence_score": 0.95,
    }


@router.get("/summary")
async def get_amortization_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_active_schedules": 0,
        "total_completed_schedules": 0,
        "total_amount_minor": 0,
        "total_amortized_minor": 0,
        "total_remaining_minor": 0,
        "overall_progress_pct": 0.0,
        "company_id": ctx.company_id,
    }


@router.post("/bulk")
async def bulk_create_amortization(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "created": [],
        "failed": [],
        "total_requested": len(body.get("items", [])),
        "total_created": 0,
        "total_failed": 0,
    }
