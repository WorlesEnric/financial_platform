from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finance_platform.routes.deps import (
    get_company_id,
    paginate,
    resolve_company_context,
)

router = APIRouter()


@router.post("/companies")
async def create_company(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "company-id", "name": body.get("name"), "status": "created"}


@router.get("/companies")
async def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/companies/{company_id}")
async def get_company(
    company_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": company_id,
        "name": "Example Corp",
        "legal_name": "Example Corp Ltd",
        "tax_id": "TAX-001",
        "currency": "USD",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z",
    }


@router.put("/companies/{company_id}")
async def update_company(
    company_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": company_id, **body, "updated": True}


@router.delete("/companies/{company_id}")
async def delete_company(
    company_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": company_id, "deleted": True}


@router.get("/companies/{company_id}/members")
async def list_company_members(
    company_id: str,
    role: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.post("/companies/{company_id}/members")
async def add_company_member(
    company_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"company_id": company_id, "user_id": body.get("user_id"), "role": body.get("role"), "status": "added"}


@router.delete("/companies/{company_id}/members/{user_id}")
async def remove_company_member(
    company_id: str,
    user_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"company_id": company_id, "user_id": user_id, "removed": True}


@router.get("/companies/{company_id}/roles")
async def list_company_roles(
    company_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "roles": [
            {"name": "admin", "permissions": ["*"]},
            {"name": "finance_manager", "permissions": ["approve", "settle", "view_all"]},
            {"name": "finance_reviewer", "permissions": ["approve", "view_all"]},
            {"name": "manager", "permissions": ["approve_dept", "view_dept"]},
            {"name": "employee", "permissions": ["submit", "view_own"]},
        ]
    }


@router.get("/users/me")
async def get_current_user_profile(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": ctx.user_id,
        "email": "user@example.com",
        "username": "jdoe",
        "role": ctx.role,
        "is_active": True,
    }


@router.put("/users/me")
async def update_current_user_profile(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": ctx.user_id, **body, "updated": True}


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": user_id,
        "email": "user@example.com",
        "username": "jdoe",
        "is_active": True,
    }
