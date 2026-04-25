from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from finance_platform.watermark.models import (
    Watermark,
    WatermarkStatus,
    WatermarkType,
    WatermarkPosition,
    DocumentReference,
)
from finance_platform.watermark.exceptions import WatermarkVerificationFailedError


class WatermarkDetector:
    def __init__(self) -> None:
        self._detection_methods: dict[WatermarkType, str] = {
            WatermarkType.TEXT: "detect_text_watermark",
            WatermarkType.IMAGE: "detect_image_watermark",
            WatermarkType.QR_CODE: "detect_qr_code_watermark",
            WatermarkType.BARCODE: "detect_barcode_watermark",
            WatermarkType.STAMP: "detect_stamp_watermark",
            WatermarkType.ELECTRONIC_SEAL: "detect_electronic_seal_watermark",
            WatermarkType.TIMESTAMP: "detect_timestamp_watermark",
            WatermarkType.DOCUMENT_ID: "detect_document_id_watermark",
            WatermarkType.COMPANY_LOGO: "detect_company_logo_watermark",
            WatermarkType.CONFIDENTIAL: "detect_confidential_watermark",
            WatermarkType.DRAFT: "detect_draft_watermark",
            WatermarkType.APPROVED: "detect_approved_watermark",
            WatermarkType.PAID: "detect_paid_watermark",
            WatermarkType.VOID: "detect_void_watermark",
            WatermarkType.COPY: "detect_copy_watermark",
            WatermarkType.CUSTOM: "detect_custom_watermark",
        }

    def detect(self, document_content: bytes, watermark: Watermark) -> dict:
        try:
            method_name = self._detection_methods.get(watermark.watermark_type, "detect_custom_watermark")
            method = getattr(self, method_name)
            result = method(document_content, watermark)
            return result
        except WatermarkVerificationFailedError:
            raise
        except Exception as exc:
            raise WatermarkVerificationFailedError(
                watermark_id=watermark.id,
                reason=f"Detection failed: {exc}",
            )

    def verify(self, document_content: bytes, watermark: Watermark) -> bool:
        result = self.detect(document_content, watermark)
        return result.get("present", False)

    def detect_text_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = watermark.content.lower() in content_str.lower()
        return {
            "present": present,
            "confidence": 0.95 if present else 0.0,
            "method": "text_match",
            "details": {"matched_string": watermark.content[:50]} if present else {},
        }

    def detect_image_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        return {
            "present": len(document_content) > 0,
            "confidence": 0.7,
            "method": "image_analysis",
            "details": {"size_bytes": len(document_content)},
        }

    def detect_qr_code_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = watermark.id in content_str or watermark.content in content_str
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "qr_decode",
            "details": {"data_found": present},
        }

    def detect_barcode_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        return self.detect_text_watermark(document_content, watermark)

    def detect_stamp_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "[STAMP]" in content_str and watermark.content in content_str
        return {
            "present": present,
            "confidence": 0.85 if present else 0.0,
            "method": "stamp_detection",
            "details": {"stamp_found": present},
        }

    def detect_electronic_seal_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "electronic_seal" in content_str and watermark.id in content_str
        return {
            "present": present,
            "confidence": 0.95 if present else 0.0,
            "method": "seal_verification",
            "details": {"seal_found": present},
        }

    def detect_timestamp_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "Timestamp:" in content_str
        return {
            "present": present,
            "confidence": 0.8 if present else 0.0,
            "method": "timestamp_detection",
            "details": {"timestamp_found": present},
        }

    def detect_document_id_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        doc_id = watermark.document_reference.id
        present = f"Doc ID: {doc_id}" in content_str
        return {
            "present": present,
            "confidence": 0.95 if present else 0.0,
            "method": "document_id_match",
            "details": {"document_id": doc_id} if present else {},
        }

    def detect_company_logo_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = watermark.company_id in content_str and "[LOGO]" in content_str
        return {
            "present": present,
            "confidence": 0.75 if present else 0.0,
            "method": "logo_detection",
            "details": {"company": watermark.company_id} if present else {},
        }

    def detect_confidential_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "CONFIDENTIAL" in content_str.upper()
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "keyword_detection",
            "details": {},
        }

    def detect_draft_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "DRAFT" in content_str.upper()
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "keyword_detection",
            "details": {},
        }

    def detect_approved_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "APPROVED" in content_str.upper()
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "keyword_detection",
            "details": {},
        }

    def detect_paid_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "PAID" in content_str.upper()
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "keyword_detection",
            "details": {},
        }

    def detect_void_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "VOID" in content_str.upper()
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "keyword_detection",
            "details": {},
        }

    def detect_copy_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = "COPY" in content_str.upper()
        return {
            "present": present,
            "confidence": 0.9 if present else 0.0,
            "method": "keyword_detection",
            "details": {},
        }

    def detect_custom_watermark(self, document_content: bytes, watermark: Watermark) -> dict:
        content_str = document_content.decode("utf-8", errors="replace")
        present = watermark.content in content_str if watermark.content else False
        return {
            "present": present,
            "confidence": 0.7 if present else 0.0,
            "method": "custom_detection",
            "details": {"content_found": present},
        }

    def scan_document(self, document_content: bytes) -> list[dict]:
        findings: list[dict] = []
        detectors = [
            ("CONFIDENTIAL", "confidential"),
            ("DRAFT", "draft"),
            ("APPROVED", "approved"),
            ("PAID", "paid"),
            ("VOID", "void"),
            ("COPY", "copy"),
            ("[STAMP]", "stamp"),
            ("Timestamp:", "timestamp"),
        ]
        content_str = document_content.decode("utf-8", errors="replace").upper()
        for keyword, label in detectors:
            if keyword.upper() in content_str:
                findings.append({
                    "type": label,
                    "confidence": 0.8,
                    "method": "scan",
                    "keyword": keyword,
                })
        return findings
