from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from finance_platform.watermark.models import (
    WatermarkPosition,
    WatermarkStatus,
    WatermarkType,
    WatermarkSeverity,
)


class DocumentReferenceSchema(BaseModel):
    id: str = ""
    document_type: str = ""
    document_url: str = ""
    checksum: str = ""
    page_count: int = 1
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"
    metadata: dict[str, str] = Field(default_factory=dict)


class WatermarkCreate(BaseModel):
    document_reference: DocumentReferenceSchema = Field(default_factory=DocumentReferenceSchema)
    template_id: Optional[str] = None
    watermark_type: WatermarkType = WatermarkType.TEXT
    content: str = ""
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    severity: WatermarkSeverity = WatermarkSeverity.INFO
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    rotation: float = Field(default=0.0, ge=0.0, le=360.0)
    expires_at: Optional[datetime] = None
    company_id: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class WatermarkUpdate(BaseModel):
    content: Optional[str] = None
    position: Optional[WatermarkPosition] = None
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0)
    rotation: Optional[float] = Field(None, ge=0.0, le=360.0)
    severity: Optional[WatermarkSeverity] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[dict[str, str]] = None


class WatermarkResponse(BaseModel):
    id: str
    document_reference: DocumentReferenceSchema
    template_id: Optional[str] = None
    watermark_type: WatermarkType
    content: str
    position: WatermarkPosition
    status: WatermarkStatus
    severity: WatermarkSeverity
    opacity: float
    rotation: float
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
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, str] = Field(default_factory=dict)

    class Config:
        from_attributes = True

    @property
    def is_active(self) -> bool:
        return self.status not in (
            WatermarkStatus.EXPIRED,
            WatermarkStatus.REVOKED,
            WatermarkStatus.VERIFICATION_FAILED,
        )


class WatermarkListParams(BaseModel):
    status: Optional[WatermarkStatus] = None
    watermark_type: Optional[WatermarkType] = None
    company_id: Optional[str] = None
    document_id: Optional[str] = None
    applied_by: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class WatermarkListResponse(BaseModel):
    items: list[WatermarkResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class WatermarkApplyRequest(BaseModel):
    watermark_id: str
    applied_by: str


class WatermarkVerifyRequest(BaseModel):
    watermark_id: str
    verified_by: str


class WatermarkRevokeRequest(BaseModel):
    watermark_id: str
    revoked_by: str
    reason: str = ""


class WatermarkTemplateCreate(BaseModel):
    name: str
    description: str = ""
    watermark_type: WatermarkType = WatermarkType.TEXT
    content_template: str = ""
    font_family: str = "Arial"
    font_size: int = Field(default=12, ge=6, le=72)
    font_color: str = "#000000"
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    rotation: float = Field(default=0.0, ge=0.0, le=360.0)
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    scale_x: float = Field(default=1.0, ge=0.1, le=10.0)
    scale_y: float = Field(default=1.0, ge=0.1, le=10.0)
    repeat: bool = False
    margin_x: int = Field(default=10, ge=0)
    margin_y: int = Field(default=10, ge=0)
    required: bool = False


class WatermarkTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content_template: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[int] = Field(None, ge=6, le=72)
    font_color: Optional[str] = None
    opacity: Optional[float] = Field(None, ge=0.0, le=1.0)
    rotation: Optional[float] = Field(None, ge=0.0, le=360.0)
    position: Optional[WatermarkPosition] = None
    scale_x: Optional[float] = Field(None, ge=0.1, le=10.0)
    scale_y: Optional[float] = Field(None, ge=0.1, le=10.0)
    repeat: Optional[bool] = None
    margin_x: Optional[int] = Field(None, ge=0)
    margin_y: Optional[int] = Field(None, ge=0)
    required: Optional[bool] = None
    active: Optional[bool] = None


class WatermarkTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    watermark_type: WatermarkType
    content_template: str
    font_family: str
    font_size: int
    font_color: str
    opacity: float
    rotation: float
    position: WatermarkPosition
    scale_x: float
    scale_y: float
    repeat: bool
    margin_x: int
    margin_y: int
    required: bool
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchWatermarkCreate(BaseModel):
    name: str
    description: str = ""
    template_id: Optional[str] = None
    watermark_type: WatermarkType = WatermarkType.TEXT
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    documents: list[DocumentReferenceSchema]
    company_id: str = ""


class BatchWatermarkResponse(BaseModel):
    batch_id: str
    name: str
    status: WatermarkStatus
    total_count: int
    success_count: int
    failure_count: int
    items: list[WatermarkResponse] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplyWatermarkResponse(BaseModel):
    watermark_id: str
    status: WatermarkStatus
    applied_at: Optional[datetime] = None
    verification_hash: str = ""
    message: str = ""


class WatermarkVerificationResponse(BaseModel):
    watermark_id: str
    verified: bool
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    details: dict[str, str] = Field(default_factory=dict)


class WatermarkStats(BaseModel):
    total_watermarks: int = 0
    total_applied: int = 0
    total_verified: int = 0
    total_failed: int = 0
    total_expired: int = 0
    total_revoked: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)
    recent_applications: int = 0


class WatermarkPreviewRequest(BaseModel):
    content: str = ""
    watermark_type: WatermarkType = WatermarkType.TEXT
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    rotation: float = Field(default=0.0, ge=0.0, le=360.0)
    font_family: str = "Arial"
    font_size: int = Field(default=12, ge=6, le=72)
    font_color: str = "#000000"


class BulkApplyRequest(BaseModel):
    document_ids: list[str]
    template_id: Optional[str] = None
    watermark_type: WatermarkType = WatermarkType.TEXT
    content: str = ""
    position: WatermarkPosition = WatermarkPosition.BOTTOM_CENTER
    opacity: float = Field(default=0.5, ge=0.0, le=1.0)
    rotation: float = Field(default=0.0, ge=0.0, le=360.0)
    company_id: str = ""
