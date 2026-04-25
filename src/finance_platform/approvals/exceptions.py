from __future__ import annotations


class ApprovalError(Exception):
    """Base exception for all approvals module errors."""

    def __init__(self, message: str, code: str = "approval_error") -> None:
        self.code = code
        super().__init__(message)


class ApprovalNotFoundError(ApprovalError):
    def __init__(self, approval_id: str) -> None:
        super().__init__(
            message=f"Approval with id '{approval_id}' not found.",
            code="approval_not_found",
        )
        self.approval_id = approval_id


class ApprovalStepNotFoundError(ApprovalError):
    def __init__(self, step_id: str) -> None:
        super().__init__(
            message=f"Approval step with id '{step_id}' not found.",
            code="approval_step_not_found",
        )
        self.step_id = step_id


class ApprovalAlreadyProcessedError(ApprovalError):
    def __init__(self, approval_id: str) -> None:
        super().__init__(
            message=f"Approval '{approval_id}' has already been processed and cannot be modified.",
            code="approval_already_processed",
        )
        self.approval_id = approval_id


class InsufficientApproversError(ApprovalError):
    def __init__(self, required: int, actual: int) -> None:
        super().__init__(
            message=f"Insufficient approvers: required {required}, got {actual}.",
            code="insufficient_approvers",
        )
        self.required = required
        self.actual = actual


class DelegationNotFoundError(ApprovalError):
    def __init__(self, delegation_id: str) -> None:
        super().__init__(
            message=f"Delegation with id '{delegation_id}' not found.",
            code="delegation_not_found",
        )
        self.delegation_id = delegation_id


class PolicyViolationError(ApprovalError):
    def __init__(self, policy_name: str, detail: str) -> None:
        super().__init__(
            message=f"Policy violation for '{policy_name}': {detail}",
            code="policy_violation",
        )
        self.policy_name = policy_name
        self.detail = detail


class PolicyNotFoundError(ApprovalError):
    def __init__(self, policy_id: str) -> None:
        super().__init__(
            message=f"Approval policy with id '{policy_id}' not found.",
            code="policy_not_found",
        )
        self.policy_id = policy_id


class StepNotActionableError(ApprovalError):
    def __init__(self, step_id: str, status: str) -> None:
        super().__init__(
            message=f"Step '{step_id}' is in status '{status}' and cannot be acted upon.",
            code="step_not_actionable",
        )
        self.step_id = step_id
        self.status = status


class UnauthorizedApprovalActionError(ApprovalError):
    def __init__(self, user_id: str, step_id: str) -> None:
        super().__init__(
            message=f"User '{user_id}' is not authorized to act on step '{step_id}'.",
            code="unauthorized_approval_action",
        )
        self.user_id = user_id
        self.step_id = step_id


class DelegationExpiredError(ApprovalError):
    def __init__(self, delegation_id: str) -> None:
        super().__init__(
            message=f"Delegation '{delegation_id}' has expired.",
            code="delegation_expired",
        )
        self.delegation_id = delegation_id


class ApprovalExpiredError(ApprovalError):
    def __init__(self, approval_id: str) -> None:
        super().__init__(
            message=f"Approval '{approval_id}' has expired and can no longer be processed.",
            code="approval_expired",
        )
        self.approval_id = approval_id
