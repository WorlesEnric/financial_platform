from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, status
from pydantic import BaseModel

from finance_platform.auth.jwt import JWTBearer, get_current_user
from finance_platform.auth.rbac import CompanyContext, require_company_role
from finance_platform.errors.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)

UNSCOPED_ERROR_MSG = "company_id is required for this endpoint"


async def get_company_id(
    x_company_id: Optional[str] = Header(None),
) -> str:
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UNSCOPED_ERROR_MSG,
        )
    return x_company_id


async def get_optional_company_id(
    x_company_id: Optional[str] = Header(None),
) -> Optional[str]:
    return x_company_id


async def resolve_company_context(
    request: Request,
    company_id: str = Depends(get_company_id),
) -> CompanyContext:
    user = getattr(request.state, "user", None)
    if user is None:
        raise AuthenticationError("User not authenticated")
    return CompanyContext(
        company_id=company_id,
        user_id=user.get("id", "") if isinstance(user, dict) else str(user.id),
        role=user.get("role", "") if isinstance(user, dict) else getattr(user, "role", ""),
    )


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


def paginate(items: list[Any], total: int, page: int, page_size: int) -> PaginatedResponse:
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )


def generate_error_response(
    status_code: int,
    detail: str,
    error_type: str = "about:blank",
    instance: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    return {
        "type": error_type,
        "title": "error",
        "status": status_code,
        "detail": detail,
        "instance": instance or "",
        "timestamp": datetime.utcnow().isoformat(),
        "error_id": str(uuid4()),
        **extra,
    }


__all__ = [
    "get_company_id",
    "get_optional_company_id",
    "resolve_company_context",
    "PageParams",
    "PaginatedResponse",
    "paginate",
    "generate_error_response",
    "UNSCOPED_ERROR_MSG",
]
