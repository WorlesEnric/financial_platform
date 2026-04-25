from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from finance_platform.watermark.models import (
    Watermark,
    WatermarkBatch,
    WatermarkBatchItem,
    WatermarkStatus,
    WatermarkSeverity,
    WatermarkTemplate,
    WatermarkType,
    WatermarkPosition,
    DocumentReference,
)
from finance_platform.watermark.repository import WatermarkRepository
from finance_platform.watermark.engine import WatermarkEngine
from finance_platform.watermark.detector import WatermarkDetector
from finance_platform.watermark.policy import WatermarkPolicyManager
from finance_platform.watermark.exceptions import (
    WatermarkNotFoundError,
    WatermarkAlreadyAppliedError,
    WatermarkVerificationFailedError,
    WatermarkPolicyViolationError,
    WatermarkTemplateNotFoundError,
    WatermarkExpiredError,
    WatermarkRevokedError,
)


class WatermarkService:
    def __init__(
        self,
        repository: Optional[WatermarkRepository] = None,
        engine: Optional[WatermarkEngine] = None,
        detector: Optional[WatermarkDetector] = None,
        policy_manager: Optional[WatermarkPolicyManager] = None,
    ) -> None:
        self.repository = repository or WatermarkRepository()
        self.engine = engine or WatermarkEngine()
        self.detector = detector or WatermarkDetector()
        self.policy_manager = policy_manager or WatermarkPolicyManager()

    def create_watermark(
        self,
        document_reference: DocumentReference,
        watermark_type: WatermarkType = WatermarkType.TEXT,
        content: str = "",
        position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER,
        opacity: float = 0.5,
        rotation: float = 0.0,
        severity: str = "info",
        company_id: str = "",
        created_by: str = "",
        template_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> Watermark:
        violations = self.policy_manager.validate_against_policies(
            watermark_type=watermark_type.value,
            position=position.value,
            mime_type=document_reference.mime_type,
            company_id=company_id,
            opacity=opacity,
        )
        if violations:
            raise WatermarkPolicyViolationError(
                policy_name="watermark_policy",
                detail="; ".join(violations),
            )

        watermark = Watermark(
            document_reference=document_reference,
            template_id=template_id,
            watermark_type=watermark_type,
            content=content or watermark_type.value.upper(),
            position=position,
            opacity=opacity,
            rotation=rotation,
            severity=WatermarkSeverity(severity) if any(severity == s.value for s in WatermarkSeverity) else WatermarkSeverity.INFO,
            company_id=company_id,
            created_by=created_by,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        return self.repository.save(watermark)

    def apply_watermark(self, watermark_id: str, applied_by: str) -> Watermark:
        watermark = self.repository.get_or_raise(watermark_id)

        if watermark.is_applied:
            raise WatermarkAlreadyAppliedError(watermark_id)
        if watermark.status == WatermarkStatus.EXPIRED:
            raise WatermarkExpiredError(watermark_id)
        if watermark.status == WatermarkStatus.REVOKED:
            raise WatermarkRevokedError(watermark_id)

        watermark.apply(applied_by)
        watermark.verification_hash = self.engine.generate_verification_hash(watermark)
        rendered = self.engine.apply_watermark(watermark)
        watermark.metadata["rendered_size_bytes"] = str(len(rendered))
        return self.repository.save(watermark)

    def verify_watermark(self, watermark_id: str, verified_by: str) -> Watermark:
        watermark = self.repository.get_or_raise(watermark_id)

        if watermark.status == WatermarkStatus.REVOKED:
            raise WatermarkRevokedError(watermark_id)
        if watermark.status == WatermarkStatus.EXPIRED:
            raise WatermarkExpiredError(watermark_id)
        if watermark.status != WatermarkStatus.APPLIED:
            raise WatermarkVerificationFailedError(
                watermark_id=watermark_id,
                reason="Watermark must be in APPLIED status before verification",
            )

        integrity_ok = self.engine.verify_watermark_integrity(watermark)
        if not integrity_ok:
            watermark.mark_verification_failed("Integrity check failed")
            self.repository.save(watermark)
            raise WatermarkVerificationFailedError(
                watermark_id=watermark_id,
                reason="Watermark integrity verification failed",
            )

        watermark.mark_verified(verified_by)
        return self.repository.save(watermark)

    def revoke_watermark(self, watermark_id: str, revoked_by: str, reason: str) -> Watermark:
        watermark = self.repository.get_or_raise(watermark_id)
        watermark.revoke(revoked_by, reason)
        return self.repository.save(watermark)

    def expire_watermark(self, watermark_id: str) -> Watermark:
        watermark = self.repository.get_or_raise(watermark_id)
        watermark.expire()
        return self.repository.save(watermark)

    def get_watermark(self, watermark_id: str) -> Watermark:
        return self.repository.get_or_raise(watermark_id)

    def list_watermarks(
        self,
        status: Optional[WatermarkStatus] = None,
        watermark_type: Optional[str] = None,
        company_id: Optional[str] = None,
        document_id: Optional[str] = None,
        applied_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Watermark], int]:
        return self.repository.list(
            status=status,
            watermark_type=watermark_type,
            company_id=company_id,
            document_id=document_id,
            applied_by=applied_by,
            page=page,
            page_size=page_size,
        )

    def delete_watermark(self, watermark_id: str) -> bool:
        return self.repository.delete(watermark_id)

    def get_stats(self, company_id: Optional[str] = None) -> dict:
        return self.repository.get_stats(company_id=company_id)

    # --- Template operations ---

    def create_template(
        self,
        name: str,
        description: str = "",
        watermark_type: WatermarkType = WatermarkType.TEXT,
        content_template: str = "",
        font_family: str = "Arial",
        font_size: int = 12,
        font_color: str = "#000000",
        opacity: float = 0.5,
        rotation: float = 0.0,
        position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        repeat: bool = False,
        margin_x: int = 10,
        margin_y: int = 10,
        required: bool = False,
    ) -> WatermarkTemplate:
        template = WatermarkTemplate(
            name=name,
            description=description,
            watermark_type=watermark_type,
            content_template=content_template,
            font_family=font_family,
            font_size=font_size,
            font_color=font_color,
            opacity=opacity,
            rotation=rotation,
            position=position,
            scale_x=scale_x,
            scale_y=scale_y,
            repeat=repeat,
            margin_x=margin_x,
            margin_y=margin_y,
            required=required,
        )
        return self.repository.save_template(template)

    def update_template(self, template_id: str, updates: dict) -> WatermarkTemplate:
        template = self.repository.get_template_or_raise(template_id)
        for key, value in updates.items():
            if hasattr(template, key) and key not in ("id", "created_at"):
                setattr(template, key, value)
        return self.repository.save_template(template)

    def get_template(self, template_id: str) -> WatermarkTemplate:
        return self.repository.get_template_or_raise(template_id)

    def list_templates(self, active_only: bool = True) -> list[WatermarkTemplate]:
        return self.repository.list_templates(active_only=active_only)

    def delete_template(self, template_id: str) -> bool:
        return self.repository.delete_template(template_id)

    def apply_template(
        self,
        template_id: str,
        document_reference: DocumentReference,
        company_id: str,
        applied_by: str,
        variables: Optional[dict[str, str]] = None,
    ) -> Watermark:
        template = self.repository.get_template_or_raise(template_id)
        content = template.render_content(variables or {})
        watermark = self.create_watermark(
            document_reference=document_reference,
            watermark_type=template.watermark_type,
            content=content,
            position=template.position,
            opacity=template.opacity,
            rotation=template.rotation,
            company_id=company_id,
            created_by=applied_by,
            template_id=template_id,
        )
        return self.apply_watermark(watermark.id, applied_by)

    # --- Batch operations ---

    def create_batch(
        self,
        name: str,
        description: str,
        documents: list[DocumentReference],
        template_id: Optional[str] = None,
        watermark_type: WatermarkType = WatermarkType.TEXT,
        position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER,
        company_id: str = "",
    ) -> WatermarkBatch:
        batch = WatermarkBatch(
            name=name,
            description=description,
            template_id=template_id,
            watermark_type=watermark_type,
            position=position,
            company_id=company_id,
        )
        for doc in documents:
            item = WatermarkBatchItem(
                document_reference=doc,
            )
            batch.add_item(item)
        return self.repository.save_batch(batch)

    def process_batch(self, batch_id: str, applied_by: str) -> WatermarkBatch:
        batch = self.repository.get_batch_or_raise(batch_id)

        for item in batch.items:
            try:
                if batch.template_id:
                    watermark = self.apply_template(
                        template_id=batch.template_id,
                        document_reference=item.document_reference,
                        company_id=batch.company_id,
                        applied_by=applied_by,
                    )
                else:
                    watermark = self.create_watermark(
                        document_reference=item.document_reference,
                        watermark_type=batch.watermark_type,
                        position=batch.position,
                        company_id=batch.company_id,
                        created_by=applied_by,
                    )
                    watermark = self.apply_watermark(watermark.id, applied_by)

                item.watermark_id = watermark.id
                item.status = WatermarkStatus.APPLIED
                batch.record_success()
            except Exception as exc:
                item.status = WatermarkStatus.FAILED
                item.error_message = str(exc)
                batch.record_failure(str(exc))

        return self.repository.save_batch(batch)

    def get_batch(self, batch_id: str) -> WatermarkBatch:
        return self.repository.get_batch_or_raise(batch_id)

    def list_batches(
        self,
        company_id: Optional[str] = None,
        status: Optional[WatermarkStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WatermarkBatch], int]:
        return self.repository.list_batches(
            company_id=company_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    # --- Detection & verification ---

    def detect_watermark(
        self, document_content: bytes, watermark_id: str
    ) -> dict:
        watermark = self.repository.get_or_raise(watermark_id)
        return self.detector.detect(document_content, watermark)

    def scan_document(self, document_content: bytes) -> list[dict]:
        return self.detector.scan_document(document_content)

    def check_integrity(self, watermark_id: str) -> bool:
        watermark = self.repository.get_or_raise(watermark_id)
        return self.engine.verify_watermark_integrity(watermark)

    # --- Policy operations (delegated) ---

    def validate_watermark_request(
        self,
        watermark_type: str,
        position: str,
        mime_type: str,
        company_id: str,
        opacity: float = 0.5,
    ) -> list[str]:
        return self.policy_manager.validate_against_policies(
            watermark_type=watermark_type,
            position=position,
            mime_type=mime_type,
            company_id=company_id,
            opacity=opacity,
        )

    def get_supported_mime_types(self) -> list[str]:
        return self.engine.list_supported_types()

    def estimate_placement(
        self,
        position: WatermarkPosition,
        page_width: int = 595,
        page_height: int = 842,
        margin_x: int = 10,
        margin_y: int = 10,
    ) -> dict[str, int]:
        return self.engine.estimate_placement(
            position=position,
            page_width=page_width,
            page_height=page_height,
            margin_x=margin_x,
            margin_y=margin_y,
        )
