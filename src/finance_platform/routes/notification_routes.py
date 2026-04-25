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


@router.get("")
async def list_notifications(
    notification_type: Optional[str] = Query(None),
    read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": notification_id,
        "type": "approval_requested",
        "title": "Approval Required",
        "message": "Expense #123 requires your approval",
        "read": False,
        "reference_type": "expense",
        "reference_id": "expense-123",
        "created_at": datetime.utcnow().isoformat(),
        "company_id": ctx.company_id,
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": notification_id, "read": True, "read_at": datetime.utcnow().isoformat()}


@router.post("/read-all")
async def mark_all_notifications_read(
    ctx: Any = Depends(resolve_company_context),
):
    return {"marked_read": True, "count": 0, "company_id": ctx.company_id}


@router.get("/unread-count")
async def get_unread_notification_count(
    ctx: Any = Depends(resolve_company_context),
):
    return {"unread_count": 0, "company_id": ctx.company_id}


@router.get("/preferences")
async def get_notification_preferences(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "email": True,
        "push": True,
        "sms": False,
        "weekly_digest": True,
        "channels": {
            "approval_requested": ["email", "push"],
            "payment_sent": ["email"],
            "debt_reminder": ["email", "sms"],
        },
    }


@router.put("/preferences")
async def update_notification_preferences(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {**body, "updated": True}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": notification_id, "deleted": True}
