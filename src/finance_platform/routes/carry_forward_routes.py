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


@router.get("/buckets")
async def list_carry_forward_buckets(
    fiscal_year: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.post("/buckets")
async def create_carry_forward_bucket(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "bucket-id", "status": "active", "company_id": ctx.company_id, **body}


@router.get("/buckets/{bucket_id}")
async def get_carry_forward_bucket(
    bucket_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": bucket_id,
        "fiscal_year": "2026",
        "source_year": "2025",
        "total_amount_minor": 1000000,
        "remaining_amount_minor": 1000000,
        "status": "active",
        "entries": [],
        "company_id": ctx.company_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.put("/buckets/{bucket_id}")
async def update_carry_forward_bucket(
    bucket_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": bucket_id, **body, "updated": True}


@router.post("/buckets/{bucket_id}/execute")
async def execute_carry_forward(
    bucket_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": bucket_id,
        "executed": True,
        "status": "completed",
        "executed_by": ctx.user_id,
        "executed_at": datetime.utcnow().isoformat(),
        "priority": "HIGH",
        "approval_skipped": True,
        "amortization_target": "PENDING_AMORTIZATION",
    }


@router.post("/buckets/{bucket_id}/entries")
async def add_carry_forward_entry(
    bucket_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "entry-id", "bucket_id": bucket_id, **body, "created": True}


@router.get("/buckets/{bucket_id}/entries")
async def list_carry_forward_entries(
    bucket_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/summary")
async def get_carry_forward_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_buckets": 0,
        "active_buckets": 0,
        "total_amount_minor": 0,
        "total_remaining_minor": 0,
        "company_id": ctx.company_id,
    }
