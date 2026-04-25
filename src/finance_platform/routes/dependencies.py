from __future__ import annotations

from typing import AsyncGenerator, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field


class CompanyContext(BaseModel):
    company_id: str
    user_id: str
    roles: list[str] = Field(default_factory=list)
    is_finance_admin: bool = False
    correlation_id: str = ""


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int


async def get_company_context(
    request: Request,
    x_company_id: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_roles: Optional[str] = Header(None),
) -> CompanyContext:
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "about:blank",
                "title": "Missing Company Context",
                "status": 400,
                "detail": "X-Company-Id header is required for this endpoint",
                "instance": str(request.url),
            },
        )
    roles = x_roles.split(",") if x_roles else []
    return CompanyContext(
        company_id=x_company_id,
        user_id=x_user_id or "",
        roles=roles,
        is_finance_admin="finance_admin" in roles,
        correlation_id=request.headers.get("X-Correlation-Id", ""),
    )


async def get_optional_company_context(
    request: Request,
    x_company_id: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_roles: Optional[str] = Header(None),
) -> Optional[CompanyContext]:
    if not x_company_id:
        return None
    roles = x_roles.split(",") if x_roles else []
    return CompanyContext(
        company_id=x_company_id,
        user_id=x_user_id or "",
        roles=roles,
        is_finance_admin="finance_admin" in roles,
        correlation_id=request.headers.get("X-Correlation-Id", ""),
    )


def require_role(role: str):
    async def role_checker(ctx: CompanyContext = Depends(get_company_context)) -> CompanyContext:
        if role not in ctx.roles and not ctx.is_finance_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "about:blank",
                    "title": "Insufficient Permissions",
                    "status": 403,
                    "detail": f"Role '{role}' is required",
                    "instance": "",
                },
            )
        return ctx
    return role_checker


async def get_pagination_params(
    page: int = 1,
    page_size: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
) -> PaginationParams:
    return PaginationParams(
        page=page,
        page_size=min(page_size, 200),
        sort_by=sort_by,
        sort_order=sort_order if sort_order in ("asc", "desc") else "desc",
    )


def paginate(items: list, total: int, params: PaginationParams) -> PaginatedResponse:
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=max(1, (total + params.page_size - 1) // params.page_size),
    )
