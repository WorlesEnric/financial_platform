from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from finance_platform.errors.base import FinancePlatformError, ErrorSeverity


class AmortizationError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Amortization error",
        *,
        code: str = "AMORT_ERROR",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        http_status: int = 500,
        cause: Optional[BaseException] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message,
            code=code,
            severity=severity,
            http_status=http_status,
            cause=cause,
            context=context,
            **kwargs,
        )


class AmortizationNotFoundError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization record not found",
        *,
        record_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx: Dict[str, Any] = {}
        if record_id:
            ctx["record_id"] = record_id
        if entity_id:
            ctx["entity_id"] = entity_id
        super().__init__(
            message,
            code="AMORT_NOT_FOUND",
            http_status=404,
            context=ctx,
            **kwargs,
        )


class AmortizationCalculationError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization calculation error",
        *,
        detail: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        if detail:
            ctx["detail"] = detail
        super().__init__(
            message,
            code="AMORT_CALCULATION_ERROR",
            http_status=422,
            context=ctx,
            **kwargs,
        )


class AmortizationValidationError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization validation error",
        *,
        field: Optional[str] = None,
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        if field:
            ctx["field"] = field
        if field_errors:
            ctx["field_errors"] = field_errors
        super().__init__(
            message,
            code="AMORT_VALIDATION_ERROR",
            http_status=400,
            context=ctx,
            **kwargs,
        )


class AmortizationStateError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization state transition not allowed",
        *,
        current_status: Optional[str] = None,
        target_status: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        if current_status:
            ctx["current_status"] = current_status
        if target_status:
            ctx["target_status"] = target_status
        super().__init__(
            message,
            code="AMORT_STATE_ERROR",
            http_status=422,
            context=ctx,
            **kwargs,
        )


class AmortizationPeriodMismatchError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization period mismatch",
        *,
        expected_periods: Optional[int] = None,
        actual_periods: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        if expected_periods is not None:
            ctx["expected_periods"] = str(expected_periods)
        if actual_periods is not None:
            ctx["actual_periods"] = str(actual_periods)
        super().__init__(
            message,
            code="AMORT_PERIOD_MISMATCH",
            http_status=422,
            context=ctx,
            **kwargs,
        )


class AmortizationEntryNotFoundError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization entry not found",
        *,
        entry_id: Optional[str] = None,
        record_id: Optional[str] = None,
        period_number: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        ctx: Dict[str, Any] = {}
        if entry_id:
            ctx["entry_id"] = entry_id
        if record_id:
            ctx["record_id"] = record_id
        if period_number is not None:
            ctx["period_number"] = str(period_number)
        super().__init__(
            message,
            code="AMORT_ENTRY_NOT_FOUND",
            http_status=404,
            context=ctx,
            **kwargs,
        )


class AmortizationRuleNotFoundError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization rule not found",
        *,
        rule_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx: Dict[str, Any] = {}
        if rule_id:
            ctx["rule_id"] = rule_id
        super().__init__(
            message,
            code="AMORT_RULE_NOT_FOUND",
            http_status=404,
            context=ctx,
            **kwargs,
        )


class AmortizationAlreadyCompletedError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization already completed",
        *,
        record_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx: Dict[str, Any] = {}
        if record_id:
            ctx["record_id"] = record_id
        super().__init__(
            message,
            code="AMORT_ALREADY_COMPLETED",
            http_status=409,
            context=ctx,
            **kwargs,
        )


class AmortizationDuplicateError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization record already exists for this entity",
        *,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx: Dict[str, Any] = {}
        if entity_type:
            ctx["entity_type"] = entity_type
        if entity_id:
            ctx["entity_id"] = entity_id
        super().__init__(
            message,
            code="AMORT_DUPLICATE",
            http_status=409,
            context=ctx,
            **kwargs,
        )
