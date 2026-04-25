from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from finance_platform.watermark.models import (
    Watermark,
    WatermarkBatch,
    WatermarkStatus,
    WatermarkTemplate,
    WatermarkType,
    WatermarkPosition,
    WatermarkSeverity,
    DocumentReference,
)
from finance_platform.watermark.service import WatermarkService
from finance_platform.watermark.schemas import (
    WatermarkCreate,
    WatermarkUpdate,
    WatermarkResponse,
    WatermarkListParams,
    WatermarkListResponse,
    WatermarkApplyRequest,
    WatermarkVerifyRequest,
    WatermarkRevokeRequest,
    WatermarkTemplateCreate,
    WatermarkTemplateUpdate,
    WatermarkTemplateResponse,
    BatchWatermarkCreate,
    BatchWatermarkResponse,
    ApplyWatermarkResponse,
    WatermarkVerificationResponse,
    WatermarkStats,
    WatermarkPreviewRequest,
    BulkApplyRequest,
)
from finance_platform.watermark.exceptions import (
    WatermarkError,
    WatermarkNotFoundError,
    WatermarkAlreadyAppliedError,
    WatermarkVerificationFailedError,
    WatermarkPolicyViolationError,
    WatermarkEngineError,
    WatermarkTemplateNotFoundError,
)

router = APIRouter(prefix="/watermarks", tags=["watermarks"])


def get_watermark_service() -> WatermarkService:
    return WatermarkService()


def _watermark_to_response(w: Watermark) -> WatermarkResponse:
    return WatermarkResponse(
        id=w.id,
        document_reference={
            "id": w.document_reference.id,
            "document_type": w.document_reference.document_type,
            "document_url": w.document_reference.document_url,
            "checksum": w.document_reference.checksum,
            "page_count": w.document_reference.page_count,
            "file_size_bytes": w.document_reference.file_size_bytes,
            "mime_type": w.document_reference.mime_type,
            "metadata": w.document_reference.metadata,
        },
        template_id=w.template_id,
        watermark_type=w.watermark_type,
        content=w.content,
        position=w.position,
        status=w.status,
        severity=w.severity,
        opacity=w.opacity,
        rotation=w.rotation,
        applied_by=w.applied_by,
        applied_at=w.applied_at,
        verified_by=w.verified_by,
        verified_at=w.verified_at,
        verification_hash=w.verification_hash,
        expires_at=w.expires_at,
        revoked_by=w.revoked_by,
        revoked_at=w.revoked_at,
        revocation_reason=w.revocation_reason,
        company_id=w.company_id,
        created_by=w.created_by,
        created_at=w.created_at,
        updated_at=w.updated_at,
        metadata=w.metadata,
    )


def _template_to_response(t: WatermarkTemplate) -> WatermarkTemplateResponse:
    return WatermarkTemplateResponse(
        id=t.id,
        name=t.name,
        description=t.description,
        watermark_type=t.watermark_type,
        content_template=t.content_template,
        font_family=t.font_family,
        font_size=t.font_size,
        font_color=t.font_color,
        opacity=t.opacity,
        rotation=t.rotation,
        position=t.position,
        scale_x=t.scale_x,
        scale_y=t.scale_y,
        repeat=t.repeat,
        margin_x=t.margin_x,
        margin_y=t.margin_y,
        required=t.required,
        active=t.active,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.post("", response_model=WatermarkResponse, status_code=201)
def create_watermark(
    payload: WatermarkCreate,
    service: WatermarkService = Depends(get_watermark_service),
):
    doc_ref = DocumentReference(
        id=payload.document_reference.id,
        document_type=payload.document_reference.document_type,
        document_url=payload.document_reference.document_url,
        checksum=payload.document_reference.checksum,
        page_count=payload.document_reference.page_count,
        file_size_bytes=payload.document_reference.file_size_bytes,
        mime_type=payload.document_reference.mime_type,
        metadata=payload.document_reference.metadata,
    )
    watermark = service.create_watermark(
        document_reference=doc_ref,
        watermark_type=payload.watermark_type,
        content=payload.content,
        position=payload.position,
        opacity=payload.opacity,
        rotation=payload.rotation,
        company_id=payload.company_id,
        template_id=payload.template_id,
        expires_at=payload.expires_at,
        metadata=payload.metadata,
    )
    return _watermark_to_response(watermark)


@router.get("", response_model=WatermarkListResponse)
def list_watermarks(
    status: Optional[WatermarkStatus] = Query(None),
    watermark_type: Optional[str] = Query(None, alias="watermark_type"),
    company_id: Optional[str] = Query(None),
    document_id: Optional[str] = Query(None),
    applied_by: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: WatermarkService = Depends(get_watermark_service),
):
    items, total = service.list_watermarks(
        status=status,
        watermark_type=watermark_type,
        company_id=company_id,
        document_id=document_id,
        applied_by=applied_by,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    return WatermarkListResponse(
        items=[_watermark_to_response(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{watermark_id}", response_model=WatermarkResponse)
def get_watermark(
    watermark_id: str,
    service: WatermarkService = Depends(get_watermark_service),
):
    watermark = service.get_watermark(watermark_id)
    return _watermark_to_response(watermark)


@router.delete("/{watermark_id}", status_code=204)
def delete_watermark(
    watermark_id: str,
    service: WatermarkService = Depends(get_watermark_service),
):
    deleted = service.delete_watermark(watermark_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Watermark '{watermark_id}' not found")


@router.post("/{watermark_id}/apply", response_model=ApplyWatermarkResponse)
def apply_watermark(
    watermark_id: str,
    payload: WatermarkApplyRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    watermark = service.apply_watermark(watermark_id, payload.applied_by)
    return ApplyWatermarkResponse(
        watermark_id=watermark.id,
        status=watermark.status,
        applied_at=watermark.applied_at,
        verification_hash=watermark.verification_hash,
        message="Watermark applied successfully",
    )


@router.post("/{watermark_id}/verify", response_model=WatermarkVerificationResponse)
def verify_watermark(
    watermark_id: str,
    payload: WatermarkVerifyRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    try:
        watermark = service.verify_watermark(watermark_id, payload.verified_by)
        return WatermarkVerificationResponse(
            watermark_id=watermark.id,
            verified=True,
            verified_by=watermark.verified_by,
            verified_at=watermark.verified_at,
            details={"verification_hash": watermark.verification_hash},
        )
    except WatermarkVerificationFailedError as exc:
        return WatermarkVerificationResponse(
            watermark_id=watermark_id,
            verified=False,
            details={"reason": str(exc)},
        )


@router.post("/{watermark_id}/revoke", response_model=WatermarkResponse)
def revoke_watermark(
    watermark_id: str,
    payload: WatermarkRevokeRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    watermark = service.revoke_watermark(watermark_id, payload.revoked_by, payload.reason)
    return _watermark_to_response(watermark)


@router.post("/{watermark_id}/expire", response_model=WatermarkResponse)
def expire_watermark(
    watermark_id: str,
    service: WatermarkService = Depends(get_watermark_service),
):
    watermark = service.expire_watermark(watermark_id)
    return _watermark_to_response(watermark)


@router.get("/stats", response_model=WatermarkStats)
def get_watermark_stats(
    company_id: Optional[str] = Query(None),
    service: WatermarkService = Depends(get_watermark_service),
):
    stats = service.get_stats(company_id=company_id)
    return WatermarkStats(**stats)


# --- Templates ---

@router.post("/templates", response_model=WatermarkTemplateResponse, status_code=201)
def create_template(
    payload: WatermarkTemplateCreate,
    service: WatermarkService = Depends(get_watermark_service),
):
    template = service.create_template(
        name=payload.name,
        description=payload.description,
        watermark_type=payload.watermark_type,
        content_template=payload.content_template,
        font_family=payload.font_family,
        font_size=payload.font_size,
        font_color=payload.font_color,
        opacity=payload.opacity,
        rotation=payload.rotation,
        position=payload.position,
        scale_x=payload.scale_x,
        scale_y=payload.scale_y,
        repeat=payload.repeat,
        margin_x=payload.margin_x,
        margin_y=payload.margin_y,
        required=payload.required,
    )
    return _template_to_response(template)


@router.get("/templates", response_model=list[WatermarkTemplateResponse])
def list_templates(
    active_only: bool = Query(True),
    service: WatermarkService = Depends(get_watermark_service),
):
    templates = service.list_templates(active_only=active_only)
    return [_template_to_response(t) for t in templates]


@router.get("/templates/{template_id}", response_model=WatermarkTemplateResponse)
def get_template(
    template_id: str,
    service: WatermarkService = Depends(get_watermark_service),
):
    template = service.get_template(template_id)
    return _template_to_response(template)


@router.put("/templates/{template_id}", response_model=WatermarkTemplateResponse)
def update_template(
    template_id: str,
    payload: WatermarkTemplateUpdate,
    service: WatermarkService = Depends(get_watermark_service),
):
    updates = payload.model_dump(exclude_none=True)
    template = service.update_template(template_id, updates)
    return _template_to_response(template)


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(
    template_id: str,
    service: WatermarkService = Depends(get_watermark_service),
):
    deleted = service.delete_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")


@router.post("/templates/{template_id}/apply", response_model=WatermarkResponse)
def apply_template(
    template_id: str,
    payload: WatermarkApplyRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    template = service.get_template(template_id)
    doc_ref = DocumentReference(
        id="",
        mime_type="application/pdf",
    )
    watermark = service.apply_template(
        template_id=template_id,
        document_reference=doc_ref,
        company_id="",
        applied_by=payload.applied_by,
    )
    return _watermark_to_response(watermark)


# --- Batches ---

@router.post("/batches", response_model=BatchWatermarkResponse, status_code=201)
def create_batch(
    payload: BatchWatermarkCreate,
    service: WatermarkService = Depends(get_watermark_service),
):
    documents = [
        DocumentReference(
            id=d.id,
            document_type=d.document_type,
            document_url=d.document_url,
            checksum=d.checksum,
            page_count=d.page_count,
            file_size_bytes=d.file_size_bytes,
            mime_type=d.mime_type,
            metadata=d.metadata,
        )
        for d in payload.documents
    ]
    batch = service.create_batch(
        name=payload.name,
        description=payload.description,
        documents=documents,
        template_id=payload.template_id,
        watermark_type=payload.watermark_type,
        position=payload.position,
        company_id=payload.company_id,
    )
    return BatchWatermarkResponse(
        batch_id=batch.id,
        name=batch.name,
        status=batch.status,
        total_count=batch.total_count,
        success_count=batch.success_count,
        failure_count=batch.failure_count,
        items=[],
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


@router.get("/batches", response_model=list[BatchWatermarkResponse])
def list_batches(
    company_id: Optional[str] = Query(None),
    status: Optional[WatermarkStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: WatermarkService = Depends(get_watermark_service),
):
    batches, total = service.list_batches(
        company_id=company_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return [
        BatchWatermarkResponse(
            batch_id=b.id,
            name=b.name,
            status=b.status,
            total_count=b.total_count,
            success_count=b.success_count,
            failure_count=b.failure_count,
            items=[],
            created_at=b.created_at,
            completed_at=b.completed_at,
        )
        for b in batches
    ]


@router.get("/batches/{batch_id}", response_model=BatchWatermarkResponse)
def get_batch(
    batch_id: str,
    service: WatermarkService = Depends(get_watermark_service),
):
    batch = service.get_batch(batch_id)
    return BatchWatermarkResponse(
        batch_id=batch.id,
        name=batch.name,
        status=batch.status,
        total_count=batch.total_count,
        success_count=batch.success_count,
        failure_count=batch.failure_count,
        items=[],
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


@router.post("/batches/{batch_id}/process", response_model=BatchWatermarkResponse)
def process_batch(
    batch_id: str,
    payload: WatermarkApplyRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    batch = service.process_batch(batch_id, payload.applied_by)
    return BatchWatermarkResponse(
        batch_id=batch.id,
        name=batch.name,
        status=batch.status,
        total_count=batch.total_count,
        success_count=batch.success_count,
        failure_count=batch.failure_count,
        items=[],
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


# --- Bulk operations ---

@router.post("/bulk-apply", response_model=list[WatermarkResponse])
def bulk_apply(
    payload: BulkApplyRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    results: list[Watermark] = []
    for doc_id in payload.document_ids:
        doc_ref = DocumentReference(id=doc_id, mime_type="application/pdf")
        watermark = service.create_watermark(
            document_reference=doc_ref,
            watermark_type=payload.watermark_type,
            content=payload.content,
            position=payload.position,
            opacity=payload.opacity,
            rotation=payload.rotation,
            company_id=payload.company_id,
        )
        applied = service.apply_watermark(watermark.id, "")
        results.append(applied)
    return [_watermark_to_response(w) for w in results]


# --- Validate / utilities ---

@router.post("/validate")
def validate_watermark_request(
    payload: WatermarkCreate,
    service: WatermarkService = Depends(get_watermark_service),
):
    violations = service.validate_watermark_request(
        watermark_type=payload.watermark_type.value,
        position=payload.position.value,
        mime_type=payload.document_reference.mime_type,
        company_id=payload.company_id,
        opacity=payload.opacity,
    )
    return {
        "valid": len(violations) == 0,
        "violations": violations,
    }


@router.get("/supported-types")
def get_supported_types(
    service: WatermarkService = Depends(get_watermark_service),
):
    return {
        "mime_types": service.get_supported_mime_types(),
        "watermark_types": [t.value for t in WatermarkType],
        "positions": [p.value for p in WatermarkPosition],
        "severities": [s.value for s in WatermarkSeverity],
    }


@router.post("/estimate-placement")
def estimate_placement(
    payload: WatermarkPreviewRequest,
    service: WatermarkService = Depends(get_watermark_service),
):
    return service.estimate_placement(
        position=payload.position,
        margin_x=10,
        margin_y=10,
    )


# --- Scan ---

@router.post("/scan")
def scan_document(
    body: dict,
    service: WatermarkService = Depends(get_watermark_service),
):
    content_str = body.get("content", "")
    findings = service.scan_document(content_str.encode("utf-8"))
    return {"findings": findings}
