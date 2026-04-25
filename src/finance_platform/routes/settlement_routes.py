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


@router.post("/runs")
async def create_settlement_run(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "run-id", "status": "pending", "company_id": ctx.company_id, **body}


@router.get("/runs")
async def list_settlement_runs(
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/runs/{run_id}")
async def get_settlement_run(
    run_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": run_id,
        "run_date": "2026-04-24",
        "total_settled_minor": 0,
        "status": "pending",
        "settlements": [],
        "company_id": ctx.company_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.post("/runs/{run_id}/execute")
async def execute_settlement_run(
    run_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": run_id,
        "status": "processing",
        "started_at": datetime.utcnow().isoformat(),
        "started_by": ctx.user_id,
    }


@router.post("/runs/{run_id}/complete")
async def complete_settlement_run(
    run_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": run_id,
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "completed_by": ctx.user_id,
    }


@router.post("/runs/{run_id}/reverse")
async def reverse_settlement_run(
    run_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": run_id,
        "status": "reversed",
        "reason": body.get("reason", ""),
        "reversed_by": ctx.user_id,
        "reversed_at": datetime.utcnow().isoformat(),
    }


@router.get("/settlements")
async def list_settlements(
    status: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/settlements/{settlement_id}")
async def get_settlement(
    settlement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": settlement_id,
        "entity_type": "expense",
        "entity_id": "expense-1",
        "total_amount_minor": 100000,
        "settled_amount_minor": 0,
        "remaining_amount_minor": 100000,
        "status": "pending",
        "priority": "normal",
        "company_id": ctx.company_id,
    }


@router.post("/settlements/{settlement_id}/allocate")
async def allocate_settlement(
    settlement_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": settlement_id,
        "allocated": True,
        "allocated_amount_minor": body.get("amount_minor", 0),
        "allocated_by": ctx.user_id,
    }


@router.post("/settlements/{settlement_id}/approve")
async def approve_settlement(
    settlement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": settlement_id,
        "status": "approved",
        "approved_by": ctx.user_id,
        "approved_at": datetime.utcnow().isoformat(),
    }


@router.delete("/settlements/{settlement_id}")
async def remove_settlement(
    settlement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": settlement_id, "removed": True}


@router.get("/summary")
async def get_settlement_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "pending_settlements": 0,
        "completed_settlements": 0,
        "total_pending_amount_minor": 0,
        "total_settled_amount_minor": 0,
        "company_id": ctx.company_id,
    }
