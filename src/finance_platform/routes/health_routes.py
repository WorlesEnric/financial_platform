from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from finance_platform.routes.deps import (
    PageParams,
    PaginatedResponse,
    get_company_id,
    get_optional_company_id,
    paginate,
    resolve_company_context,
)

router = APIRouter()


@router.get("/ping")
async def health_ping():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "service": "finance-platform"}


@router.get("/ready")
async def health_readiness():
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "ok",
            "cache": "ok",
            "storage": "ok",
        },
    }


@router.get("/live")
async def health_liveness():
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/version")
async def health_version():
    return {
        "version": "1.0.0",
        "build": "2026-04-24",
        "name": "finance-platform",
    }


@router.get("/metrics")
async def health_metrics():
    return {
        "uptime_seconds": 0,
        "active_requests": 0,
        "total_requests": 0,
        "error_count": 0,
        "average_response_ms": 0.0,
    }
