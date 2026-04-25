from __future__ import annotations


class WatermarkError(Exception):
    def __init__(self, message: str, code: str = "watermark_error") -> None:
        self.code = code
        super().__init__(message)


class WatermarkNotFoundError(WatermarkError):
    def __init__(self, watermark_id: str) -> None:
        super().__init__(
            message=f"Watermark with id '{watermark_id}' not found.",
            code="watermark_not_found",
        )
        self.watermark_id = watermark_id


class WatermarkAlreadyAppliedError(WatermarkError):
    def __init__(self, watermark_id: str) -> None:
        super().__init__(
            message=f"Watermark '{watermark_id}' has already been applied.",
            code="watermark_already_applied",
        )
        self.watermark_id = watermark_id


class WatermarkVerificationFailedError(WatermarkError):
    def __init__(self, watermark_id: str, reason: str) -> None:
        super().__init__(
            message=f"Watermark verification failed for '{watermark_id}': {reason}",
            code="watermark_verification_failed",
        )
        self.watermark_id = watermark_id
        self.reason = reason


class WatermarkPolicyViolationError(WatermarkError):
    def __init__(self, policy_name: str, detail: str) -> None:
        super().__init__(
            message=f"Watermark policy violation for '{policy_name}': {detail}",
            code="watermark_policy_violation",
        )
        self.policy_name = policy_name
        self.detail = detail


class WatermarkEngineError(WatermarkError):
    def __init__(self, operation: str, detail: str) -> None:
        super().__init__(
            message=f"Watermark engine error during '{operation}': {detail}",
            code="watermark_engine_error",
        )
        self.operation = operation
        self.detail = detail


class WatermarkBatchError(WatermarkError):
    def __init__(self, batch_id: str, detail: str) -> None:
        super().__init__(
            message=f"Watermark batch '{batch_id}' error: {detail}",
            code="watermark_batch_error",
        )
        self.batch_id = batch_id
        self.detail = detail


class WatermarkTemplateNotFoundError(WatermarkError):
    def __init__(self, template_id: str) -> None:
        super().__init__(
            message=f"Watermark template with id '{template_id}' not found.",
            code="watermark_template_not_found",
        )
        self.template_id = template_id


class InvalidWatermarkPositionError(WatermarkError):
    def __init__(self, position: str) -> None:
        super().__init__(
            message=f"Invalid watermark position '{position}'.",
            code="invalid_watermark_position",
        )
        self.position = position


class WatermarkCorruptedException(WatermarkError):
    def __init__(self, watermark_id: str, detail: str) -> None:
        super().__init__(
            message=f"Watermark '{watermark_id}' data is corrupted: {detail}",
            code="watermark_corrupted",
        )
        self.watermark_id = watermark_id
        self.detail = detail


class DocumentNotSupportedError(WatermarkError):
    def __init__(self, mime_type: str) -> None:
        super().__init__(
            message=f"Document type '{mime_type}' is not supported for watermarking.",
            code="document_not_supported",
        )
        self.mime_type = mime_type


class WatermarkExpiredError(WatermarkError):
    def __init__(self, watermark_id: str) -> None:
        super().__init__(
            message=f"Watermark '{watermark_id}' has expired.",
            code="watermark_expired",
        )
        self.watermark_id = watermark_id


class WatermarkRevokedError(WatermarkError):
    def __init__(self, watermark_id: str) -> None:
        super().__init__(
            message=f"Watermark '{watermark_id}' has been revoked.",
            code="watermark_revoked",
        )
        self.watermark_id = watermark_id
