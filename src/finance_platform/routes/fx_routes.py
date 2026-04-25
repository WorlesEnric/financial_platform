from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finance_platform.routes.deps import (
    get_company_id,
    paginate,
    resolve_company_context,
)

router = APIRouter()


@router.get("/rates")
async def list_fx_rates(
    base_currency: Optional[str] = Query(None),
    target_currency: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.post("/rates")
async def create_fx_rate(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {"id": "rate-id", **body, "created": True}


@router.get("/rates/latest")
async def get_latest_fx_rates(
    base_currency: str = Query("USD"),
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "base_currency": base_currency,
        "date": date.today().isoformat(),
        "rates": {
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 151.50,
            "CAD": 1.37,
            "CHF": 0.91,
        },
    }


@router.get("/rates/{rate_id}")
async def get_fx_rate(
    rate_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": rate_id,
        "from_currency": "USD",
        "to_currency": "EUR",
        "rate": 0.92,
        "date": "2026-04-24",
        "source": "ecb",
    }


@router.get("/snapshots")
async def list_fx_snapshots(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ctx: Any = Depends(resolve_company_context),
):
    return paginate([], 0, page, page_size)


@router.post("/snapshots")
async def create_fx_snapshot(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": "snapshot-id",
        "base_currency": body.get("base_currency", "USD"),
        "snapshot_date": date.today().isoformat(),
        "immutable": True,
        "created": True,
    }


@router.get("/snapshots/{snapshot_id}")
async def get_fx_snapshot(
    snapshot_id: str,
    ctx: Any = Depends(resolve_company_context),
):
    return {
        "id": snapshot_id,
        "base_currency": "USD",
        "snapshot_date": "2026-04-24",
        "source": "ecb",
        "rates": {"EUR": 0.92, "GBP": 0.79},
        "immutable": True,
    }


@router.post("/convert")
async def convert_currency(
    body: Dict[str, Any],
    ctx: Any = Depends(resolve_company_context),
):
    from_currency = body.get("from_currency", "USD")
    to_currency = body.get("to_currency", "EUR")
    amount_minor = body.get("amount_minor", 0)
    return {
        "from_currency": from_currency,
        "to_currency": to_currency,
        "original_amount_minor": amount_minor,
        "converted_amount_minor": int(amount_minor * 0.92),
        "rate": 0.92,
        "rate_date": date.today().isoformat(),
    }
