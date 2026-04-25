# Task Brief — Enterprise Financial Reimbursement + Amortization Platform

**Task ID:** `task-1777008735841`
**Step ID:** `step.task-1777008735841.brief`
**Source spec:** `tests/financial_platform/spec.md` (referenced, not present on disk)

---

## Objective

Build a runnable Python package `finance_platform` (src/ layout, `pip install -e .`) implementing an enterprise multi-company reimbursement + amortization platform with 24 named subsystems producing 20,000–30,000 LOC across ≥100 .py files, no file >1500 LOC, mean ≤280 LOC/file.

---

## Hard Constraints (from acceptance contract)

1. **Package layout**: `src/finance_platform/` top-level package. `pyproject.toml` at repo root with `[project.name]="finance-platform"`, runtime deps: fastapi, sqlmodel, pydantic, pydantic-settings, alembic, httpx. Console script: `finance_platform=finance_platform.cli:main`.

2. **App factory**: `create_app()` returning a FastAPI instance, ±25 mounted routes covering MVP API endpoints (see subsystem 15 — routes).

3. **Subsystem count**: ≥15 of 24 subsystem categories present. Each subsystem is a top-level package under `finance_platform/` with ≥6 .py files and ≥1200 LOC.

4. **24 required subsystems**: identity, amortization, expenses, fx, ocr, watermark, approvals, settlements, debts, carry_forward, notifications, audit, models, schemas, routes, db, migrations, auth, config, errors, state_machines, services, cli, logging.

5. **Monetary fields**: integer `*_amount_minor` columns everywhere; Pydantic DTOs expose as Decimal strings.

6. **Multi-company isolation**: every business endpoint MUST resolve `company_id`; routes without company context return 400.

7. **FX immutability**: `fx_rate_snapshots` immutable after creation; repo raises on UPDATE when `immutable_flag=true`.

8. **Approval uniqueness**: two approvals on same expense from two distinct finance reviewers of the same company.

9. **Void flow**: at least one original reviewer must participate OR FINANCE_ADMIN substitution path with audit entry.

10. **Carry-forward**: skips two-person approval, enters PENDING_AMORTIZATION with priority=HIGH.

11. **Settlement priority**: HIGH-priority carry-forward items cleared first, then FIFO within normal debts; over-registration rejected.

12. **No tests shipped**: integrate step MUST strip `test_*.py`, `tests/`, `conftest.py`.

13. **File count**: ≥100 .py, ≥15000 LOC total.

14. **Worker distribution**: ≥8 distinct worker_ids contributed files (16-worker fan-out), no single worker >45%.

15. **Shard non-overlap**: every shard's `writable_globs` must be strict prefixes of its subpackage path.

16. **Integration deliverables**: `src/finance_platform/__init__.py` re-exporting `create_app`, `SPEC_MAPPING.md`, `README.md` with quickstart.

17. **Alembic**: env.py + ≥3 revisions (0001_initial, 0002_multi_company_partitions, 0003_amortization_versioning).

18. **Logging**: structlog, per-request correlation id, company-scoped log binder.

19. **Domain events**: outbox pattern via `audit/domain_events`; services publish events, not directly to notification channels.

20. **Error format**: ProblemDetail-style RFC-7807 HTTPException subclasses; domain exception hierarchy (ValidationError, PermissionDeniedError, BusinessRuleViolation, StateTransitionError, CrossCompanyAccessError, FxRateMissingError, DebtAllocationError).

21. **CLI**: console entry with subcommands `run-server`, `migrate`, `month-end-close`, `seed-fixtures`, `list-companies`, `list-pending-approvals`.

22. **Auth**: bearer-token middleware, JWT issuer, RBAC decorators (require_role, require_company_role), company-context resolution middleware rejecting unscoped requests.

23. **State machines**: explicit classes for expense/debt/settlement with allowed-transition matrices raising StateTransitionError.

---

## Soft Preferences

- Use Click (not typer) for CLI to keep deps minimal.
- SQLModel inheritance pattern with a shared `Base` timestamps mixin.
- Async everywhere (AsyncEngine, async session, FastAPI async endpoints).
- CamelCase↔snake_case mapping via Pydantic's `alias_generator`.
- `models/` module should own all table definitions; `schemas/` owns all DTOs.

---

## Explicit Non-Goals

- **No tests** (any file matching `test_*.py`, `tests/`, `conftest.py` must be stripped before delivery).
- **No CI/CD configuration** (no `.github/`, no Dockerfile unless explicitly required by spec — not required here).
- **No actual OCR/Tesseract integration** — stubs/shims are acceptable per subsystem 5.
- **No real email/webhook delivery** — stubs per subsystem 11.
- **No production deployment config** (no k8s manifests, no docker-compose).
- **No UI/frontend** — FastAPI APIs only, no HTML/JS/CSS.
- **No OpenAPI/Swagger customization** beyond what FastAPI generates by default.

---

## Open Ambiguities

| # | Ambiguity | Impact |
|---|-----------|--------|
| 1 | `spec.md` file does not exist on disk. Shall we assume the subsystem descriptions in this brief (from the acceptance contract) are the complete spec? | If spec.md is needed, we must infer it from the acceptance contract text. |
| 2 | Exact relationship between `models/` and per-subsystem models (e.g., `identity/models.py` vs `finance_platform/models/identity.py`). | Choice: either `models/` is the single source of truth or each subsystem owns its models with `models/` re-exporting. |
| 3 | Should `services/` facade call per-subsystem services or contain all business logic inline? | Convention needed: facade delegates to per-subsystem service classes (e.g., `identity/identity_service.py`). |
| 4 | Cryptography approach for JWT (PyJWT vs python-jose vs fastapi-jwt-auth). | Assume PyJWT (lightest dep). |
| 5 | `REDIS_URL` and `OBJECT_STORE_URL` config vars — are these used anywhere or just declared? | Assume declared but stubbed until integrate stage. |
| 6 | `finance_platform/schemas/` — one module per subsystem or single flat package? | Assume flat package with `_schema.py` suffix for discoverability. |

---

## Next Decision Boundary

After this brief is accepted, the **acceptance contract** step (`step.task-1777008735841.acceptance`) will formalize the spec. Then the **read-target-state** step will map what exists vs what must be authored. The primary execution phase will be **27+ author shards** (24 subsystems + models-and-schemas + migrations + integrate) running in parallel across 16 workers.

The first key decision for the planner: how to split the 24 subsystem packages into non-overlapping `writable_globs` assignments so that 16 workers each get ~1–2 subsystems and no paths collide.
