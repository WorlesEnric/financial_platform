from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import (
    BaseModel,
    TimestampMixin,
)


class OcrExtractionResult(TimestampMixin):
    expense_document_id: str
    company_id: str
    raw_text: str = ""
    ocr_engine: str = ""
    engine_version: str = ""
    confidence_overall: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_text: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_layout: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_field_extraction: float = Field(default=0.0, ge=0.0, le=1.0)
    structured_json: Dict[str, Any] = Field(default_factory=dict)
    page_count: int = Field(default=0, ge=0)
    language: str = "eng"
    processing_time_ms: int = Field(default=0, ge=0)
    is_latest: bool = True
    version_number: int = Field(default=1, ge=1)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0)
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExpenseDocument(TimestampMixin):
    company_id: str
    user_id: str
    filename: str = Field(..., max_length=512)
    content_type: str = Field(..., max_length=128)
    size_bytes: int = Field(..., ge=0)
    storage_key: str
    file_sha256: str = Field(..., min_length=64, max_length=64)
    is_append_only: bool = True
    is_ocr_processed: bool = False
    latest_ocr_result_id: Optional[str] = None
    approved_file_url: Optional[str] = None
    voided_file_url: Optional[str] = None
    approved_file_sha256: Optional[str] = None
    voided_file_sha256: Optional[str] = None


class ExpenseFieldConfirmation(BaseModel):
    expense_document_id: str
    company_id: str
    user_id: str
    field_name: str = Field(..., max_length=128)
    ocr_value: Optional[str] = None
    confirmed_value: str
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_different_from_ocr: bool = False
    confirmed_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
