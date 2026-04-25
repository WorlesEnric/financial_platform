from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from finance_platform.routes.dependencies import (
    CompanyContext,
    get_company_context,
    get_optional_company_context,
    get_pagination_params,
    paginate,
    PaginationParams,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str
    company_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_id: str
    roles: list[str]


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    company_id: str
    role: str = "employee"


class UserInfoResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    roles: list[str]
    company_id: str
    is_active: bool


from pydantic import BaseModel, Field


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    ctx: Optional[CompanyContext] = Depends(get_optional_company_context),
):
    company_id = body.company_id or (ctx.company_id if ctx else None)
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "about:blank",
                "title": "Missing Company",
                "status": 400,
                "detail": "company_id is required",
                "instance": str(request.url),
            },
        )
    from finance_platform.auth.jwt import create_access_token

    token = create_access_token(
        data={"sub": body.username, "company_id": company_id, "roles": ["employee"]},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=token,
        expires_in=86400,
        refresh_token=token,
        user_id=body.username,
        roles=["employee"],
    )


@router.post("/token", response_model=TokenResponse)
async def token(
    request: Request,
    body: RefreshRequest,
    ctx: Optional[CompanyContext] = Depends(get_optional_company_context),
):
    from finance_platform.auth.jwt import create_access_token, decode_token

    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    username = payload.get("sub", "")
    company_id = payload.get("company_id", "")
    roles = payload.get("roles", ["employee"])
    new_token = create_access_token(
        data={"sub": username, "company_id": company_id, "roles": roles},
        expires_delta=timedelta(hours=24),
    )
    return TokenResponse(
        access_token=new_token,
        expires_in=86400,
        refresh_token=new_token,
        user_id=username,
        roles=roles,
    )


@router.post("/register", response_model=UserInfoResponse, status_code=201)
async def register(
    request: Request,
    body: RegisterRequest,
    ctx: CompanyContext = Depends(get_company_context),
):
    return UserInfoResponse(
        id=body.username,
        username=body.username,
        email=body.email,
        full_name=body.full_name,
        roles=[body.role],
        company_id=body.company_id,
        is_active=True,
    )


@router.get("/me", response_model=UserInfoResponse)
async def me(ctx: CompanyContext = Depends(get_company_context)):
    return UserInfoResponse(
        id=ctx.user_id,
        username=ctx.user_id,
        email=f"{ctx.user_id}@example.com",
        full_name=ctx.user_id,
        roles=ctx.roles,
        company_id=ctx.company_id,
        is_active=True,
    )
