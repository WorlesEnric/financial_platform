from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from finance_platform.amortization.models import AmortizationStatus
from finance_platform.amortization.repository import AmortizationRepository
from finance_platform.amortization.schemas import (
    AmortizationBulkCreateRequest,
    AmortizationBulkCreateResponse,
    AmortizationEntryPaymentRequest,
    AmortizationEntryDeferRequest,
    AmortizationEntryWaiveRequest,
    AmortizationEntryResponse,
    AmortizationFilterParams,
    AmortizationForecastResponse,
    AmortizationListResponse,
    AmortizationRecordCreate,
    AmortizationRecordResponse,
    AmortizationRecordUpdate,
    AmortizationStatusUpdateRequest,
    AmortizationSummaryResponse,
)
from finance_platform.amortization.service import AmortizationService
from finance_platform.routes.deps import get_company_id, resolve_company_context

router = APIRouter(prefix="/api/v1/amortization", tags=["amortization"])


def get_service() -> AmortizationService:
    return AmortizationService(repository=AmortizationRepository())


@router.post("/records", response_model=AmortizationRecordResponse, status_code=201)
async def create_record(
    data: AmortizationRecordCreate,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    data.company_id = ctx.company_id
    return service.create_record(data)


@router.get("/records", response_model=AmortizationListResponse)
async def list_records(
    company_id: str = Depends(get_company_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AmortizationService = Depends(get_service),
):
    return service.list_records(company_id, page, page_size)


@router.get("/records/{record_id}", response_model=AmortizationRecordResponse)
async def get_record(
    record_id: str,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.get_record(record_id)


@router.patch("/records/{record_id}", response_model=AmortizationRecordResponse)
async def update_record(
    record_id: str,
    data: AmortizationRecordUpdate,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.update_record(record_id, data)


@router.delete("/records/{record_id}", status_code=204)
async def delete_record(
    record_id: str,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    service.delete_record(record_id)


@router.post("/records/bulk", response_model=AmortizationBulkCreateResponse)
async def bulk_create(
    data: AmortizationBulkCreateRequest,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    data.company_id = ctx.company_id
    return service.bulk_create(data)


@router.get("/records/{record_id}/entries", response_model=list[AmortizationEntryResponse])
async def get_entries(
    record_id: str,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.get_entries(record_id)


@router.post("/entries/{entry_id}/pay", response_model=AmortizationEntryResponse)
async def pay_entry(
    entry_id: str,
    data: AmortizationEntryPaymentRequest,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.pay_entry(entry_id, data)


@router.post("/entries/{entry_id}/defer", response_model=AmortizationEntryResponse)
async def defer_entry(
    entry_id: str,
    data: AmortizationEntryDeferRequest,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.defer_entry(entry_id, data)


@router.post("/entries/{entry_id}/waive", response_model=AmortizationEntryResponse)
async def waive_entry(
    entry_id: str,
    data: AmortizationEntryWaiveRequest,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.waive_entry(entry_id, data)


@router.post("/records/{record_id}/status", response_model=AmortizationRecordResponse)
async def update_status(
    record_id: str,
    data: AmortizationStatusUpdateRequest,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.update_status(record_id, data.status, data.reason)


@router.get("/summary", response_model=AmortizationSummaryResponse)
async def get_summary(
    company_id: str = Depends(get_company_id),
    fiscal_year: Optional[str] = Query(None),
    service: AmortizationService = Depends(get_service),
):
    return service.get_summary(company_id, fiscal_year or "2026")


@router.post("/records/{record_id}/forecast", response_model=AmortizationForecastResponse)
async def generate_forecast(
    record_id: str,
    ctx=Depends(resolve_company_context),
    service: AmortizationService = Depends(get_service),
):
    return service.generate_forecast(record_id)
