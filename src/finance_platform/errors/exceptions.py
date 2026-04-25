from __future__ import annotations

from typing import Any, Optional

from finance_platform.errors.base import ErrorSeverity, FinancePlatformError
from finance_platform.errors.codes import ErrorCategory, ErrorCode


class AuthError(FinancePlatformError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.AUTH_INVALID_CREDENTIALS.value,
        http_status: int = 401,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class AuthenticationError(AuthError):
    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        code: str = ErrorCode.AUTH_INVALID_CREDENTIALS.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class AuthorizationError(AuthError):
    def __init__(
        self,
        message: str = "Insufficient permissions",
        *,
        code: str = ErrorCode.FORBIDDEN.value,
        http_status: int = 403,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class PermissionDeniedError(AuthorizationError):
    def __init__(
        self,
        message: str = "Permission denied",
        *,
        code: str = ErrorCode.FORBIDDEN.value,
        http_status: int = 403,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        super().__init__(
            message,
            code=code,
            http_status=http_status,
            context=ctx,
            **kwargs,
        )


class ValidationError(FinancePlatformError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.VALIDATION_CONSTRAINT_VIOLATION.value,
        http_status: int = 400,
        field_errors: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        self.field_errors = field_errors or {}
        ctx = kwargs.pop("context", {})
        ctx["field_errors"] = self.field_errors
        super().__init__(
            message, code=code, http_status=http_status, context=ctx, **kwargs
        )


class NotFoundError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Resource not found",
        *,
        code: str = ErrorCode.NOT_FOUND.value,
        http_status: int = 404,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        if resource_type:
            ctx["resource_type"] = resource_type
        if resource_id:
            ctx["resource_id"] = resource_id
        super().__init__(
            message, code=code, http_status=http_status, context=ctx, **kwargs
        )


class ConflictError(FinancePlatformError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.CONFLICT_DUPLICATE.value,
        http_status: int = 409,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class DatabaseError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Database error",
        *,
        code: str = ErrorCode.DB_QUERY.value,
        http_status: int = 500,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class ServiceError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Service error",
        *,
        code: str = ErrorCode.SERVICE_UNAVAILABLE.value,
        http_status: int = 503,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class ExternalServiceError(FinancePlatformError):
    def __init__(
        self,
        message: str = "External service error",
        *,
        code: str = ErrorCode.EXTERNAL_API_ERROR.value,
        http_status: int = 502,
        service_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ctx = kwargs.pop("context", {})
        if service_name:
            ctx["service_name"] = service_name
        super().__init__(
            message, code=code, http_status=http_status, context=ctx, **kwargs
        )


class ConfigurationError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Configuration error",
        *,
        code: str = ErrorCode.CONFIG_MISSING.value,
        severity: ErrorSeverity = ErrorSeverity.CRITICAL,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, severity=severity, **kwargs)


class BusinessRuleError(FinancePlatformError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.BUSINESS_RULE_VIOLATION.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class IntegrationError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Integration error",
        *,
        code: str = ErrorCode.INTEGRATION_MISMATCH.value,
        http_status: int = 500,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class StateMachineError(FinancePlatformError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.STATE_MACHINE_INVALID_TRANSITION.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class AmortizationError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Amortization error",
        *,
        code: str = ErrorCode.AMORT_CALCULATION_ERROR.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class AmortizationScheduleError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization schedule not found",
        *,
        code: str = ErrorCode.AMORT_SCHEDULE_NOT_FOUND.value,
        http_status: int = 404,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class AmortizationCalculationError(AmortizationError):
    def __init__(
        self,
        message: str = "Amortization calculation error",
        *,
        code: str = ErrorCode.AMORT_CALCULATION_ERROR.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class ApprovalError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Approval error",
        *,
        code: str = ErrorCode.APPROVAL_CHAIN_BROKEN.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class ApprovalChainError(ApprovalError):
    def __init__(
        self,
        message: str = "Approval chain broken",
        *,
        code: str = ErrorCode.APPROVAL_CHAIN_BROKEN.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class ApprovalPermissionError(ApprovalError):
    def __init__(
        self,
        message: str = "Insufficient approval permission",
        *,
        code: str = ErrorCode.APPROVAL_INSUFFICIENT.value,
        http_status: int = 403,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class ExpenseError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Expense error",
        *,
        code: str = ErrorCode.EXPENSE_POLICY_VIOLATION.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class ExpenseRejectionError(ExpenseError):
    def __init__(
        self,
        message: str = "Expense rejected",
        *,
        code: str = ErrorCode.EXPENSE_REJECTED.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class ExpenseDuplicateError(ExpenseError):
    def __init__(
        self,
        message: str = "Duplicate expense",
        *,
        code: str = ErrorCode.EXPENSE_DUPLICATE.value,
        http_status: int = 409,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class FxError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Foreign exchange error",
        *,
        code: str = ErrorCode.FX_CONVERSION_ERROR.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class FxRateNotFoundError(FxError):
    def __init__(
        self,
        message: str = "FX rate not found",
        *,
        code: str = ErrorCode.FX_RATE_NOT_FOUND.value,
        http_status: int = 404,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class FxConversionError(FxError):
    def __init__(
        self,
        message: str = "FX conversion error",
        *,
        code: str = ErrorCode.FX_CONVERSION_ERROR.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class NotificationError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Notification error",
        *,
        code: str = ErrorCode.NOTIF_DELIVERY_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class NotificationDeliveryError(NotificationError):
    def __init__(
        self,
        message: str = "Notification delivery failed",
        *,
        code: str = ErrorCode.NOTIF_DELIVERY_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class SettlementError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Settlement error",
        *,
        code: str = ErrorCode.SETTLEMENT_IMBALANCE.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class SettlementReconciliationError(SettlementError):
    def __init__(
        self,
        message: str = "Settlement reconciliation failed",
        *,
        code: str = ErrorCode.SETTLEMENT_RECONCILIATION_FAILED.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class CarryForwardError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Carry forward error",
        *,
        code: str = ErrorCode.CARRY_FORWARD_CALCULATION_ERROR.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class CarryForwardPeriodError(CarryForwardError):
    def __init__(
        self,
        message: str = "Carry forward period error",
        *,
        code: str = ErrorCode.CARRY_FORWARD_PERIOD_MISMATCH.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class DebtError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Debt error",
        *,
        code: str = ErrorCode.DEBT_VALIDATION_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class DebtSettlementError(DebtError):
    def __init__(
        self,
        message: str = "Debt settlement error",
        *,
        code: str = ErrorCode.DEBT_ALREADY_SETTLED.value,
        http_status: int = 409,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class MigrationError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Migration error",
        *,
        code: str = ErrorCode.MIGRATION_FAILED.value,
        severity: ErrorSeverity = ErrorSeverity.CRITICAL,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, severity=severity, **kwargs)


class MigrationVersionError(MigrationError):
    def __init__(
        self,
        message: str = "Migration version conflict",
        *,
        code: str = ErrorCode.MIGRATION_VERSION_CONFLICT.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class OcrError(FinancePlatformError):
    def __init__(
        self,
        message: str = "OCR error",
        *,
        code: str = ErrorCode.OCR_PROCESSING_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class OcrProcessingError(OcrError):
    def __init__(
        self,
        message: str = "OCR processing failed",
        *,
        code: str = ErrorCode.OCR_PROCESSING_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class OcrUnreadableError(OcrError):
    def __init__(
        self,
        message: str = "Document unreadable by OCR",
        *,
        code: str = ErrorCode.OCR_UNREADABLE.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class WatermarkError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Watermark error",
        *,
        code: str = ErrorCode.WATERMARK_VALIDATION_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class WatermarkValidationError(WatermarkError):
    def __init__(
        self,
        message: str = "Watermark validation failed",
        *,
        code: str = ErrorCode.WATERMARK_VALIDATION_FAILED.value,
        http_status: int = 422,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class AuditError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Audit error",
        *,
        code: str = ErrorCode.AUDIT_LOG_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class AuditTrailError(AuditError):
    def __init__(
        self,
        message: str = "Audit trail integrity error",
        *,
        code: str = ErrorCode.AUDIT_TRAIL_BROKEN.value,
        http_status: int = 500,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class IdentityError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Identity error",
        *,
        code: str = ErrorCode.IDENTITY_VERIFICATION_FAILED.value,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, **kwargs)


class IdentityVerificationError(IdentityError):
    def __init__(
        self,
        message: str = "Identity verification failed",
        *,
        code: str = ErrorCode.IDENTITY_VERIFICATION_FAILED.value,
        http_status: int = 403,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, http_status=http_status, **kwargs)


class LoggingError(FinancePlatformError):
    def __init__(
        self,
        message: str = "Logging error",
        *,
        code: str = ErrorCode.LOGGING_CONFIG_ERROR.value,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, code=code, severity=severity, **kwargs)
