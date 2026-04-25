from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from finance_platform.watermark.models import (
    Watermark,
    WatermarkBatch,
    WatermarkBatchItem,
    WatermarkStatus,
    WatermarkTemplate,
    DocumentReference,
)
from finance_platform.watermark.exceptions import (
    WatermarkNotFoundError,
    WatermarkTemplateNotFoundError,
    WatermarkBatchError,
)


class WatermarkRepository:
    def __init__(self) -> None:
        self._watermarks: dict[str, Watermark] = {}
        self._templates: dict[str, WatermarkTemplate] = {}
        self._batches: dict[str, WatermarkBatch] = {}

    # --- Watermarks ---

    def save(self, watermark: Watermark) -> Watermark:
        watermark.updated_at = datetime.now(timezone.utc)
        self._watermarks[watermark.id] = watermark
        return watermark

    def get(self, watermark_id: str) -> Optional[Watermark]:
        return self._watermarks.get(watermark_id)

    def get_or_raise(self, watermark_id: str) -> Watermark:
        watermark = self.get(watermark_id)
        if watermark is None:
            raise WatermarkNotFoundError(watermark_id)
        return watermark

    def list(
        self,
        status: Optional[WatermarkStatus] = None,
        watermark_type: Optional[str] = None,
        company_id: Optional[str] = None,
        document_id: Optional[str] = None,
        applied_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Watermark], int]:
        results = list(self._watermarks.values())

        if status is not None:
            results = [w for w in results if w.status == status]
        if watermark_type is not None:
            results = [w for w in results if w.watermark_type.value == watermark_type]
        if company_id is not None:
            results = [w for w in results if w.company_id == company_id]
        if document_id is not None:
            results = [w for w in results if w.document_reference.id == document_id]
        if applied_by is not None:
            results = [w for w in results if w.applied_by == applied_by]

        results.sort(key=lambda w: w.created_at, reverse=True)
        total = len(results)

        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return paginated, total

    def delete(self, watermark_id: str) -> bool:
        return self._watermarks.pop(watermark_id, None) is not None

    def get_stats(self, company_id: Optional[str] = None) -> dict:
        watermarks = list(self._watermarks.values())
        if company_id is not None:
            watermarks = [w for w in watermarks if w.company_id == company_id]

        total = len(watermarks)
        applied = sum(1 for w in watermarks if w.status == WatermarkStatus.APPLIED)
        verified = sum(1 for w in watermarks if w.status == WatermarkStatus.VERIFIED)
        failed = sum(1 for w in watermarks if w.status == WatermarkStatus.VERIFICATION_FAILED or w.status == WatermarkStatus.FAILED)
        expired = sum(1 for w in watermarks if w.status == WatermarkStatus.EXPIRED)
        revoked = sum(1 for w in watermarks if w.status == WatermarkStatus.REVOKED)

        by_type: dict[str, int] = {}
        for w in watermarks:
            key = w.watermark_type.value
            by_type[key] = by_type.get(key, 0) + 1

        by_severity: dict[str, int] = {}
        for w in watermarks:
            key = w.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1

        now = datetime.now(timezone.utc)
        recent = sum(1 for w in watermarks if w.applied_at and (now - w.applied_at).days < 7)

        return {
            "total_watermarks": total,
            "total_applied": applied,
            "total_verified": verified,
            "total_failed": failed,
            "total_expired": expired,
            "total_revoked": revoked,
            "by_type": by_type,
            "by_severity": by_severity,
            "recent_applications": recent,
        }

    # --- Templates ---

    def save_template(self, template: WatermarkTemplate) -> WatermarkTemplate:
        template.updated_at = datetime.now(timezone.utc)
        self._templates[template.id] = template
        return template

    def get_template(self, template_id: str) -> Optional[WatermarkTemplate]:
        return self._templates.get(template_id)

    def get_template_or_raise(self, template_id: str) -> WatermarkTemplate:
        template = self.get_template(template_id)
        if template is None:
            raise WatermarkTemplateNotFoundError(template_id)
        return template

    def list_templates(self, active_only: bool = True) -> list[WatermarkTemplate]:
        results = list(self._templates.values())
        if active_only:
            results = [t for t in results if t.active]
        return results

    def delete_template(self, template_id: str) -> bool:
        return self._templates.pop(template_id, None) is not None

    # --- Batches ---

    def save_batch(self, batch: WatermarkBatch) -> WatermarkBatch:
        self._batches[batch.id] = batch
        return batch

    def get_batch(self, batch_id: str) -> Optional[WatermarkBatch]:
        return self._batches.get(batch_id)

    def get_batch_or_raise(self, batch_id: str) -> WatermarkBatch:
        batch = self.get_batch(batch_id)
        if batch is None:
            raise WatermarkBatchError(batch_id, "Batch not found")
        return batch

    def list_batches(
        self,
        company_id: Optional[str] = None,
        status: Optional[WatermarkStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WatermarkBatch], int]:
        results = list(self._batches.values())
        if company_id is not None:
            results = [b for b in results if b.company_id == company_id]
        if status is not None:
            results = [b for b in results if b.status == status]

        results.sort(key=lambda b: b.created_at, reverse=True)
        total = len(results)

        start = (page - 1) * page_size
        end = start + page_size
        paginated = results[start:end]

        return paginated, total

    def delete_batch(self, batch_id: str) -> bool:
        return self._batches.pop(batch_id, None) is not None
