from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.errors.exceptions import (
    NotFoundError,
    ValidationError,
    BusinessRuleError,
    ExpenseDuplicateError,
    ExpenseRejectionError,
)
from finance_platform.models.base import ApprovalState, CurrencyCode, ExpenseCategory, ReimbursementStatus
from finance_platform.models.expense import Expense, ExpenseAttachment, ExpenseLineItem
from finance_platform.state_machines.expense import ExpenseStateMachine


class ExpenseService:
    def __init__(self) -> None:
        self._expenses: Dict[str, Expense] = {}

    def create_expense(
        self,
        user_id: str,
        title: str,
        category: ExpenseCategory,
        amount: float,
        total_amount: float,
        expense_date: date,
        currency: CurrencyCode = CurrencyCode.USD,
        description: Optional[str] = None,
        tax_amount: float = 0.0,
        vendor_name: Optional[str] = None,
        invoice_number: Optional[str] = None,
        billable: bool = False,
        reimbursable: bool = True,
        cost_center: Optional[str] = None,
        department: Optional[str] = None,
        project_id: Optional[str] = None,
        budget_code: Optional[str] = None,
        line_items: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            title=title,
            category=category,
            amount=amount,
            total_amount=total_amount,
            expense_date=expense_date,
            currency=currency,
            description=description,
            tax_amount=tax_amount,
            vendor_name=vendor_name,
            invoice_number=invoice_number,
            billable=billable,
            reimbursable=reimbursable,
            cost_center=cost_center,
            department=department,
            project_id=project_id,
            budget_code=budget_code,
            status=ReimbursementStatus.DRAFT,
            approval_state=ApprovalState.PENDING,
            tags=tags or [],
            metadata=metadata or {},
        )
        if line_items:
            expense.line_items = [ExpenseLineItem(**li) for li in line_items]
        self._expenses[expense.id] = expense
        return expense

    def get_expense(self, expense_id: str) -> Expense:
        expense = self._expenses.get(expense_id)
        if not expense or expense.is_deleted:
            raise NotFoundError(f"Expense {expense_id} not found", resource_type="Expense", resource_id=expense_id)
        return expense

    def update_expense(self, expense_id: str, **updates: Any) -> Expense:
        expense = self.get_expense(expense_id)
        if expense.status != ReimbursementStatus.DRAFT:
            raise BusinessRuleError("Can only update expenses in DRAFT status")
        for key, value in updates.items():
            if hasattr(expense, key) and key not in ("id", "user_id", "created_at", "status", "approval_state"):
                setattr(expense, key, value)
        expense.touch()
        return expense

    def delete_expense(self, expense_id: str) -> None:
        expense = self.get_expense(expense_id)
        expense.soft_delete()

    def list_expenses(
        self,
        user_id: Optional[str] = None,
        status: Optional[ReimbursementStatus] = None,
        category: Optional[ExpenseCategory] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Expense]:
        results = [e for e in self._expenses.values() if not e.is_deleted]
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if status:
            results = [e for e in results if e.status == status]
        if category:
            results = [e for e in results if e.category == category]
        if date_from:
            results = [e for e in results if e.expense_date >= date_from]
        if date_to:
            results = [e for e in results if e.expense_date <= date_to]
        if min_amount is not None:
            results = [e for e in results if e.total_amount >= min_amount]
        if max_amount is not None:
            results = [e for e in results if e.total_amount <= max_amount]
        if tags:
            results = [e for e in results if any(t in e.tags for t in tags)]
        return results

    def submit_expense(self, expense_id: str) -> Expense:
        expense = self.get_expense(expense_id)
        sm = ExpenseStateMachine(expense)
        sm.transition(ReimbursementStatus.SUBMITTED)
        return expense

    def approve_expense(self, expense_id: str, approved_by: str) -> Expense:
        expense = self.get_expense(expense_id)
        sm = ExpenseStateMachine(expense)
        sm.transition(ReimbursementStatus.APPROVED, context={"approved_by": approved_by})
        return expense

    def reject_expense(self, expense_id: str, rejection_reason: str) -> Expense:
        expense = self.get_expense(expense_id)
        sm = ExpenseStateMachine(expense)
        sm.transition(ReimbursementStatus.REJECTED, context={"rejection_reason": rejection_reason})
        return expense

    def pay_expense(self, expense_id: str) -> Expense:
        expense = self.get_expense(expense_id)
        sm = ExpenseStateMachine(expense)
        sm.transition(ReimbursementStatus.PAID)
        return expense

    def cancel_expense(self, expense_id: str) -> Expense:
        expense = self.get_expense(expense_id)
        sm = ExpenseStateMachine(expense)
        sm.transition(ReimbursementStatus.CANCELLED)
        return expense

    def close_expense(self, expense_id: str) -> Expense:
        expense = self.get_expense(expense_id)
        sm = ExpenseStateMachine(expense)
        sm.transition(ReimbursementStatus.CLOSED)
        return expense

    def add_attachment(self, expense_id: str, filename: str, content_type: str, size_bytes: int, storage_key: str) -> Expense:
        expense = self.get_expense(expense_id)
        attachment = ExpenseAttachment(
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
        )
        expense.attachments.append(attachment)
        expense.touch()
        return expense

    def get_expense_statistics(
        self,
        user_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        expenses = self.list_expenses(user_id=user_id, date_from=date_from, date_to=date_to)
        if not expenses:
            return {"count": 0, "total_amount": 0.0, "average_amount": 0.0, "by_category": {}, "by_status": {}}
        total = sum(e.total_amount for e in expenses)
        by_category: Dict[str, float] = {}
        by_status: Dict[str, int] = {}
        for e in expenses:
            by_category[e.category.value] = by_category.get(e.category.value, 0) + e.total_amount
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
        return {
            "count": len(expenses),
            "total_amount": round(total, 2),
            "average_amount": round(total / len(expenses), 2),
            "by_category": by_category,
            "by_status": by_status,
        }

    def bulk_submit(self, expense_ids: List[str]) -> Tuple[List[str], List[str]]:
        succeeded: List[str] = []
        failed: List[str] = []
        for eid in expense_ids:
            try:
                self.submit_expense(eid)
                succeeded.append(eid)
            except Exception:
                failed.append(eid)
        return succeeded, failed
