from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finance_platform.routes.deps import (
    get_company_id,
    paginate,
    resolve_company_context,
)

router = APIRouter()


@router.post("/documents")
async def apply_watermark(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "watermark-id", "status": "applied", "company_id": ctx.company_id, **body}


@router.get("/documents")
async def list_watermarked_documents(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/documents/{document_id}")
async def get_watermark(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "document_ref": "doc-123",
        "watermark_type": "confidential",
        "text": "CONFIDENTIAL",
        "status": "applied",
        "applied_at": datetime.utcnow().isoformat(),
        "applied_by": ctx.user_id,
        "company_id": ctx.company_id,
    }


@router.post("/documents/{document_id}/verify")
async def verify_watermark(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "verified": True,
        "integrity": "intact",
        "verified_at": datetime.utcnow().isoformat(),
    }


@router.post("/documents/{document_id}/remove")
async def remove_watermark(
    document_id: str,
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "removed": True,
        "reason": body.get("reason", ""),
        "removed_by": ctx.user_id,
        "removed_at": datetime.utcnow().isoformat(),
    }


@router.post("/validate")
async def validate_watermark_integrity(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "valid": True,
        "checksum_match": True,
        "tampered": False,
        "validated_at": datetime.utcnow().isoformat(),
    }
