"""Expenses subpackage — re-export façade.

Centralized under ``models/expense.py``, ``schemas/expense_schema.py``,
``state_machines/expense.py``, ``services/expense_service.py``, and
``routes/expense_routes.py``. Fabricated symbols in the original stub
(ExpenseDocument, OcrExtractionResult, ExpenseRecord,
ExpenseFieldConfirmation, ExpenseApproval, ExpenseStatus,
ApprovalAction, the *Record*/*Document*/*Confirmation/*Approval
Create+Response schemas, ExpenseRepository) were never shipped and
are dropped. See ../../../problem.md.
"""

from finance_platform.models.expense import (
    Expense,
    ExpenseAttachment,
    ExpenseLineItem,
)
from finance_platform.schemas.expense_schema import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseTimelineResponse,
    ExpenseUpdate,
)
from finance_platform.services.expense_service import ExpenseService
from finance_platform.state_machines.expense import ExpenseStateMachine
from finance_platform.routes.expense_routes import router as expense_router

__all__ = [
    "Expense",
    "ExpenseAttachment",
    "ExpenseLineItem",
    "ExpenseCreate",
    "ExpenseListResponse",
    "ExpenseResponse",
    "ExpenseTimelineResponse",
    "ExpenseUpdate",
    "ExpenseService",
    "ExpenseStateMachine",
    "expense_router",
]
