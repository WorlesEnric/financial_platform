from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from finance_platform.routes.deps import (
    get_company_id,
    get_optional_company_id,
    resolve_company_context,
)

router = APIRouter()

# Template directory is resolved relative to the package install location.
# In development (pip install -e .) this is src/finance_platform/templates/.
templates = Jinja2Templates(directory="src/finance_platform/templates")


def _render(request: Request, template_name: str, context: Dict[str, Any] | None = None) -> HTMLResponse:
    """Render a Jinja2 template with standard context injected."""
    ctx = dict(context or {})
    ctx.setdefault("current_company", None)
    ctx.setdefault("request", request)
    ctx.setdefault("active_page", "")
    return templates.TemplateResponse(request, template_name, ctx)


def _render_partial(request: Request, template_name: str, context: Dict[str, Any] | None = None) -> HTMLResponse:
    """Render a Jinja2 partial template (no base layout extension)."""
    ctx = dict(context or {})
    ctx.setdefault("current_company", None)
    ctx.setdefault("request", request)
    return templates.TemplateResponse(request, template_name, ctx)


# ── Dashboard ────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return _render(request, "dashboard.html", {"active_page": "dashboard"})


@router.get("/dashboard/stats", response_class=HTMLResponse)
async def dashboard_stats(
    request: Request,
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """HTMX partial: dashboard summary statistics."""
    stats = {
        "total_expenses": 0,
        "total_amount_display": "$0.00",
        "pending_approvals": 0,
        "pending_settlements": 0,
        "company_scoped": bool(company_id),
    }
    return _render_partial(request, "partials/stats.html", {"stats": stats})


@router.get("/select-company", response_class=HTMLResponse)
async def select_company_form(request: Request):
    """Company selection dialog (HTMX partial)."""
    html = """<div id="company-options" class="company-dropdown">
    <p class="subtitle">Set <code>X-Company-Id</code> header to scope requests. The backend resolves company context per request.</p>
</div>"""
    return HTMLResponse(html)


# ── Expenses ─────────────────────────────────────────────────────────────

@router.get("/expenses", response_class=HTMLResponse)
async def expenses_page(
    request: Request,
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """Serve the expenses list page or HTMX partial table."""
    if request.headers.get("HX-Request"):
        return await _expenses_table_partial(request, search, status_filter, page, page_size, company_id)
    return _render(request, "expenses/list.html", {"active_page": "expenses"})


async def _expenses_table_partial(
    request: Request,
    search: Optional[str],
    status_filter: Optional[str],
    page: int,
    page_size: int,
    company_id: Optional[str],
) -> HTMLResponse:
    """HTMX partial: expense table rows via Jinja2 template."""
    if not company_id:
        return _render_partial(request, "partials/empty_company.html", {
            "message": "No company context available.",
        })

    expenses = [
        {"id": "exp-001", "title": "Office Supplies - Q1", "amount_display": "$1,500.00",
         "status": "submitted", "category": "office_supplies", "created_at": "2026-05-01"},
        {"id": "exp-002", "title": "Travel - Client Visit", "amount_display": "$3,200.00",
         "status": "approved", "category": "travel", "created_at": "2026-04-28"},
        {"id": "exp-003", "title": "Software Licenses", "amount_display": "$899.00",
         "status": "draft", "category": "software", "created_at": "2026-04-25"},
    ]
    return _render_partial(request, "partials/expenses_table.html", {"expenses": expenses})


@router.get("/expenses/recent", response_class=HTMLResponse)
async def expenses_recent(
    request: Request,
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """HTMX partial: recent expenses for dashboard card."""
    if not company_id:
        return _render_partial(request, "partials/empty_state.html", {
            "message": "Select a company to view recent expenses.",
        })
    expenses = [
        {"id": "exp-001", "title": "Office Supplies", "amount": "$1,500.00", "status": "submitted"},
        {"id": "exp-002", "title": "Travel", "amount": "$3,200.00", "status": "approved"},
        {"id": "exp-003", "title": "Software", "amount": "$899.00", "status": "draft"},
    ]
    return _render_partial(request, "partials/expenses_recent.html", {"expenses": expenses})


@router.get("/expenses/new", response_class=HTMLResponse)
async def expense_create_form(request: Request):
    """Render the new expense form."""
    return _render(request, "expenses/list.html", {"active_page": "expenses", "show_create_form": True})


@router.get("/expenses/{expense_id}", response_class=HTMLResponse)
async def expense_detail_page(request: Request, expense_id: str):
    """Render the expense detail page."""
    expense = {
        "id": expense_id,
        "title": "Expense Detail",
        "amount_display": "$0.00",
        "category": "general",
        "status": "draft",
        "approval_state": "not_applicable",
        "created_at": datetime.utcnow().isoformat(),
    }
    return _render(request, "expenses/detail.html", {"active_page": "expenses", "expense": expense})


@router.get("/expenses/{expense_id}/line-items", response_class=HTMLResponse)
async def expense_line_items_partial(request: Request, expense_id: str):
    """HTMX partial: expense line items."""
    return _render_partial(request, "partials/empty_state.html", {
        "message": "No line items for this expense.",
    })


@router.get("/expenses/{expense_id}/attachments", response_class=HTMLResponse)
async def expense_attachments_partial(request: Request, expense_id: str):
    """HTMX partial: expense attachments."""
    return _render_partial(request, "partials/empty_state.html", {
        "message": "No attachments.",
    })


# ── Approvals ────────────────────────────────────────────────────────────

@router.get("/approvals/pending", response_class=HTMLResponse)
async def approvals_pending_page(request: Request):
    return _render(request, "approvals/pending.html", {"active_page": "approvals"})


@router.get("/approvals/pending-summary", response_class=HTMLResponse)
async def approvals_pending_summary(
    request: Request,
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """HTMX partial: pending approvals summary for dashboard card."""
    if not company_id:
        return _render_partial(request, "partials/empty_state.html", {
            "message": "Select a company to view pending approvals.",
        })
    return _render_partial(request, "partials/approvals_summary.html", {
        "pending": 0,
        "escalated": 0,
    })


@router.get("/approvals/pending-data", response_class=HTMLResponse)
async def approvals_pending_data(
    request: Request,
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """HTMX partial: pending approvals table."""
    if not company_id:
        return _render_partial(request, "partials/empty_company.html", {
            "message": "No company context.",
        })
    return _render_partial(request, "partials/approvals_pending_data.html", {"approvals": []})


@router.get("/approvals/chains/{chain_id}", response_class=HTMLResponse)
async def approval_chain_detail_page(request: Request, chain_id: str):
    """Render the approval chain detail page."""
    chain = {
        "id": chain_id,
        "entity_type": "expense",
        "entity_id": "expense-1",
        "status": "pending",
        "current_step": 1,
        "steps": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    return _render(request, "approvals/detail.html", {"active_page": "approvals", "chain": chain})


# ── Settlements ──────────────────────────────────────────────────────────

@router.get("/settlements", response_class=HTMLResponse)
async def settlements_page(
    request: Request,
    status_filter: Optional[str] = Query(None),
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """Serve the settlements list page or HTMX partial."""
    if request.headers.get("HX-Request"):
        return await _settlements_table_partial(request, status_filter, company_id)
    return _render(request, "settlements/list.html", {"active_page": "settlements"})


async def _settlements_table_partial(
    request: Request,
    status_filter: Optional[str],
    company_id: Optional[str],
) -> HTMLResponse:
    if not company_id:
        return _render_partial(request, "partials/empty_company.html", {
            "message": "No company context.",
        })
    return _render_partial(request, "partials/settlements_table.html", {"settlements": []})


@router.get("/settlements/{settlement_id}", response_class=HTMLResponse)
async def settlement_detail_page(request: Request, settlement_id: str):
    """Render the settlement detail page."""
    settlement = {
        "id": settlement_id,
        "entity_type": "expense",
        "entity_id": "expense-1",
        "total_amount_display": "$1,000.00",
        "settled_amount_display": "$0.00",
        "remaining_amount_display": "$1,000.00",
        "status": "pending",
        "priority": "normal",
    }
    return _render(request, "settlements/detail.html", {"active_page": "settlements", "settlement": settlement})


@router.get("/settlements/summary-card", response_class=HTMLResponse)
async def settlements_summary_card(
    request: Request,
    company_id: Optional[str] = Depends(get_optional_company_id),
):
    """HTMX partial: settlement summary for dashboard card."""
    if not company_id:
        return _render_partial(request, "partials/empty_state.html", {
            "message": "Select a company to view settlement status.",
        })
    return _render_partial(request, "partials/settlement_summary.html", {
        "summary": {
            "pending_settlements": 0,
            "completed_settlements": 0,
            "total_pending_amount_display": "$0.00",
            "total_settled_amount_display": "$0.00",
        }
    })


# ── Health ───────────────────────────────────────────────────────────────

@router.get("/health-check", response_class=HTMLResponse)
async def frontend_health(request: Request):
    return HTMLResponse("<p>Frontend routes are operational.</p>")


__all__ = ["router"]
