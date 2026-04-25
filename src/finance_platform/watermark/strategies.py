from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from finance_platform.watermark.models import (
    Watermark,
    WatermarkOverlay,
    WatermarkPayload,
    WatermarkPosition,
    WatermarkResult,
    WatermarkState,
    WatermarkType,
)


class WatermarkStrategy:
    def create_watermark(
        self,
        document_id: str,
        document_type: str,
        company_id: str,
        applied_by: str,
        applied_by_name: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> Watermark:
        raise NotImplementedError

    def build_overlay(
        self, watermark: Watermark, payload: WatermarkPayload
    ) -> WatermarkOverlay:
        raise NotImplementedError

    def compute_hash(self, watermark: Watermark) -> str:
        raise NotImplementedError

    @property
    def watermark_type(self) -> WatermarkType:
        raise NotImplementedError

    @property
    def default_position(self) -> WatermarkPosition:
        return WatermarkPosition.CENTER

    def validate(self, watermark: Watermark) -> None:
        pass


class ApprovalWatermarkStrategy(WatermarkStrategy):
    @property
    def watermark_type(self) -> WatermarkType:
        return WatermarkType.APPROVED

    @property
    def default_position(self) -> WatermarkPosition:
        return WatermarkPosition.DIAGONAL

    def create_watermark(
        self,
        document_id: str,
        document_type: str,
        company_id: str,
        applied_by: str,
        applied_by_name: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> Watermark:
        now = datetime.now(timezone.utc)
        payload = WatermarkPayload(
            document_id=document_id,
            document_type=document_type,
            reviewer_id=applied_by,
            reviewer_name=applied_by_name,
            company_id=company_id,
            watermark_type=WatermarkType.APPROVED,
            sha256_hash="",
            timestamp=now,
            metadata=metadata or {},
        )
        overlay = payload.to_overlay(self.default_position)
        overlay.color = "#006600"
        overlay.opacity = 0.35
        overlay.font_size = 36
        overlay.rotation = -30.0

        watermark = Watermark(
            id=str(uuid.uuid4()),
            document_id=document_id,
            document_type=document_type,
            company_id=company_id,
            watermark_type=WatermarkType.APPROVED,
            state=WatermarkState.PENDING,
            overlay=overlay,
            applied_by=applied_by,
            applied_by_name=applied_by_name,
            position=self.default_position,
            metadata=metadata or {},
        )
        raw = f"{watermark.id}|{document_id}|{applied_by}|{now.isoformat()}|APPROVED"
        watermark.sha256_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        watermark.payload = payload
        return watermark

    def build_overlay(
        self, watermark: Watermark, payload: WatermarkPayload
    ) -> WatermarkOverlay:
        return WatermarkOverlay(
            text=f"APPROVED - {payload.reviewer_name} - {payload.formatted_timestamp}",
            font_size=36,
            opacity=0.35,
            rotation=-30.0,
            position=WatermarkPosition.DIAGONAL,
            color="#006600",
            bold=True,
            stamp_format="APPROVED {reviewer} {timestamp}",
        )

    def compute_hash(self, watermark: Watermark) -> str:
        raw = (
            f"{watermark.id}|{watermark.document_id}|{watermark.applied_by}|"
            f"{watermark.applied_at or ''}|APPROVED"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class VoidWatermarkStrategy(WatermarkStrategy):
    @property
    def watermark_type(self) -> WatermarkType:
        return WatermarkType.VOID

    @property
    def default_position(self) -> WatermarkPosition:
        return WatermarkPosition.DIAGONAL

    def create_watermark(
        self,
        document_id: str,
        document_type: str,
        company_id: str,
        applied_by: str,
        applied_by_name: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> Watermark:
        now = datetime.now(timezone.utc)
        payload = WatermarkPayload(
            document_id=document_id,
            document_type=document_type,
            reviewer_id=applied_by,
            reviewer_name=applied_by_name,
            company_id=company_id,
            watermark_type=WatermarkType.VOID,
            sha256_hash="",
            timestamp=now,
            metadata=metadata or {},
        )
        overlay = payload.to_overlay(self.default_position)
        overlay.color = "#CC0000"
        overlay.opacity = 0.45
        overlay.font_size = 42
        overlay.rotation = -30.0

        watermark = Watermark(
            id=str(uuid.uuid4()),
            document_id=document_id,
            document_type=document_type,
            company_id=company_id,
            watermark_type=WatermarkType.VOID,
            state=WatermarkState.PENDING,
            overlay=overlay,
            applied_by=applied_by,
            applied_by_name=applied_by_name,
            position=self.default_position,
            metadata=metadata or {},
        )
        raw = f"{watermark.id}|{document_id}|{applied_by}|{now.isoformat()}|VOID"
        watermark.sha256_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        watermark.payload = payload
        return watermark

    def build_overlay(
        self, watermark: Watermark, payload: WatermarkPayload
    ) -> WatermarkOverlay:
        return WatermarkOverlay(
            text=f"VOID - {payload.reviewer_name} - {payload.formatted_timestamp}",
            font_size=42,
            opacity=0.45,
            rotation=-30.0,
            position=WatermarkPosition.DIAGONAL,
            color="#CC0000",
            bold=True,
            stamp_format="VOID {reviewer} {timestamp}",
        )

    def compute_hash(self, watermark: Watermark) -> str:
        raw = (
            f"{watermark.id}|{watermark.document_id}|{watermark.applied_by}|"
            f"{watermark.applied_at or ''}|VOID"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ArchiveWatermarkStrategy(WatermarkStrategy):
    @property
    def watermark_type(self) -> WatermarkType:
        return WatermarkType.ARCHIVE

    @property
    def default_position(self) -> WatermarkPosition:
        return WatermarkPosition.BOTTOM_RIGHT

    def create_watermark(
        self,
        document_id: str,
        document_type: str,
        company_id: str,
        applied_by: str,
        applied_by_name: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> Watermark:
        now = datetime.now(timezone.utc)
        payload = WatermarkPayload(
            document_id=document_id,
            document_type=document_type,
            reviewer_id=applied_by,
            reviewer_name=applied_by_name,
            company_id=company_id,
            watermark_type=WatermarkType.ARCHIVE,
            sha256_hash="",
            timestamp=now,
            metadata=metadata or {},
        )
        overlay = payload.to_overlay(self.default_position)
        overlay.color = "#333333"
        overlay.opacity = 0.3
        overlay.font_size = 18
        overlay.rotation = 0.0

        watermark = Watermark(
            id=str(uuid.uuid4()),
            document_id=document_id,
            document_type=document_type,
            company_id=company_id,
            watermark_type=WatermarkType.ARCHIVE,
            state=WatermarkState.PENDING,
            overlay=overlay,
            applied_by=applied_by,
            applied_by_name=applied_by_name,
            position=self.default_position,
            metadata=metadata or {},
        )
        raw = f"{watermark.id}|{document_id}|{applied_by}|{now.isoformat()}|ARCHIVE"
        watermark.sha256_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        watermark.payload = payload
        return watermark

    def build_overlay(
        self, watermark: Watermark, payload: WatermarkPayload
    ) -> WatermarkOverlay:
        return WatermarkOverlay(
            text=f"ARCHIVE - {payload.reviewer_name} - {payload.formatted_timestamp}",
            font_size=18,
            opacity=0.3,
            rotation=0.0,
            position=WatermarkPosition.BOTTOM_RIGHT,
            color="#333333",
            bold=False,
            stamp_format="ARCHIVE {reviewer} {timestamp}",
        )

    def compute_hash(self, watermark: Watermark) -> str:
        raw = (
            f"{watermark.id}|{watermark.document_id}|{watermark.applied_by}|"
            f"{watermark.applied_at or ''}|ARCHIVE"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


_strategy_registry: dict[WatermarkType, type[WatermarkStrategy]] = {
    WatermarkType.APPROVED: ApprovalWatermarkStrategy,
    WatermarkType.VOID: VoidWatermarkStrategy,
    WatermarkType.ARCHIVE: ArchiveWatermarkStrategy,
}


def get_watermark_strategy(
    watermark_type: WatermarkType,
) -> WatermarkStrategy:
    strategy_cls = _strategy_registry.get(watermark_type)
    if strategy_cls is None:
        raise ValueError(f"No watermark strategy registered for type '{watermark_type.value}'")
    return strategy_cls()


def register_watermark_strategy(
    watermark_type: WatermarkType, strategy_cls: type[WatermarkStrategy]
) -> None:
    _strategy_registry[watermark_type] = strategy_cls
