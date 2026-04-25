from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from finance_platform.watermark.models import Watermark, WatermarkState, WatermarkType
from finance_platform.watermark.repository import WatermarkRepository
from finance_platform.watermark.strategies import get_watermark_strategy


class WatermarkVerifier:
    def __init__(self, repository: WatermarkRepository) -> None:
        self._repository = repository

    def verify_integrity(self, watermark: Watermark) -> bool:
        strategy = get_watermark_strategy(watermark.watermark_type)
        expected_hash = strategy.compute_hash(watermark)
        return watermark.sha256_hash == expected_hash

    def verify_document_chain(
        self, document_id: str, watermark_type: Optional[WatermarkType] = None
    ) -> list[dict]:
        watermarks = self._repository.list_by_document(
            document_id=document_id, watermark_type=watermark_type
        )
        results = []
        for w in watermarks:
            valid = self.verify_integrity(w)
            chain_valid = self._verify_chain_link(w)
            results.append(
                {
                    "watermark_id": w.id,
                    "watermark_type": w.watermark_type.value,
                    "state": w.state.value,
                    "hash_valid": valid,
                    "chain_valid": chain_valid,
                    "sha256_hash": w.sha256_hash,
                    "applied_at": w.applied_at.isoformat() if w.applied_at else None,
                }
            )
        return results

    def _verify_chain_link(self, watermark: Watermark) -> bool:
        expected_chain = watermark.chain_hash()
        raw = (
            f"{watermark.id}|{watermark.document_id}|{watermark.watermark_type.value}|"
            f"{watermark.sha256_hash}|{watermark.previous_hash or ''}|{watermark.applied_at or ''}"
        )
        computed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return computed == expected_chain

    def verify_watermark_active(
        self, document_id: str, watermark_type: WatermarkType
    ) -> Optional[Watermark]:
        active = self._repository.find_active_for_document(
            document_id, watermark_type
        )
        if active is None:
            return None
        if active.is_expired:
            return None
        return active

    def verify_hash_against_document(
        self, document_id: str, expected_hash: str
    ) -> tuple[bool, Optional[Watermark], Optional[str]]:
        watermarks = self._repository.list_by_document(document_id)
        for w in watermarks:
            if w.sha256_hash == expected_hash:
                return True, w, w.sha256_hash
            if self.verify_integrity(w):
                return True, w, w.sha256_hash
        return False, None, None

    def bulk_verify(
        self, watermark_ids: list[str]
    ) -> list[dict]:
        results = []
        for wid in watermark_ids:
            watermark = self._repository.get(wid)
            if watermark is None:
                results.append(
                    {
                        "watermark_id": wid,
                        "exists": False,
                        "hash_valid": False,
                        "chain_valid": False,
                        "state": None,
                    }
                )
                continue
            results.append(
                {
                    "watermark_id": wid,
                    "exists": True,
                    "hash_valid": self.verify_integrity(watermark),
                    "chain_valid": self._verify_chain_link(watermark),
                    "state": watermark.state.value,
                }
            )
        return results

    def verify_all_for_document(self, document_id: str) -> dict:
        watermarks = self._repository.list_by_document(document_id)
        all_valid = True
        details = []
        for w in watermarks:
            hash_valid = self.verify_integrity(w)
            chain_valid = self._verify_chain_link(w)
            expired = w.is_expired
            if not (hash_valid and chain_valid and not expired):
                all_valid = False
            details.append(
                {
                    "watermark_id": w.id,
                    "watermark_type": w.watermark_type.value,
                    "state": w.state.value,
                    "hash_valid": hash_valid,
                    "chain_valid": chain_valid,
                    "expired": expired,
                }
            )
        return {
            "document_id": document_id,
            "all_valid": all_valid,
            "watermark_count": len(watermarks),
            "details": details,
        }

    def check_if_document_is_voided(self, document_id: str) -> bool:
        active_void = self.verify_watermark_active(
            document_id, WatermarkType.VOID
        )
        return active_void is not None

    def check_if_document_is_approved(self, document_id: str) -> bool:
        active_approval = self.verify_watermark_active(
            document_id, WatermarkType.APPROVED
        )
        return active_approval is not None
