from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from finance_platform.logging import get_logger
from finance_platform.ocr.config import OcrConfig
from finance_platform.ocr.engine import OcrEngine
from finance_platform.ocr.extractor import FieldExtractor, InvoiceExtractor, ReceiptExtractor
from finance_platform.ocr.models import (
    ExtractedFields,
    OcrBatchResult,
    OcrDocumentType,
    OcrProcessingStatus,
    OcrRecord,
    OcrRequest,
    OcrResult,
)
from finance_platform.ocr.processor import OcrProcessor
from finance_platform.ocr.validators import OcrValidationResult, OcrValidator

logger = get_logger(__name__)


class OcrService:

    def __init__(
        self,
        config: Optional[OcrConfig] = None,
        processor: Optional[OcrProcessor] = None,
        validator: Optional[OcrValidator] = None,
    ) -> None:
        self.config = config or OcrConfig()
        self.processor = processor or OcrProcessor(self.config)
        self.validator = validator or OcrValidator()
        self._extractors: Dict[OcrDocumentType, FieldExtractor] = {
            OcrDocumentType.INVOICE: InvoiceExtractor(),
            OcrDocumentType.RECEIPT: ReceiptExtractor(),
            OcrDocumentType.CREDIT_NOTE: InvoiceExtractor(),
            OcrDocumentType.DEBIT_NOTE: InvoiceExtractor(),
        }
        self._default_extractor = FieldExtractor()

    def _get_extractor(self, doc_type: OcrDocumentType) -> FieldExtractor:
        return self._extractors.get(doc_type, self._default_extractor)

    async def process_document(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        company_id: str,
        request: Optional[OcrRequest] = None,
        expense_id: Optional[str] = None,
        attachment_id: Optional[str] = None,
    ) -> OcrRecord:
        start_time = time.monotonic()
        request = request or OcrRequest()

        record = OcrRecord(
            id=str(uuid.uuid4()),
            company_id=company_id,
            expense_id=expense_id,
            attachment_id=attachment_id,
            document_type=request.document_type,
            processing_status=OcrProcessingStatus.PROCESSING,
            language=request.language or self.config.language.value,
            ocr_engine=self.config.engine_type.value,
        )

        try:
            result = await self.processor.process(file_data, filename, content_type, request)

            extractor = self._get_extractor(result.document_type)
            extracted = extractor.extract_all(result.raw_text, result.document_type)
            result.extracted_fields = extracted

            validation = self.validator.validate_result(result)

            record.raw_text = result.raw_text
            record.ocr_engine = result.ocr_engine
            record.engine_version = "1.0"
            record.confidence_score = result.confidence.overall
            record.extracted_data = extracted.to_flat_dict() if extracted else {}
            record.processing_time_ms = result.processing_time_ms
            record.page_count = result.page_count
            record.warning_messages = validation.warnings
            record.metadata = result.processing_metadata

            if not validation.is_valid:
                record.processing_status = OcrProcessingStatus.FAILED
                record.error_message = "; ".join(validation.errors)
                if validation.errors:
                    record.error_code = "OCR_VALIDATION_FAILED"
            elif self.validator.validate_for_auto_approval(result, self.config.target_confidence):
                record.processing_status = OcrProcessingStatus.COMPLETED
            else:
                record.processing_status = OcrProcessingStatus.PARTIALLY_COMPLETED

            elapsed = time.monotonic() - start_time
            logger.info(
                "ocr_document_processed",
                record_id=record.id,
                company_id=company_id,
                document_type=request.document_type.value,
                status=record.processing_status.value,
                confidence=record.confidence_score,
                elapsed_ms=round(elapsed * 1000, 2),
            )

            return record

        except Exception as exc:
            elapsed = time.monotonic() - start_time
            record.processing_status = OcrProcessingStatus.FAILED
            record.error_message = str(exc)
            record.error_code = "OCR_PROCESSING_FAILED"
            record.processing_time_ms = round(elapsed * 1000, 2)

            logger.error(
                "ocr_document_failed",
                record_id=record.id,
                company_id=company_id,
                filename=filename,
                error=str(exc),
                elapsed_ms=round(elapsed * 1000, 2),
            )

            return record

    async def process_batch(
        self,
        documents: List[Dict[str, Any]],
        company_id: str,
        default_request: Optional[OcrRequest] = None,
    ) -> OcrBatchResult:
        batch_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        results: List[OcrResult] = []
        total_succeeded = 0
        total_failed = 0

        for doc in documents:
            record = await self.process_document(
                file_data=doc["data"],
                filename=doc.get("filename", "unknown"),
                content_type=doc.get("content_type", "application/octet-stream"),
                company_id=company_id,
                request=doc.get("request", default_request),
                expense_id=doc.get("expense_id"),
                attachment_id=doc.get("attachment_id"),
            )

            if record.processing_status == OcrProcessingStatus.COMPLETED:
                total_succeeded += 1
            elif record.processing_status == OcrProcessingStatus.FAILED:
                total_failed += 1

        completed_at = datetime.now(timezone.utc)
        total_time = (completed_at - started_at).total_seconds() * 1000

        batch_result = OcrBatchResult(
            results=results,
            total_processed=len(documents),
            total_succeeded=total_succeeded,
            total_failed=total_failed,
            total_time_ms=total_time,
            batch_id=batch_id,
            started_at=started_at,
            completed_at=completed_at,
        )

        logger.info(
            "ocr_batch_processed",
            batch_id=batch_id,
            company_id=company_id,
            total=len(documents),
            succeeded=total_succeeded,
            failed=total_failed,
            elapsed_ms=round(total_time, 2),
        )

        return batch_result

    async def process_expense_attachment(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        company_id: str,
        expense_id: str,
        attachment_id: str,
    ) -> OcrRecord:
        request = OcrRequest(document_type=OcrDocumentType.RECEIPT)
        return await self.process_document(
            file_data=file_data,
            filename=filename,
            content_type=content_type,
            company_id=company_id,
            request=request,
            expense_id=expense_id,
            attachment_id=attachment_id,
        )

    async def process_invoice(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        company_id: str,
    ) -> OcrRecord:
        request = OcrRequest(document_type=OcrDocumentType.INVOICE, extract_tables=True)
        return await self.process_document(
            file_data=file_data,
            filename=filename,
            content_type=content_type,
            company_id=company_id,
            request=request,
        )

    async def get_processing_status(self, record_id: str) -> Optional[OcrProcessingStatus]:
        logger.debug("get_processing_status", record_id=record_id)
        return None

    async def retry_processing(
        self,
        record_id: str,
        file_data: bytes,
        filename: str,
        content_type: str,
        company_id: str,
    ) -> OcrRecord:
        record = await self.process_document(
            file_data=file_data,
            filename=filename,
            content_type=content_type,
            company_id=company_id,
        )
        record.retry_count = (record.retry_count or 0) + 1
        return record

    async def review_and_correct(
        self,
        record_id: str,
        corrected_fields: Dict[str, str],
        reviewer_id: str,
        notes: Optional[str] = None,
    ) -> OcrRecord:
        logger.info(
            "ocr_review_completed",
            record_id=record_id,
            reviewer_id=reviewer_id,
            corrected_fields=list(corrected_fields.keys()),
        )
        return OcrRecord(
            id=record_id,
            company_id="",
            reviewed_by=reviewer_id,
            reviewed_at=datetime.now(timezone.utc),
            review_notes=notes,
        )

    async def health_check(self) -> Dict[str, Any]:
        import platform
        engine_healthy = await OcrEngine(self.config).health_check()
        return {
            "service": "ocr",
            "status": "healthy" if engine_healthy else "degraded",
            "engine_type": self.config.engine_type.value,
            "engine_available": engine_healthy,
            "python_version": platform.python_version(),
            "config": {
                "min_confidence": self.config.min_confidence,
                "target_confidence": self.config.target_confidence,
                "max_image_size_mb": self.config.max_image_size_mb,
                "supported_formats": self.config.supported_formats,
                "enable_image_preprocessing": self.config.enable_image_preprocessing,
                "language": self.config.language.value,
            },
        }
