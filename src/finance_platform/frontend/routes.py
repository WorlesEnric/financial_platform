# frontend/routes.py — Frontend page routes and API access helpers
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from finance_platform.auth.jwt import create_access_token, decode_token
from finance_platform.config import get_settings

router = APIRouter(tags=["frontend"])

_templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect root to login or dashboard."""
    return RedirectResponse(url="/ui/login")


@router.get("/ui/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login / token-entry page."""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX},
    )


@router.post("/ui/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    token: str = Form(""),
    user_id: str = Form("demo"),
    company_id: str = Form("default-company"),
    role: str = Form("employee"),
):
    """Accept a pasted JWT token or generate a demo token."""
    if not token.strip():
        # Generate a demo token for exploration
        token = create_access_token(
            user_id=user_id.strip() or "demo-user",
            company_id=company_id.strip() or "default-company",
            role=role.strip() or "employee",
            expires_delta=timedelta(hours=8),
        )
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "api_prefix": get_settings().API_PREFIX,
            "generated_token": token,
            "company_id": company_id,
        },
    )


@router.get("/ui/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX},
    )


@router.get("/ui/expenses", response_class=HTMLResponse)
async def expenses_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "expenses"},
    )


@router.get("/ui/approvals", response_class=HTMLResponse)
async def approvals_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "approvals"},
    )


@router.get("/ui/companies", response_class=HTMLResponse)
async def companies_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "companies"},
    )


@router.get("/ui/fx", response_class=HTMLResponse)
async def fx_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "fx"},
    )


@router.get("/ui/amortization", response_class=HTMLResponse)
async def amortization_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "amortization"},
    )


@router.get("/ui/settlements", response_class=HTMLResponse)
async def settlements_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "settlements"},
    )


@router.get("/ui/debts", response_class=HTMLResponse)
async def debts_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "debts"},
    )


@router.get("/ui/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "api_prefix": get_settings().API_PREFIX, "active_section": "audit"},
    )
