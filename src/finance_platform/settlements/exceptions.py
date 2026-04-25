from __future__ import annotations


class SettlementError(Exception):
    def __init__(self, message: str, code: str = "settlement_error") -> None:
        self.code = code
        super().__init__(message)


class SettlementNotFoundError(SettlementError):
    def __init__(self, settlement_id: str) -> None:
        super().__init__(
            message=f"Settlement with id '{settlement_id}' not found.",
            code="settlement_not_found",
        )
        self.settlement_id = settlement_id


class SettlementRunNotFoundError(SettlementError):
    def __init__(self, run_id: str) -> None:
        super().__init__(
            message=f"Settlement run with id '{run_id}' not found.",
            code="settlement_run_not_found",
        )
        self.run_id = run_id


class SettlementAlreadyCompletedError(SettlementError):
    def __init__(self, settlement_id: str, status: str) -> None:
        super().__init__(
            message=(
                f"Settlement '{settlement_id}' is already in status '{status}' "
                f"and cannot be modified."
            ),
            code="settlement_already_completed",
        )
        self.settlement_id = settlement_id
        self.status = status


class SettlementAlreadyReversedError(SettlementError):
    def __init__(self, settlement_id: str) -> None:
        super().__init__(
            message=f"Settlement '{settlement_id}' has already been reversed.",
            code="settlement_already_reversed",
        )
        self.settlement_id = settlement_id


class SettlementOverRegistrationError(SettlementError):
    def __init__(self, entity_type: str, entity_id: str, amount: float, available: float) -> None:
        super().__init__(
            message=(
                f"Over-registration rejected for {entity_type} '{entity_id}': "
                f"attempted to settle {amount}, but only {available} remaining."
            ),
            code="settlement_over_registration",
        )
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.amount = amount
        self.available = available


class SettlementAllocationError(SettlementError):
    def __init__(self, message: str, detail: str = "") -> None:
        super().__init__(
            message=f"Settlement allocation error: {message}",
            code="settlement_allocation_error",
        )
        self.detail = detail


class SettlementValidationError(SettlementError):
    def __init__(self, message: str, field_errors: dict[str, str] | None = None) -> None:
        self.field_errors = field_errors or {}
        super().__init__(
            message=f"Settlement validation error: {message}",
            code="settlement_validation_error",
        )


class SettlementRunInProgressError(SettlementError):
    def __init__(self, run_id: str) -> None:
        super().__init__(
            message=f"Settlement run '{run_id}' is already in progress.",
            code="settlement_run_in_progress",
        )
        self.run_id = run_id


class SettlementPriorityError(SettlementError):
    def __init__(self, entity_id: str, message: str = "") -> None:
        super().__init__(
            message=message or f"Settlement priority conflict for entity '{entity_id}'.",
            code="settlement_priority_error",
        )
        self.entity_id = entity_id


class SettlementPaymentError(SettlementError):
    def __init__(self, payment_ref: str, detail: str = "") -> None:
        super().__init__(
            message=f"Payment '{payment_ref}' failed: {detail}",
            code="settlement_payment_error",
        )
        self.payment_ref = payment_ref
        self.detail = detail


class SettlementReconciliationFailedError(SettlementError):
    def __init__(self, run_id: str, expected: float, actual: float) -> None:
        super().__init__(
            message=(
                f"Settlement run '{run_id}' reconciliation failed: "
                f"expected {expected}, got {actual}."
            ),
            code="settlement_reconciliation_failed",
        )
        self.run_id = run_id
        self.expected = expected
        self.actual = actual


class SettlementStateTransitionError(SettlementError):
    def __init__(self, current: str, target: str, reason: str = "") -> None:
        msg = f"Cannot transition from '{current}' to '{target}'"
        if reason:
            msg += f": {reason}"
        super().__init__(message=msg, code="settlement_state_transition_error")
        self.current = current
        self.target = target
