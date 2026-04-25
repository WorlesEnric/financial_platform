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


@router.post("")
async def create_debt(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "debt-id", "status": "active", "company_id": ctx.company_id, **body}


@router.get("")
async def list_debts(
    status: Optional[str] = Query(None),
    creditor_id: Optional[str] = Query(None),
    debtor_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/{debt_id}")
async def get_debt(
    debt_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": debt_id,
        "creditor_id": "cred-1",
        "debtor_id": "debtor-1",
        "original_amount_minor": 500000,
        "outstanding_amount_minor": 500000,
        "status": "active",
        "incurred_date": "2026-01-15",
        "due_date": "2026-06-15",
        "company_id": ctx.company_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.put("/{debt_id}")
async def update_debt(
    debt_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": debt_id, **body, "updated": True}


@router.delete("/{debt_id}")
async def delete_debt(
    debt_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": debt_id, "deleted": True}


@router.post("/{debt_id}/payments")
async def add_debt_payment(
    debt_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "payment-id", "debt_id": debt_id, **body, "recorded_by": ctx.user_id, "created": True}


@router.get("/{debt_id}/payments")
async def list_debt_payments(
    debt_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.post("/{debt_id}/settle")
async def settle_debt(
    debt_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": debt_id,
        "settled": True,
        "settlement_method": body.get("method", "cash"),
        "settled_amount_minor": body.get("amount_minor", 0),
        "settled_by": ctx.user_id,
        "settled_at": datetime.utcnow().isoformat(),
    }


@router.post("/{debt_id}/write-off")
async def write_off_debt(
    debt_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": debt_id,
        "status": "written_off",
        "reason": body.get("reason", ""),
        "written_off_by": ctx.user_id,
        "written_off_at": datetime.utcnow().isoformat(),
    }


@router.get("/summary")
async def get_debt_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_active_debts": 0,
        "total_overdue_debts": 0,
        "total_outstanding_minor": 0,
        "total_overdue_minor": 0,
        "company_id": ctx.company_id,
    }
