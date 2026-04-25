from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class WatermarkType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    QR_CODE = "qr_code"
    BARCODE = "barcode"
    STAMP = "stamp"
    ELECTRONIC_SEAL = "electronic_seal"
    TIMESTAMP = "timestamp"
    DOCUMENT_ID = "document_id"
    COMPANY_LOGO = "company_logo"
    CONFIDENTIAL = "confidential"
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"
    VOID = "void"
    COPY = "copy"
    CUSTOM = "custom"


class WatermarkPosition(str, Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    MIDDLE_CENTER = "middle_center"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    TILED = "tiled"
    DIAGONAL = "diagonal"
    HEADER = "header"
    FOOTER = "footer"
    FULL_PAGE = "full_page"


class WatermarkStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    VERIFIED = "verified"
    VERIFICATION_FAILED = "verification_failed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    FAILED = "failed"


class WatermarkSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKING = "blocking"


@dataclass
class DocumentReference:
    id: str = ""
    document_type: str = ""
    document_url: str = ""
    checksum: str = ""
    page_count: int = 1
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class WatermarkTemplate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    watermark_type: WatermarkType = WatermarkType.TEXT
    content_template: str = ""
    font_family: str = "Arial"
    font_size: int = 12
    font_color: str = "#000000"
    opacity: float = 0.5
    rotation: float = 0.0
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    scale_x: float = 1.0
    scale_y: float = 1.0
    repeat: bool = False
    margin_x: int = 10
    margin_y: int = 10
    required: bool = False
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def render_content(self, variables: dict[str, str]) -> str:
        result = self.content_template
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, value)
        return result


@dataclass
class Watermark:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_reference: DocumentReference = field(default_factory=DocumentReference)
    template_id: Optional[str] = None
    watermark_type: WatermarkType = WatermarkType.TEXT
    content: str = ""
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    status: WatermarkStatus = WatermarkStatus.PENDING
    severity: WatermarkSeverity = WatermarkSeverity.INFO
    opacity: float = 0.5
    rotation: float = 0.0
    applied_by: str = ""
    applied_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_hash: str = ""
    expires_at: Optional[datetime] = None
    revoked_by: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: str = ""
    company_id: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = field(default_factory=dict)

    def apply(self, applied_by: str) -> None:
        self.status = WatermarkStatus.APPLIED
        self.applied_by = applied_by
        self.applied_at = datetime.now(timezone.utc)
        self.updated_at = self.applied_at

    def mark_verified(self, verified_by: str) -> None:
        self.status = WatermarkStatus.VERIFIED
        self.verified_by = verified_by
        self.verified_at = datetime.now(timezone.utc)
        self.updated_at = self.verified_at

    def mark_verification_failed(self, reason: str) -> None:
        self.status = WatermarkStatus.VERIFICATION_FAILED
        self.metadata["verification_failure_reason"] = reason
        self.updated_at = datetime.now(timezone.utc)

    def revoke(self, revoked_by: str, reason: str) -> None:
        self.status = WatermarkStatus.REVOKED
        self.revoked_by = revoked_by
        self.revoked_at = datetime.now(timezone.utc)
        self.revocation_reason = reason
        self.updated_at = self.revoked_at

    def expire(self) -> None:
        self.status = WatermarkStatus.EXPIRED
        self.updated_at = datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        if self.status in (WatermarkStatus.EXPIRED, WatermarkStatus.REVOKED, WatermarkStatus.VERIFICATION_FAILED):
            return False
        if self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    @property
    def is_applied(self) -> bool:
        return self.status in (WatermarkStatus.APPLIED, WatermarkStatus.VERIFIED)


@dataclass
class WatermarkBatchItem:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    batch_id: str = ""
    document_reference: DocumentReference = field(default_factory=DocumentReference)
    watermark_id: Optional[str] = None
    status: WatermarkStatus = WatermarkStatus.PENDING
    error_message: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WatermarkBatch:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    template_id: Optional[str] = None
    watermark_type: WatermarkType = WatermarkType.TEXT
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    items: list[WatermarkBatchItem] = field(default_factory=list)
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    status: WatermarkStatus = WatermarkStatus.PENDING
    company_id: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: dict[str, str] = field(default_factory=dict)

    def add_item(self, item: WatermarkBatchItem) -> None:
        item.batch_id = self.id
        self.items.append(item)
        self.total_count = len(self.items)

    def record_success(self) -> None:
        self.success_count += 1
        if self.success_count + self.failure_count >= self.total_count:
            self.status = WatermarkStatus.APPLIED
            self.completed_at = datetime.now(timezone.utc)

    def record_failure(self, error: str) -> None:
        self.failure_count += 1
        self.metadata["last_error"] = error
        if self.success_count + self.failure_count >= self.total_count:
            self.status = WatermarkStatus.FAILED if self.failure_count > 0 else WatermarkStatus.APPLIED
            self.completed_at = datetime.now(timezone.utc)
