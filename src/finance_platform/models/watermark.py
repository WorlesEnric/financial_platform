from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field

from finance_platform.models.base import BaseModel, TimestampMixin


class WatermarkType(str, Enum):
    APPROVED = "approved"
    VOIDED = "voided"
    PROCESSED = "processed"
    ARCHIVED = "archived"


class WatermarkStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Watermark(BaseModel):
    document_id: str
    watermark_type: WatermarkType
    status: WatermarkStatus = WatermarkStatus.PENDING
    source_file_url: str
    source_file_sha256: str
    output_file_url: Optional[str] = None
    output_file_sha256: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    overlay_data: Dict[str, Any] = Field(default_factory=dict)
    failure_reason: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WatermarkTemplate(BaseModel):
    name: str
    watermark_type: WatermarkType
    position: str = "bottom-right"
    font_size: int = 24
    opacity: float = 0.5
    text_template: str
    color: str = "#FF0000"
    rotation: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
