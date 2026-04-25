from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OcrEngineType(str, Enum):
    TESSERACT = "tesseract"
    GOOGLE_VISION = "google_vision"
    AWS_TEXTRACT = "aws_textract"
    AZURE_FORM_RECOGNIZER = "azure_form_recognizer"
    OCR_SPACE = "ocr_space"
    CUSTOM = "custom"


class OcrLanguage(str, Enum):
    ENGLISH = "eng"
    SPANISH = "spa"
    FRENCH = "fra"
    GERMAN = "deu"
    ITALIAN = "ita"
    PORTUGUESE = "por"
    DUTCH = "nld"
    JAPANESE = "jpn"
    KOREAN = "kor"
    CHINESE_SIMPLIFIED = "chi_sim"
    CHINESE_TRADITIONAL = "chi_tra"
    ARABIC = "ara"
    RUSSIAN = "rus"
    HINDI = "hin"
    THAI = "tha"
    VIETNAMESE = "vie"
    TURKISH = "tur"
    POLISH = "pol"
    SWEDISH = "swe"
    DANISH = "dan"
    NORWEGIAN = "nor"
    FINNISH = "fin"
    GREEK = "ell"
    HEBREW = "heb"


@dataclass
class OcrConfig:
    engine_type: OcrEngineType = OcrEngineType.TESSERACT
    language: OcrLanguage = OcrLanguage.ENGLISH
    tesseract_path: Optional[str] = None
    tesseract_config: Dict[str, Any] = field(default_factory=dict)
    google_credentials_path: Optional[str] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: str = "us-east-1"
    azure_endpoint: Optional[str] = None
    azure_key: Optional[str] = None
    ocr_space_api_key: Optional[str] = None
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_seconds: int = 120
    min_confidence: float = 0.5
    target_confidence: float = 0.8
    enable_image_preprocessing: bool = True
    enable_deskew: bool = True
    enable_orientation_detection: bool = True
    enable_table_extraction: bool = False
    enable_barcode_detection: bool = False
    max_image_size_mb: float = 20.0
    supported_formats: List[str] = field(
        default_factory=lambda: ["png", "jpg", "jpeg", "tiff", "tif", "bmp", "pdf", "gif"]
    )
    psm_mode: int = 3
    oem_mode: int = 3
    custom_engine_module: Optional[str] = None
    custom_engine_class: Optional[str] = None
    batch_size: int = 10
    processing_pool_size: int = 4
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600


DEFAULT_OCR_CONFIG = OcrConfig()
