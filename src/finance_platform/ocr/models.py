from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel, TimestampMixin


class OcrDocumentType(str, Enum):
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PURCHASE_ORDER = "purchase_order"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    BANK_STATEMENT = "bank_statement"
    TAX_FORM = "tax_form"
    CONTRACT = "contract"
    IDENTITY_DOCUMENT = "identity_document"
    OTHER = "other"


class OcrFieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    TAX_ID = "tax_id"
    ACCOUNT_NUMBER = "account_number"
    ROUTING_NUMBER = "routing_number"
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    TABLE = "table"
    BOOLEAN = "boolean"


class OcrProcessingStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    REJECTED = "rejected"


class OcrConfidence(BaseModel):
    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    text: float = Field(default=0.0, ge=0.0, le=1.0)
    layout: float = Field(default=0.0, ge=0.0, le=1.0)
    field_extraction: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def is_reliable(self) -> bool:
        return self.overall >= 0.8

    @property
    def needs_review(self) -> bool:
        return 0.5 <= self.overall < 0.8

    @property
    def is_unreliable(self) -> bool:
        return self.overall < 0.5


class OcrField(BaseModel):
    name: str
    value: Optional[str] = None
    field_type: OcrFieldType = OcrFieldType.TEXT
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_text: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    page_number: Optional[int] = None
    alternates: List[str] = Field(default_factory=list)
    validated: bool = False
    validation_errors: List[str] = Field(default_factory=list)


class ExtractedFields(BaseModel):
    vendor_name: Optional[OcrField] = None
    vendor_address: Optional[OcrField] = None
    vendor_tax_id: Optional[OcrField] = None
    customer_name: Optional[OcrField] = None
    customer_address: Optional[OcrField] = None
    invoice_number: Optional[OcrField] = None
    invoice_date: Optional[OcrField] = None
    due_date: Optional[OcrField] = None
    purchase_order_number: Optional[OcrField] = None
    subtotal: Optional[OcrField] = None
    tax_amount: Optional[OcrField] = None
    tax_rate: Optional[OcrField] = None
    discount_amount: Optional[OcrField] = None
    shipping_amount: Optional[OcrField] = None
    total_amount: Optional[OcrField] = None
    currency: Optional[OcrField] = None
    payment_terms: Optional[OcrField] = None
    payment_method: Optional[OcrField] = None
    bank_account: Optional[OcrField] = None
    routing_number: Optional[OcrField] = None
    line_items: List[OcrField] = Field(default_factory=list)
    additional_fields: Dict[str, OcrField] = Field(default_factory=dict)

    def to_flat_dict(self) -> Dict[str, Optional[str]]:
        result: Dict[str, Optional[str]] = {}
        for field_name, field_obj in self.__iter_fields():
            if field_obj is not None and not isinstance(field_obj, list):
                result[field_name] = field_obj.value
        return result

    def __iter_fields(self):
        for field_name in self.model_fields_set:
            yield field_name, getattr(self, field_name)

    @property
    def confidence(self) -> float:
        scores = []
        for _, field_obj in self.__iter_fields():
            if isinstance(field_obj, OcrField):
                scores.append(field_obj.confidence)
            elif isinstance(field_obj, list):
                scores.extend(f.confidence for f in field_obj if isinstance(f, OcrField))
        return sum(scores) / len(scores) if scores else 0.0


class OcrResult(BaseModel):
    id: str
    document_type: OcrDocumentType
    raw_text: str
    confidence: OcrConfidence
    extracted_fields: ExtractedFields
    processing_time_ms: float
    processing_status: OcrProcessingStatus
    page_count: int = 1
    ocr_engine: str = "unknown"
    language: str = "eng"
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


class OcrRequest(BaseModel):
    document_type: OcrDocumentType = OcrDocumentType.OTHER
    language: str = "eng"
    enhance_image: bool = True
    deskew: bool = True
    detect_orientation: bool = True
    extract_tables: bool = False
    extract_barcodes: bool = False
    page_range: Optional[str] = None
    timeout_seconds: int = 120
    expected_fields: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OcrBatchResult(BaseModel):
    results: List[OcrResult]
    total_processed: int
    total_succeeded: int
    total_failed: int
    total_time_ms: float
    batch_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.total_succeeded / self.total_processed


class OcrRecord(TimestampMixin):
    expense_id: Optional[str] = None
    attachment_id: Optional[str] = None
    company_id: str
    document_type: OcrDocumentType = OcrDocumentType.OTHER
    processing_status: OcrProcessingStatus = OcrProcessingStatus.PENDING
    raw_text: str = ""
    ocr_engine: str = ""
    engine_version: str = ""
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float = 0
    page_count: int = 0
    language: str = "eng"
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    warning_messages: List[str] = Field(default_factory=list)
    retry_count: int = 0
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
