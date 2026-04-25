from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from finance_platform.watermark.models import (
    Watermark,
    WatermarkStatus,
    WatermarkType,
    WatermarkPosition,
    DocumentReference,
)
from finance_platform.watermark.exceptions import (
    WatermarkEngineError,
    DocumentNotSupportedError,
    InvalidWatermarkPositionError,
)


class WatermarkEngine:
    SUPPORTED_MIME_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/tiff",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/html",
    }

    def __init__(self) -> None:
        self._renderers: dict[WatermarkType, str] = {
            WatermarkType.TEXT: "render_text_watermark",
            WatermarkType.IMAGE: "render_image_watermark",
            WatermarkType.QR_CODE: "render_qr_code_watermark",
            WatermarkType.BARCODE: "render_barcode_watermark",
            WatermarkType.STAMP: "render_stamp_watermark",
            WatermarkType.ELECTRONIC_SEAL: "render_electronic_seal_watermark",
            WatermarkType.TIMESTAMP: "render_timestamp_watermark",
            WatermarkType.DOCUMENT_ID: "render_document_id_watermark",
            WatermarkType.COMPANY_LOGO: "render_company_logo_watermark",
            WatermarkType.CONFIDENTIAL: "render_confidential_watermark",
            WatermarkType.DRAFT: "render_draft_watermark",
            WatermarkType.APPROVED: "render_approved_watermark",
            WatermarkType.PAID: "render_paid_watermark",
            WatermarkType.VOID: "render_void_watermark",
            WatermarkType.COPY: "render_copy_watermark",
            WatermarkType.CUSTOM: "render_custom_watermark",
        }

    def validate_document(self, document: DocumentReference) -> None:
        if document.mime_type not in self.SUPPORTED_MIME_TYPES:
            raise DocumentNotSupportedError(document.mime_type)

    def validate_position(self, position: WatermarkPosition) -> None:
        try:
            WatermarkPosition(position.value)
        except ValueError:
            raise InvalidWatermarkPositionError(position.value)

    def generate_verification_hash(self, watermark: Watermark) -> str:
        data = {
            "id": watermark.id,
            "content": watermark.content,
            "position": watermark.position.value,
            "opacity": watermark.opacity,
            "rotation": watermark.rotation,
            "document_id": watermark.document_reference.id,
            "document_checksum": watermark.document_reference.checksum,
            "applied_at": watermark.applied_at.isoformat() if watermark.applied_at else "",
            "applied_by": watermark.applied_by,
            "company_id": watermark.company_id,
        }
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def apply_watermark(self, watermark: Watermark) -> bytes:
        self.validate_document(watermark.document_reference)
        self.validate_position(watermark.position)
        try:
            renderer_name = self._renderers.get(watermark.watermark_type, "render_custom_watermark")
            renderer = getattr(self, renderer_name)
            return renderer(watermark)
        except Exception as exc:
            raise WatermarkEngineError(
                operation="apply_watermark",
                detail=str(exc),
            )

    def render_text_watermark(self, watermark: Watermark) -> bytes:
        rendered = (
            f"--- WATERMARK ---\n"
            f"Content: {watermark.content}\n"
            f"Type: {watermark.watermark_type.value}\n"
            f"Position: {watermark.position.value}\n"
            f"Opacity: {watermark.opacity}\n"
            f"Applied: {watermark.applied_at or 'N/A'}\n"
            f"--- END WATERMARK ---"
        )
        return rendered.encode("utf-8")

    def render_image_watermark(self, watermark: Watermark) -> bytes:
        return self.render_text_watermark(watermark)

    def render_qr_code_watermark(self, watermark: Watermark) -> bytes:
        qr_data = json.dumps({
            "id": watermark.id,
            "content": watermark.content,
            "doc_id": watermark.document_reference.id,
            "company": watermark.company_id,
        }, separators=(",", ":"))
        return qr_data.encode("utf-8")

    def render_barcode_watermark(self, watermark: Watermark) -> bytes:
        barcode_data = watermark.content or watermark.id
        return barcode_data.encode("utf-8")

    def render_stamp_watermark(self, watermark: Watermark) -> bytes:
        stamp = (
            f"[STAMP] {watermark.content}\n"
            f"Date: {watermark.applied_at or datetime.now(timezone.utc).isoformat()}\n"
            f"By: {watermark.applied_by}\n"
            f"Hash: {watermark.verification_hash[:16]}..."
        )
        return stamp.encode("utf-8")

    def render_electronic_seal_watermark(self, watermark: Watermark) -> bytes:
        seal_data = json.dumps({
            "type": "electronic_seal",
            "watermark_id": watermark.id,
            "sealed_by": watermark.applied_by,
            "sealed_at": (watermark.applied_at or datetime.now(timezone.utc)).isoformat(),
            "document_id": watermark.document_reference.id,
            "hash": watermark.verification_hash,
        })
        return seal_data.encode("utf-8")

    def render_timestamp_watermark(self, watermark: Watermark) -> bytes:
        ts = watermark.content or datetime.now(timezone.utc).isoformat()
        return f"Timestamp: {ts}".encode("utf-8")

    def render_document_id_watermark(self, watermark: Watermark) -> bytes:
        return f"Doc ID: {watermark.document_reference.id}".encode("utf-8")

    def render_company_logo_watermark(self, watermark: Watermark) -> bytes:
        return f"[LOGO] Company: {watermark.company_id}".encode("utf-8")

    def render_confidential_watermark(self, watermark: Watermark) -> bytes:
        return b"CONFIDENTIAL"

    def render_draft_watermark(self, watermark: Watermark) -> bytes:
        return b"DRAFT"

    def render_approved_watermark(self, watermark: Watermark) -> bytes:
        return f"APPROVED - {watermark.applied_at or 'N/A'}".encode("utf-8")

    def render_paid_watermark(self, watermark: Watermark) -> bytes:
        return f"PAID - {watermark.applied_at or 'N/A'}".encode("utf-8")

    def render_void_watermark(self, watermark: Watermark) -> bytes:
        return b"VOID"

    def render_copy_watermark(self, watermark: Watermark) -> bytes:
        return b"COPY"

    def render_custom_watermark(self, watermark: Watermark) -> bytes:
        return watermark.content.encode("utf-8") if watermark.content else b""

    def verify_watermark_integrity(self, watermark: Watermark) -> bool:
        expected = self.generate_verification_hash(watermark)
        return expected == watermark.verification_hash

    def supports_mime_type(self, mime_type: str) -> bool:
        return mime_type in self.SUPPORTED_MIME_TYPES

    def list_supported_types(self) -> list[str]:
        return sorted(self.SUPPORTED_MIME_TYPES)

    def estimate_placement(
        self,
        position: WatermarkPosition,
        page_width: int = 595,
        page_height: int = 842,
        margin_x: int = 10,
        margin_y: int = 10,
    ) -> dict[str, int]:
        placements = {
            WatermarkPosition.TOP_LEFT: (margin_x, margin_y),
            WatermarkPosition.TOP_CENTER: (page_width // 2, margin_y),
            WatermarkPosition.TOP_RIGHT: (page_width - margin_x, margin_y),
            WatermarkPosition.MIDDLE_LEFT: (margin_x, page_height // 2),
            WatermarkPosition.MIDDLE_CENTER: (page_width // 2, page_height // 2),
            WatermarkPosition.MIDDLE_RIGHT: (page_width - margin_x, page_height // 2),
            WatermarkPosition.BOTTOM_LEFT: (margin_x, page_height - margin_y),
            WatermarkPosition.BOTTOM_CENTER: (page_width // 2, page_height - margin_y),
            WatermarkPosition.BOTTOM_RIGHT: (page_width - margin_x, page_height - margin_y),
            WatermarkPosition.HEADER: (page_width // 2, margin_y),
            WatermarkPosition.FOOTER: (page_width // 2, page_height - margin_y),
            WatermarkPosition.DIAGONAL: (page_width // 2, page_height // 2),
            WatermarkPosition.TILED: (margin_x, margin_y),
            WatermarkPosition.FULL_PAGE: (page_width // 2, page_height // 2),
        }
        x, y = placements.get(position, (margin_x, margin_y))
        return {"x": x, "y": y, "page_width": page_width, "page_height": page_height}
