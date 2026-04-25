from __future__ import annotations

import io
import time
from typing import Any, Dict, List, Optional, Tuple

from finance_platform.logging import get_logger
from finance_platform.ocr.config import OcrConfig
from finance_platform.ocr.engine import OcrEngine
from finance_platform.ocr.models import (
    OcrConfidence,
    OcrDocumentType,
    OcrProcessingStatus,
    OcrRequest,
    OcrResult,
)

logger = get_logger(__name__)


class ImagePreprocessor:

    def __init__(self, config: OcrConfig) -> None:
        self.config = config

    async def preprocess(
        self,
        image_data: bytes,
        filename: str,
        content_type: str,
    ) -> Tuple[bytes, Dict[str, Any]]:
        metadata: Dict[str, Any] = {
            "original_size_bytes": len(image_data),
            "preprocessing_applied": [],
        }
        if not self.config.enable_image_preprocessing:
            return image_data, metadata

        try:
            from PIL import Image, ImageEnhance, ImageFilter

            image = Image.open(io.BytesIO(image_data))
            original_mode = image.mode

            if image.mode != "RGB":
                image = image.convert("RGB")

            if self.config.enable_deskew:
                image = self._deskew(image)
                metadata["preprocessing_applied"].append("deskew")

            if self.config.enable_orientation_detection:
                image = self._correct_orientation(image)
                metadata["preprocessing_applied"].append("orientation_correction")

            image = self._enhance_image(image)
            metadata["preprocessing_applied"].append("enhancement")

            buf = io.BytesIO()
            save_format = "PNG" if content_type in ("image/png",) else "JPEG"
            image.save(buf, format=save_format, optimize=True)
            buf.seek(0)
            processed_data = buf.getvalue()

            metadata["processed_size_bytes"] = len(processed_data)
            metadata["original_mode"] = original_mode
            metadata["processed_mode"] = image.mode
            metadata["dimensions"] = {"width": image.width, "height": image.height}

            return processed_data, metadata

        except ImportError:
            logger.warning("PIL not available, skipping image preprocessing")
            metadata["warning"] = "PIL not available, preprocessing skipped"
            return image_data, metadata
        except Exception as exc:
            logger.error("image_preprocessing_failed", error=str(exc), filename=filename)
            metadata["error"] = str(exc)
            return image_data, metadata

    def _deskew(self, image: Any) -> Any:
        try:
            from PIL import ImageFilter

            grayscale = image.convert("L")
            grayscale = grayscale.filter(ImageFilter.MedianFilter(size=3))
            from PIL import ImageOps

            inverted = ImageOps.invert(grayscale)
            import math

            w, h = inverted.size
            if w > 2000 or h > 2000:
                scale = 2000 / max(w, h)
                inverted = inverted.resize((int(w * scale), int(h * scale)))
            try:
                import pytesseract
                osd = pytesseract.image_to_osd(inverted, output_type=pytesseract.Output.DICT)
                angle = osd.get("rotate", 0.0)
                if abs(angle) > 0.5:
                    image = image.rotate(angle, expand=True, fillcolor=(255, 255, 255))
            except Exception:
                pass
        except Exception:
            pass
        return image

    def _correct_orientation(self, image: Any) -> Any:
        try:
            import pytesseract
            grayscale = image.convert("L")
            osd = pytesseract.image_to_osd(grayscale, output_type=pytesseract.Output.DICT)
            angle = osd.get("rotate", 0)
            if angle != 0:
                image = image.rotate(angle, expand=True, fillcolor=(255, 255, 255))
        except Exception:
            pass
        return image

    def _enhance_image(self, image: Any) -> Any:
        try:
            from PIL import ImageEnhance, ImageFilter

            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            image = image.filter(ImageFilter.SHARPEN)
        except Exception:
            pass
        return image


class OcrProcessor:

    def __init__(
        self,
        config: Optional[OcrConfig] = None,
        engine: Optional[OcrEngine] = None,
    ) -> None:
        self.config = config or OcrConfig()
        self.engine = engine or OcrEngine(self.config)
        self.preprocessor = ImagePreprocessor(self.config)

    async def process(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        request: Optional[OcrRequest] = None,
    ) -> OcrResult:
        start_time = time.monotonic()
        request = request or OcrRequest()
        metadata: Dict[str, Any] = {}

        try:
            is_pdf = content_type == "application/pdf" or filename.lower().endswith(".pdf")

            if not self._is_format_supported(filename, content_type):
                from finance_platform.errors import OcrError
                raise OcrError(
                    f"Unsupported format: {content_type or filename}",
                    code="OCR_UNSUPPORTED_FORMAT",
                )

            self._validate_file_size(file_data)

            if is_pdf:
                page_results = await self.engine.process_pdf(file_data, filename, options={"request": request})
                return self._merge_page_results(page_results, start_time, metadata, request.document_type)
            else:
                processed_data, preprocess_meta = await self.preprocessor.preprocess(
                    file_data, filename, content_type
                )
                if preprocess_meta:
                    metadata["preprocessing"] = preprocess_meta

                result = await self.engine.process_image(
                    processed_data, filename, content_type, options={"request": request}
                )

                elapsed = time.monotonic() - start_time
                result.processing_time_ms = round(elapsed * 1000, 2)
                result.document_type = request.document_type
                result.language = request.language or self.config.language.value
                result.processing_metadata = metadata

                return result

        except Exception as exc:
            elapsed = time.monotonic() - start_time
            logger.error(
                "ocr_processing_failed",
                filename=filename,
                error=str(exc),
                elapsed_ms=round(elapsed * 1000, 2),
            )
            from finance_platform.errors import OcrProcessingError
            raise OcrProcessingError(str(exc)) from exc

    def _is_format_supported(self, filename: str, content_type: Optional[str]) -> bool:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if content_type:
            if "pdf" in content_type:
                return "pdf" in self.config.supported_formats
            if "image" in content_type:
                return True
        return ext in self.config.supported_formats

    def _validate_file_size(self, data: bytes) -> None:
        max_bytes = int(self.config.max_image_size_mb * 1024 * 1024)
        if len(data) > max_bytes:
            from finance_platform.errors import OcrError
            raise OcrError(
                f"File size {len(data) / (1024*1024):.1f}MB exceeds limit of {self.config.max_image_size_mb}MB",
                code="OCR_PROCESSING_FAILED",
            )

    def _merge_page_results(self, results: List[OcrResult], start_time: float, metadata: Dict[str, Any], doc_type: OcrDocumentType) -> OcrResult:
        if not results:
            from finance_platform.errors import OcrProcessingError
            raise OcrProcessingError("No pages processed from PDF")

        all_text = "\n\n".join(r.raw_text for r in results)
        avg_confidence = OcrConfidence(
            overall=sum(r.confidence.overall for r in results) / len(results),
            text=sum(r.confidence.text for r in results) / len(results),
            layout=sum(r.confidence.layout for r in results) / len(results),
            field_extraction=sum(r.confidence.field_extraction for r in results) / len(results),
        )
        total_time = time.monotonic() - start_time
        page_count = len(results)
        any_failed = any(r.processing_status == OcrProcessingStatus.FAILED for r in results)

        first = results[0]
        merged = OcrResult(
            id=first.id,
            document_type=doc_type,
            raw_text=all_text,
            confidence=avg_confidence,
            extracted_fields=first.extracted_fields,
            processing_time_ms=round(total_time * 1000, 2),
            processing_status=OcrProcessingStatus.PARTIALLY_COMPLETED if any_failed else OcrProcessingStatus.COMPLETED,
            page_count=page_count,
            ocr_engine=first.ocr_engine,
            language=first.language,
            warnings=[w for r in results for w in r.warnings],
            processing_metadata=metadata,
        )
        return merged
