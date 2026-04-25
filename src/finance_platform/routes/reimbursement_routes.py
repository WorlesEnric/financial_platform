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


@router.post("")
async def create_reimbursement(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "reimbursement-id", "status": "draft", "company_id": ctx.company_id, **body}


@router.get("")
async def list_reimbursements(
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/{reimbursement_id}")
async def get_reimbursement(
    reimbursement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": reimbursement_id,
        "user_id": ctx.user_id,
        "total_amount_minor": 150000,
        "currency": "USD",
        "status": "pending",
        "items": [],
        "company_id": ctx.company_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.put("/{reimbursement_id}")
async def update_reimbursement(
    reimbursement_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": reimbursement_id, **body, "updated": True}


@router.post("/{reimbursement_id}/submit")
async def submit_reimbursement(
    reimbursement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": reimbursement_id, "status": "submitted", "submitted_at": datetime.utcnow().isoformat()}


@router.post("/{reimbursement_id}/approve")
async def approve_reimbursement(
    reimbursement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": reimbursement_id, "status": "approved", "approved_by": ctx.user_id}


@router.post("/{reimbursement_id}/pay")
async def pay_reimbursement(
    reimbursement_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": reimbursement_id,
        "status": "paid",
        "paid_amount_minor": body.get("amount_minor", 0),
        "paid_by": ctx.user_id,
        "paid_at": datetime.utcnow().isoformat(),
    }


@router.post("/{reimbursement_id}/reject")
async def reject_reimbursement(
    reimbursement_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": reimbursement_id,
        "status": "rejected",
        "reason": body.get("reason", ""),
        "rejected_by": ctx.user_id,
    }


@router.post("/{reimbursement_id}/cancel")
async def cancel_reimbursement(
    reimbursement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": reimbursement_id, "status": "cancelled", "cancelled_by": ctx.user_id}


@router.get("/{reimbursement_id}/history")
async def get_reimbursement_history(
    reimbursement_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"items": [], "reimbursement_id": reimbursement_id}


@router.get("/summary")
async def get_reimbursement_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_pending": 0,
        "total_approved": 0,
        "total_paid": 0,
        "total_amount_pending_minor": 0,
        "total_amount_paid_minor": 0,
        "company_id": ctx.company_id,
    }
