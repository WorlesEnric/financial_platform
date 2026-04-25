"""Debts subpackage — re-export façade.

Centralized under ``models/debt.py``, ``state_machines/debt.py``, and
``routes/debt_routes.py``. Note there is no central ``DebtService``
anywhere in the build — the stub claimed one but the implementation
was never shipped. Other fabricated symbols (DebtItem, DebtState,
DebtNetBalance, DebtExceptionQueue, DebtItemCreate/Response,
DebtNetBalanceResponse, DebtSettlementRequest, DebtRepository) are
also dropped. See ../../../problem.md.
"""

from finance_platform.models.debt import Debt, DebtPayment, DebtSettlement
from finance_platform.state_machines.debt import DebtStateMachine
from finance_platform.routes.debt_routes import router as debt_router

__all__ = [
    "Debt",
    "DebtPayment",
    "DebtSettlement",
    "DebtStateMachine",
    "debt_router",
]
