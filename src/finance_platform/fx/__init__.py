"""FX subpackage — re-export façade.

Centralized under ``models/fx_rate.py``,
``services/fx_rate_service.py``, and ``routes/fx_routes.py``.
Fabricated symbols in the original stub (FxSourceAdapter,
FxQuoteRequest, FxQuoteResponse, PricingBasis, *Snapshot*/Quote*
schemas, FxRateRepository, CorporateTableAdapter, BankApiAdapter,
ThirdPartyAdapter, get_fx_source_adapter) were never shipped and are
dropped. See ../../../problem.md.
"""

from finance_platform.models.fx_rate import FxRate, FxRateSnapshot
from finance_platform.services.fx_rate_service import FxRateService
from finance_platform.routes.fx_routes import router as fx_router

__all__ = [
    "FxRate",
    "FxRateSnapshot",
    "FxRateService",
    "fx_router",
]
