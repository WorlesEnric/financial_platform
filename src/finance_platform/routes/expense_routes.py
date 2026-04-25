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
async def create_expense(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "expense-id", "status": "draft", "company_id": ctx.company_id, **body}


@router.get("")
async def list_expenses(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/{expense_id}")
async def get_expense(
    expense_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": expense_id,
        "title": "Office Supplies",
        "amount_minor": 150000,
        "currency": "USD",
        "category": "office_supplies",
        "status": "submitted",
        "approval_state": "pending",
        "company_id": ctx.company_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.put("/{expense_id}")
async def update_expense(
    expense_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": expense_id, **body, "updated": True}


@router.post("/{expense_id}/submit")
async def submit_expense(
    expense_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": expense_id, "status": "submitted", "submitted_at": datetime.utcnow().isoformat()}


@router.post("/{expense_id}/approve")
async def approve_expense(
    expense_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": expense_id, "status": "approved", "approved_by": ctx.user_id}


@router.post("/{expense_id}/reject")
async def reject_expense(
    expense_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": expense_id,
        "status": "rejected",
        "reason": body.get("reason", ""),
        "rejected_by": ctx.user_id,
    }


@router.post("/{expense_id}/void")
async def void_expense(
    expense_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": expense_id,
        "status": "voided",
        "reason": body.get("reason", ""),
        "voided_by": ctx.user_id,
        "requires_original_reviewer": True,
    }


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": expense_id, "deleted": True}


@router.get("/{expense_id}/attachments")
async def list_expense_attachments(
    expense_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"items": [], "expense_id": expense_id}


@router.post("/{expense_id}/attachments")
async def upload_expense_attachment(
    expense_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "attachment-id", "expense_id": expense_id, "filename": body.get("filename", ""), "uploaded": True}


@router.get("/{expense_id}/line-items")
async def list_expense_line_items(
    expense_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"items": [], "expense_id": expense_id}


@router.post("/{expense_id}/line-items")
async def add_expense_line_item(
    expense_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "line-item-id", "expense_id": expense_id, **body, "created": True}


@router.get("/summary")
async def get_expense_summary(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_expenses": 0,
        "total_amount_minor": 0,
        "pending_count": 0,
        "approved_count": 0,
        "rejected_count": 0,
        "company_id": ctx.company_id,
    }
