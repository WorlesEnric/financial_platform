from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from finance_platform.routes.dependencies import (
    CompanyContext,
    get_company_context,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class ReportParams(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    group_by: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None


class ExpenseSummary(BaseModel):
    total_expenses: float = 0.0
    total_reimbursable: float = 0.0
    total_non_reimbursable: float = 0.0
    expense_count: int = 0
    by_category: dict[str, float] = Field(default_factory=dict)
    by_department: dict[str, float] = Field(default_factory=dict)
    by_cost_center: dict[str, float] = Field(default_factory=dict)


class ApprovalSummary(BaseModel):
    total_approvals: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    average_approval_time_hours: float = 0.0
    by_type: dict[str, int] = Field(default_factory=dict)


class SettlementSummary(BaseModel):
    total_settlements: int = 0
    total_amount: float = 0.0
    completed_count: int = 0
    pending_count: int = 0
    failed_count: int = 0
    by_entity_type: dict[str, float] = Field(default_factory=dict)


class FinancialReport(BaseModel):
    period: dict[str, Any] = Field(default_factory=dict)
    expense_summary: ExpenseSummary = Field(default_factory=ExpenseSummary)
    approval_summary: ApprovalSummary = Field(default_factory=ApprovalSummary)
    settlement_summary: SettlementSummary = Field(default_factory=SettlementSummary)
    total_outstanding_debts: float = 0.0
    total_carry_forward: float = 0.0
    currency: str = "USD"


@router.get("/expenses", response_model=ExpenseSummary)
async def expense_report(
    ctx: CompanyContext = Depends(get_company_context),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    group_by: Optional[str] = None,
):
    from finance_platform.routes.expense_routes import _expenses_db

    expenses = list(_expenses_db.values())
    if from_date:
        expenses = [e for e in expenses if e.get("expense_date") and e["expense_date"] >= str(from_date)]
    if to_date:
        expenses = [e for e in expenses if e.get("expense_date") and e["expense_date"] <= str(to_date)]
    total = sum(e.get("total_amount", 0) for e in expenses)
    reimbursable = sum(e.get("total_amount", 0) for e in expenses if e.get("reimbursable"))
    non_reimbursable = sum(e.get("total_amount", 0) for e in expenses if not e.get("reimbursable"))
    by_category: dict[str, float] = {}
    by_department: dict[str, float] = {}
    by_cost_center: dict[str, float] = {}
    for e in expenses:
        cat = e.get("category", "other")
        by_category[cat] = by_category.get(cat, 0) + e.get("total_amount", 0)
        dept = e.get("department", "unknown")
        by_department[dept] = by_department.get(dept, 0) + e.get("total_amount", 0)
        cc = e.get("cost_center", "unknown")
        by_cost_center[cc] = by_cost_center.get(cc, 0) + e.get("total_amount", 0)
    return ExpenseSummary(
        total_expenses=round(total, 2),
        total_reimbursable=round(reimbursable, 2),
        total_non_reimbursable=round(non_reimbursable, 2),
        expense_count=len(expenses),
        by_category=by_category,
        by_department=by_department,
        by_cost_center=by_cost_center,
    )


@router.get("/approvals", response_model=ApprovalSummary)
async def approval_report(
    ctx: CompanyContext = Depends(get_company_context),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    from finance_platform.routes.approval_routes import _approvals_db

    approvals = list(_approvals_db.values())
    if from_date:
        approvals = [a for a in approvals if a.get("created_at") and str(from_date) <= str(a["created_at"])]
    if to_date:
        approvals = [a for a in approvals if a.get("created_at") and str(a["created_at"]) <= str(to_date)]
    by_type: dict[str, int] = {}
    for a in approvals:
        atype = a.get("approval_type", "unknown")
        by_type[atype] = by_type.get(atype, 0) + 1
    return ApprovalSummary(
        total_approvals=len(approvals),
        pending=sum(1 for a in approvals if a.get("status") in ("pending", "in_progress")),
        approved=sum(1 for a in approvals if a.get("status") == "approved"),
        rejected=sum(1 for a in approvals if a.get("status") == "rejected"),
        by_type=by_type,
    )


@router.get("/settlements", response_model=SettlementSummary)
async def settlement_report(
    ctx: CompanyContext = Depends(get_company_context),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    from finance_platform.routes.settlement_routes import _settlements_db

    settlements = list(_settlements_db.values())
    if from_date:
        settlements = [s for s in settlements if s.get("created_at") and str(from_date) <= str(s["created_at"])]
    if to_date:
        settlements = [s for s in settlements if s.get("created_at") and str(s["created_at"]) <= str(to_date)]
    by_entity: dict[str, float] = {}
    for s in settlements:
        etype = s.get("entity_type", "unknown")
        by_entity[etype] = by_entity.get(etype, 0) + s.get("total_amount", 0)
    return SettlementSummary(
        total_settlements=len(settlements),
        total_amount=round(sum(s.get("total_amount", 0) for s in settlements), 2),
        completed_count=sum(1 for s in settlements if s.get("status") == "completed"),
        pending_count=sum(1 for s in settlements if s.get("status") == "pending"),
        failed_count=sum(1 for s in settlements if s.get("status") == "failed"),
        by_entity_type=by_entity,
    )


@router.get("/financial", response_model=FinancialReport)
async def financial_report(
    ctx: CompanyContext = Depends(get_company_context),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    from finance_platform.routes.debt_routes import _debts_db
    from finance_platform.routes.carry_forward_routes import _buckets_db

    expense_summary = await expense_report(ctx, from_date, to_date)
    approval_summary = await approval_report(ctx, from_date, to_date)
    settlement_summary = await settlement_report(ctx, from_date, to_date)
    debts = list(_debts_db.values())
    buckets = list(_buckets_db.values())
    return FinancialReport(
        period={
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None,
        },
        expense_summary=expense_summary,
        approval_summary=approval_summary,
        settlement_summary=settlement_summary,
        total_outstanding_debts=round(sum(d.get("outstanding_amount", 0) for d in debts), 2),
        total_carry_forward=round(sum(b.get("remaining_amount", 0) for b in buckets), 2),
        currency="USD",
    )
