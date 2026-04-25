from __future__ import annotations

import io
import os
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from finance_platform.ocr.config import OcrConfig, OcrEngineType, OcrLanguage
from finance_platform.ocr.models import (
    OcrConfidence,
    OcrDocumentType,
    OcrProcessingStatus,
    OcrResult,
)


class OcrEngineAdapter(ABC):

    def __init__(self, config: OcrConfig) -> None:
        self.config = config

    @abstractmethod
    async def process_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> OcrResult:
        ...

    @abstractmethod
    async def process_pdf(
        self,
        pdf_data: bytes,
        filename: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[OcrResult]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        ...


class TesseractAdapter(OcrEngineAdapter):

    def __init__(self, config: OcrConfig) -> None:
        super().__init__(config)
        self._tesseract_available = False

    async def process_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> OcrResult:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(image_data))
        custom_config = self._build_tesseract_config(options)

        raw_text = pytesseract.image_to_string(image, lang=self.config.language.value, config=custom_config)
        word_data = pytesseract.image_to_data(image, lang=self.config.language.value, config=custom_config, output_type=pytesseract.Output.DICT)

        confidence = self._calculate_confidence(word_data)
        page_count = 1

        ocr_result = OcrResult(
            id=os.urandom(16).hex(),
            document_type=OcrDocumentType.OTHER,
            raw_text=raw_text.strip(),
            confidence=confidence,
            extracted_fields=None,
            processing_time_ms=0,
            processing_status=OcrProcessingStatus.COMPLETED if raw_text.strip() else OcrProcessingStatus.FAILED,
            page_count=page_count,
            ocr_engine=OcrEngineType.TESSERACT.value,
            language=self.config.language.value,
        )
        return ocr_result

    async def process_pdf(
        self,
        pdf_data: bytes,
        filename: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[OcrResult]:
        import pdf2image

        images = pdf2image.convert_from_bytes(pdf_data)
        results: List[OcrResult] = []
        for i, image in enumerate(images):
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            buf.seek(0)
            page_opts = dict(options or {})
            page_opts["page_number"] = i + 1
            result = await self.process_image(buf.getvalue(), f"{filename}_p{i}", "image/png", page_opts)
            result.page_count = len(images)
            results.append(result)
        return results

    async def health_check(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    async def get_supported_languages(self) -> List[str]:
        try:
            import pytesseract
            langs = pytesseract.get_languages()
            return langs or []
        except Exception:
            return []

    def _build_tesseract_config(self, options: Optional[Dict[str, Any]] = None) -> str:
        opts = options or {}
        psm = opts.get("psm_mode", self.config.psm_mode)
        oem = opts.get("oem_mode", self.config.oem_mode)
        config_parts = [f"--psm {psm}", f"--oem {oem}"]
        if self.config.tesseract_config:
            for k, v in self.config.tesseract_config.items():
                config_parts.append(f"-c {k}={v}")
        return " ".join(config_parts)

    def _calculate_confidence(self, word_data: Dict[str, Any]) -> OcrConfidence:
        conf_values = [c for c in word_data.get("conf", []) if isinstance(c, (int, float)) and c >= 0]
        if not conf_values:
            return OcrConfidence(overall=0.0, text=0.0, layout=0.0, field_extraction=0.0)
        avg_conf = sum(conf_values) / len(conf_values) / 100.0
        return OcrConfidence(
            overall=avg_conf,
            text=avg_conf,
            layout=avg_conf * 0.9,
            field_extraction=avg_conf * 0.8,
        )


class OcrEngine:

    def __init__(self, config: Optional[OcrConfig] = None) -> None:
        self.config = config or DEFAULT_OCR_CONFIG
        self._adapter: Optional[OcrEngineAdapter] = None

    async def _get_adapter(self) -> OcrEngineAdapter:
        if self._adapter is not None:
            return self._adapter
        self._adapter = self._create_adapter()
        return self._adapter

    def _create_adapter(self) -> OcrEngineAdapter:
        if self.config.engine_type == OcrEngineType.TESSERACT:
            return TesseractAdapter(self.config)
        return TesseractAdapter(self.config)

    async def process_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> OcrResult:
        adapter = await self._get_adapter()
        return await adapter.process_image(image_data, filename, content_type, options)

    async def process_pdf(
        self,
        pdf_data: bytes,
        filename: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[OcrResult]:
        adapter = await self._get_adapter()
        return await adapter.process_pdf(pdf_data, filename, options)

    async def health_check(self) -> bool:
        try:
            adapter = await self._get_adapter()
            return await adapter.health_check()
        except Exception:
            return False


from finance_platform.ocr.config import DEFAULT_OCR_CONFIG
