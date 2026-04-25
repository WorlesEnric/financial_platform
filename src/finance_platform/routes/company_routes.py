from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from finance_platform.routes.dependencies import (
    CompanyContext,
    get_company_context,
    get_pagination_params,
    paginate,
    PaginationParams,
)

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"
    locale: str = "en-US"
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"
    locale: str = "en-US"
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


_companies_db: dict[str, dict] = {}


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    ctx: CompanyContext = Depends(get_company_context),
    params: PaginationParams = Depends(get_pagination_params),
    is_active: Optional[bool] = None,
):
    results = list(_companies_db.values())
    if is_active is not None:
        results = [c for c in results if c.get("is_active") == is_active]
    results.sort(key=lambda c: c.get("name", ""))
    total = len(results)
    start = (params.page - 1) * params.page_size
    end = start + params.page_size
    paginated = results[start:end]
    return CompanyListResponse(
        items=[CompanyResponse(**c) for c in paginated],
        total=total,
        page=params.page,
        page_size=params.page_size,
        total_pages=max(1, (total + params.page_size - 1) // params.page_size),
    )


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    body: CompanyCreate,
):
    now = datetime.utcnow()
    company_id = f"comp_{len(_companies_db) + 1}"
    record = {
        "id": company_id,
        "name": body.name,
        "legal_name": body.legal_name or body.name,
        "tax_id": body.tax_id,
        "currency": body.currency,
        "timezone": body.timezone,
        "locale": body.locale,
        "address": body.address,
        "phone": body.phone,
        "email": body.email,
        "website": body.website,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    _companies_db[company_id] = record
    return CompanyResponse(**record)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
):
    record = _companies_db.get(company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(**record)


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    body: CompanyUpdate,
):
    record = _companies_db.get(company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Company not found")
    update_data = body.model_dump(exclude_none=True)
    record.update(update_data)
    record["updated_at"] = datetime.utcnow()
    return CompanyResponse(**record)


@router.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: str,
):
    if company_id not in _companies_db:
        raise HTTPException(status_code=404, detail="Company not found")
    del _companies_db[company_id]


@router.get("/current", response_model=CompanyResponse)
async def get_current_company(
    ctx: CompanyContext = Depends(get_company_context),
):
    record = _companies_db.get(ctx.company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse(**record)
