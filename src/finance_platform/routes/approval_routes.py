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


@router.post("/chains")
async def create_approval_chain(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "chain-id", "status": "pending", "company_id": ctx.company_id, **body}


@router.get("/chains")
async def list_approval_chains(
    status: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    approver_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/chains/{chain_id}")
async def get_approval_chain(
    chain_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": chain_id,
        "entity_type": "expense",
        "entity_id": "expense-1",
        "status": "pending",
        "current_step": 1,
        "steps": [],
        "company_id": ctx.company_id,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.post("/chains/{chain_id}/decide")
async def decide_approval_step(
    chain_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": chain_id,
        "step_id": body.get("step_id", ""),
        "approved": body.get("approved", False),
        "decided_by": ctx.user_id,
        "decided_at": datetime.utcnow().isoformat(),
    }


@router.post("/chains/{chain_id}/escalate")
async def escalate_approval(
    chain_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": chain_id,
        "escalated": True,
        "reason": body.get("reason", ""),
        "escalated_by": ctx.user_id,
    }


@router.post("/chains/{chain_id}/recall")
async def recall_approval(
    chain_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": chain_id, "status": "recalled", "recalled_by": ctx.user_id}


@router.post("/delegations")
async def create_delegation(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "delegation-id", **body, "created_by": ctx.user_id, "active": True}


@router.get("/delegations")
async def list_delegations(
    delegator_id: Optional[str] = Query(None),
    active_only: bool = Query(True),
    ctx: Any = Depends(resolve_company_context),
):
    return {"items": []}


@router.delete("/delegations/{delegation_id}")
async def revoke_delegation(
    delegation_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": delegation_id, "revoked": True}


@router.get("/policies")
async def list_approval_policies(
    ctx: Any = Depends(resolve_company_context),
):
    return {"items": []}


@router.post("/policies")
async def create_approval_policy(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "policy-id", **body, "active": True}


@router.get("/pending")
async def list_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/stats")
async def get_approval_stats(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_pending": 0,
        "total_approved": 0,
        "total_rejected": 0,
        "total_escalated": 0,
        "average_approval_time_hours": 0.0,
        "company_id": ctx.company_id,
    }
