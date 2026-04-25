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
async def submit_ocr_document(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "doc-id", "status": "queued", "company_id": ctx.company_id, **body}


@router.get("/documents")
async def list_ocr_documents(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.get("/documents/{document_id}")
async def get_ocr_document(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "filename": "receipt.pdf",
        "status": "completed",
        "ocr_text": "Extracted text content...",
        "confidence": 0.95,
        "processed_at": datetime.utcnow().isoformat(),
        "company_id": ctx.company_id,
    }


@router.post("/documents/{document_id}/process")
async def process_ocr_document(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "status": "processing",
        "started_at": datetime.utcnow().isoformat(),
    }


@router.post("/documents/{document_id}/reprocess")
async def reprocess_ocr_document(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "status": "queued",
        "reprocessing": True,
        "queued_at": datetime.utcnow().isoformat(),
    }


@router.delete("/documents/{document_id}")
async def delete_ocr_document(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": document_id, "deleted": True}


@router.get("/documents/{document_id}/text")
async def get_ocr_text(
    document_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": document_id,
        "raw_text": "Extracted text from OCR processing...",
        "structured_data": {
            "invoice_number": "INV-001",
            "vendor": "Office Supplies Co",
            "total_amount": "150.00",
            "date": "2026-04-01",
        },
        "confidence": 0.95,
    }


@router.get("/stats")
async def get_ocr_stats(
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "total_documents": 0,
        "processed": 0,
        "failed": 0,
        "queued": 0,
        "average_confidence": 0.0,
        "company_id": ctx.company_id,
    }
