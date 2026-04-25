from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from finance_platform.models.settlement import Settlement, SettlementRun
from finance_platform.settlements.exceptions import (
    SettlementError,
    SettlementNotFoundError,
    SettlementRunNotFoundError,
    SettlementOverRegistrationError,
    SettlementAlreadyCompletedError,
    SettlementRunInProgressError,
)
from finance_platform.settlements.models import (
    EntityType,
    SettlementFilter,
    SettlementPayment,
    SettlementBatch,
    SettlementBatchStatus,
    SettlementPriority,
    PaymentMethod,
    PaymentStatus,
)
from finance_platform.settlements.schemas import (
    SettlementCreateRequest,
    SettlementUpdateRequest,
    SettlementResponse,
    SettlementRunCreateRequest,
    SettlementRunResponse,
    SettlementAllocationRequest,
    SettlementBatchRequest,
    SettlementSummaryResponse,
    SettlementListResponse,
    PaymentCreateRequest,
    PaymentResponse,
    SettlementSearchParams,
)
from finance_platform.settlements.service import SettlementService
from finance_platform.settlements.state_machine import SettlementEvent

router = APIRouter(prefix="/settlements", tags=["settlements"])
service = SettlementService()


def get_service() -> SettlementService:
    return service


def _settlement_to_response(s: Settlement) -> SettlementResponse:
    return SettlementResponse(
        id=s.id,
        entity_type=s.entity_type,
        entity_id=s.entity_id,
        total_amount=s.total_amount,
        settled_amount=s.settled_amount,
        remaining_amount=s.remaining_amount,
        currency=s.currency if isinstance(s.currency, str) else s.currency.value,
        status=s.status,
        settlement_run_id=s.settlement_run_id,
        settlement_date=s.settlement_date,
        payment_method=s.payment_method,
        payment_reference=s.payment_reference,
        approved_by=s.approved_by,
        approved_at=s.approved_at,
        notes=s.notes,
        tags=s.tags,
        metadata=s.metadata,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


def _run_to_response(r: SettlementRun) -> SettlementRunResponse:
    return SettlementRunResponse(
        id=r.id,
        run_date=r.run_date,
        description=r.description,
        total_settled=r.total_settled,
        currency=r.currency if isinstance(r.currency, str) else r.currency.value,
        status=r.status,
        started_at=r.started_at,
        completed_at=r.completed_at,
        error_message=r.error_message,
        triggered_by=r.triggered_by,
        is_automatic=r.is_automatic,
        metadata=r.metadata,
    )


def _payment_to_response(p: SettlementPayment) -> PaymentResponse:
    return PaymentResponse(
        id=p.id,
        settlement_id=p.settlement_id,
        run_id=p.run_id,
        amount=p.amount,
        currency=p.currency,
        payment_method=p.payment_method.value if isinstance(p.payment_method, PaymentMethod) else p.payment_method,
        payment_reference=p.payment_reference,
        status=p.status,
        paid_at=p.paid_at,
        confirmed_at=p.confirmed_at,
        bank_account_ref=p.bank_account_ref,
        beneficiary_name=p.beneficiary_name,
        notes=p.notes,
        created_at=p.created_at,
    )


@router.post("", response_model=SettlementResponse, status_code=201)
def create_settlement(
    req: SettlementCreateRequest,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    settlement = svc.create_settlement(
        entity_type=req.entity_type.value,
        entity_id=req.entity_id,
        total_amount=req.total_amount,
        currency=req.currency,
        priority=req.priority,
        description=req.description,
        department=req.department,
        cost_center=req.cost_center,
        due_date=req.due_date,
        reference_number=req.reference_number,
        tags=req.tags,
        metadata=req.metadata,
    )
    return _settlement_to_response(settlement)


@router.get("/{settlement_id}", response_model=SettlementResponse)
def get_settlement(
    settlement_id: str,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.get_settlement(settlement_id)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _settlement_to_response(settlement)


@router.patch("/{settlement_id}", response_model=SettlementResponse)
def update_settlement(
    settlement_id: str,
    req: SettlementUpdateRequest,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.update_settlement(
            settlement_id=settlement_id,
            total_amount=req.total_amount,
            currency=req.currency,
            priority=req.priority,
            description=req.description,
            department=req.department,
            cost_center=req.cost_center,
            due_date=req.due_date,
            reference_number=req.reference_number,
            tags=req.tags,
            metadata=req.metadata,
            notes=req.notes,
        )
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementAlreadyCompletedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _settlement_to_response(settlement)


@router.delete("/{settlement_id}", status_code=204)
def delete_settlement(
    settlement_id: str,
    svc: SettlementService = Depends(get_service),
) -> None:
    try:
        svc.delete_settlement(settlement_id)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementAlreadyCompletedError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return None


@router.get("", response_model=SettlementListResponse)
def list_settlements(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    currency: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    svc: SettlementService = Depends(get_service),
) -> SettlementListResponse:
    filter_obj = SettlementFilter()
    if entity_type:
        filter_obj.entity_type = EntityType(entity_type)
    if entity_id:
        filter_obj.entity_id = entity_id
    if status:
        filter_obj.status = status
    if run_id:
        filter_obj.run_id = run_id
    if currency:
        filter_obj.currency = currency
    if date_from:
        filter_obj.date_from = date_from
    if date_to:
        filter_obj.date_to = date_to

    settlements, total = svc.list_settlements(
        filter_obj=filter_obj,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items = [_settlement_to_response(s) for s in settlements]
    total_pages = max(1, (total + page_size - 1) // page_size)

    return SettlementListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=SettlementSummaryResponse)
def get_summary(
    svc: SettlementService = Depends(get_service),
) -> SettlementSummaryResponse:
    summary = svc.get_summary()
    return SettlementSummaryResponse(
        total_pending=summary.total_pending,
        total_processing=summary.total_processing,
        total_completed=summary.total_completed,
        total_failed=summary.total_failed,
        total_reversed=summary.total_reversed,
        total_amount_pending=summary.total_amount_pending,
        total_amount_settled=summary.total_amount_settled,
        total_high_priority_pending=summary.total_high_priority_pending,
        total_high_priority_amount=summary.total_high_priority_amount,
        pending_by_entity_type=summary.pending_by_entity_type,
        amount_by_currency=summary.amount_by_currency,
        active_run_count=summary.active_run_count,
        last_run_date=summary.last_run_date,
    )


# --- Transitions ---

@router.post("/{settlement_id}/approve", response_model=SettlementResponse)
def approve_settlement(
    settlement_id: str,
    approved_by: str = Query(...),
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.approve_settlement(settlement_id, approved_by)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


@router.post("/{settlement_id}/complete", response_model=SettlementResponse)
def complete_settlement(
    settlement_id: str,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.complete_settlement(settlement_id)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


@router.post("/{settlement_id}/fail", response_model=SettlementResponse)
def fail_settlement(
    settlement_id: str,
    error_message: str = Query(default=""),
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.fail_settlement(settlement_id, error_message)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


@router.post("/{settlement_id}/reverse", response_model=SettlementResponse)
def reverse_settlement(
    settlement_id: str,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.reverse_settlement(settlement_id)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


@router.post("/{settlement_id}/cancel", response_model=SettlementResponse)
def cancel_settlement(
    settlement_id: str,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.cancel_settlement(settlement_id)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


# --- Allocations ---

@router.post("/{settlement_id}/allocations", response_model=SettlementResponse)
def create_allocation(
    settlement_id: str,
    req: SettlementAllocationRequest,
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.create_allocation(
            settlement_id=settlement_id,
            entity_type=req.entity_type.value,
            entity_id=req.entity_id,
            allocated_amount=req.allocated_amount,
            currency=req.currency,
            fx_rate=req.fx_rate,
            fx_from_currency=req.fx_from_currency,
            notes=req.notes,
        )
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementOverRegistrationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


# --- Runs ---

@router.post("/runs", response_model=SettlementRunResponse, status_code=201)
def create_run(
    req: SettlementRunCreateRequest,
    svc: SettlementService = Depends(get_service),
) -> SettlementRunResponse:
    try:
        run = svc.create_run(
            description=req.description,
            currency=req.currency,
            is_automatic=req.is_automatic,
            settlement_ids=req.settlement_ids,
            scheduled_date=req.scheduled_date,
        )
    except SettlementRunInProgressError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _run_to_response(run)


@router.get("/runs/{run_id}", response_model=SettlementRunResponse)
def get_run(
    run_id: str,
    svc: SettlementService = Depends(get_service),
) -> SettlementRunResponse:
    try:
        run = svc.get_run(run_id)
    except SettlementRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _run_to_response(run)


@router.get("/runs", response_model=dict)
def list_runs(
    status: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    svc: SettlementService = Depends(get_service),
) -> dict:
    runs, total = svc.list_runs(status=status, page=page, page_size=page_size)
    items = [_run_to_response(r) for r in runs]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/runs/{run_id}/start", response_model=SettlementRunResponse)
def start_run(
    run_id: str,
    svc: SettlementService = Depends(get_service),
) -> SettlementRunResponse:
    try:
        run = svc.start_run(run_id)
    except SettlementRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementRunInProgressError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return _run_to_response(run)


@router.post("/runs/{run_id}/complete", response_model=SettlementRunResponse)
def complete_run(
    run_id: str,
    error_message: Optional[str] = Query(default=None),
    svc: SettlementService = Depends(get_service),
) -> SettlementRunResponse:
    try:
        run = svc.complete_run(run_id, error_message=error_message)
    except SettlementRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _run_to_response(run)


@router.get("/runs/{run_id}/reconcile", response_model=dict)
def reconcile_run(
    run_id: str,
    svc: SettlementService = Depends(get_service),
) -> dict:
    try:
        return svc.reconcile_run(run_id)
    except SettlementRunNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Payments ---

@router.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(
    req: PaymentCreateRequest,
    svc: SettlementService = Depends(get_service),
) -> PaymentResponse:
    try:
        payment = svc.create_payment(
            settlement_id=req.settlement_id,
            amount=req.amount,
            currency=req.currency,
            payment_method=req.payment_method,
            bank_account_ref=req.bank_account_ref,
            beneficiary_name=req.beneficiary_name,
            beneficiary_account=req.beneficiary_account,
            notes=req.notes,
        )
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SettlementError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _payment_to_response(payment)


@router.get("/payments", response_model=dict)
def list_payments(
    settlement_id: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    status: Optional[PaymentStatus] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    svc: SettlementService = Depends(get_service),
) -> dict:
    payments, total = svc.list_payments(
        settlement_id=settlement_id,
        run_id=run_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    items = [_payment_to_response(p) for p in payments]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: str,
    payment_reference: str = Query(...),
    svc: SettlementService = Depends(get_service),
) -> PaymentResponse:
    try:
        payment = svc.confirm_payment(payment_id, payment_reference)
    except SettlementError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _payment_to_response(payment)


@router.post("/payments/{payment_id}/fail", response_model=PaymentResponse)
def fail_payment(
    payment_id: str,
    error_message: str = Query(default=""),
    svc: SettlementService = Depends(get_service),
) -> PaymentResponse:
    try:
        payment = svc.fail_payment(payment_id, error_message)
    except SettlementError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _payment_to_response(payment)


# --- Register for settlement (G24) ---

@router.post("/register", response_model=SettlementResponse, status_code=201)
def register_for_settlement(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    amount: float = Query(..., gt=0),
    currency: str = Query(default="USD"),
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        settlement = svc.register_for_settlement(
            entity_type=entity_type,
            entity_id=entity_id,
            amount=amount,
            currency=currency,
        )
    except SettlementOverRegistrationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)


# --- Event transition endpoint ---

@router.post("/{settlement_id}/transition", response_model=SettlementResponse)
def transition_settlement(
    settlement_id: str,
    event: str = Query(...),
    svc: SettlementService = Depends(get_service),
) -> SettlementResponse:
    try:
        event_enum = SettlementEvent(event)
        settlement = svc.transition_settlement(settlement_id, event_enum)
    except SettlementNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValueError, SettlementError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _settlement_to_response(settlement)
