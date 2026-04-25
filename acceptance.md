# Acceptance Contract — `step.task-1777008735841.acceptance`

## 1. Pass/Fail Gates

Every gate below MUST pass for the deliverable to be accepted. Gates are organized by category.

### 1.1 Structural Gates

| # | Gate | Evidence Required |
|---|------|-------------------|
| G1 | ≥100 `.py` files exist under `src/finance_platform/` | `find src/finance_platform -name '*.py' \| wc -l` |
| G2 | ≥15,000 total LOC across all `.py` files under `src/` | `find src -name '*.py' \| xargs wc -l \| tail -1` |
| G3 | No single `.py` file exceeds 1500 lines | `find src -name '*.py' -exec wc -l {} + \| awk '$1 > 1500'` must be empty |
| G4 | Mean ≤280 LOC/file across Python sources | total LOC / file count ≤ 280 |
| G5 | `pyproject.toml` at repo root with `[project.name] = "finance-platform"` | `grep -q 'name.*finance-platform' pyproject.toml` |
| G6 | `pyproject.toml` declares runtime deps: fastapi, sqlmodel, pydantic, pydantic-settings, alembic, httpx | Check `[project.dependencies]` in pyproject.toml |
| G7 | `pyproject.toml` declares console script `finance_platform=finance_platform.cli:main` | `grep -q 'finance_platform.*finance_platform.cli:main' pyproject.toml` |
| G8 | `pip install -e .` succeeds in a clean venv | Install and confirm exit code 0 |
| G9 | `import finance_platform` succeeds | Python import test |
| G10 | `finance_platform.create_app()` returns a `fastapi.FastAPI` instance | Python type check |
| G11 | No `test_*.py` / `tests/` / `conftest.py` files shipped | `find . -name 'test_*.py' -o -name 'conftest.py' -type d -name 'tests'` must be empty |

### 1.2 Subsystem Coverage Gates

| # | Gate | Evidence Required |
|---|------|-------------------|
| G12 | ≥15 of 24 required subsystems are present as top-level packages under `src/finance_platform/` | Each subsystem = directory with ≥6 `.py` files and ≥1200 LOC. Verify with `find src/finance_platform/<subsys> -name '*.py' \| wc -l` and `wc -l src/finance_platform/<subsys>/**/*.py` |
| G13 | Each present subsystem has ≥6 `.py` files | Per-subsystem file count |
| G14 | Each present subsystem has ≥1200 LOC | Per-subsystem line count |

Subsystems required: identity, amortization, expenses, fx, ocr, watermark, approvals, settlements, debts, carry_forward, notifications, audit, models, schemas, routes, db, migrations, auth, config, errors, state_machines, services, cli, logging.

### 1.3 Functional Gates

| # | Gate | Evidence Required |
|---|------|-------------------|
| G15 | FastAPI app has ≥25 mounted routes covering MVP critical API set | `app.routes` count ≥25; inspect route paths |
| G16 | `create_app()` mounts every subsystem router | Code inspection of `create_app()` |
| G17 | Every route has company-context resolution; unscoped business routes return 400 | Route-level integration check |
| G18 | Monetary fields use integer `*_amount_minor` columns | Grep model definitions for `_amount_minor` as integer type |
| G19 | Pydantic DTOs expose monetary fields as Decimal strings | Grep schemas for Decimal str serialization |
| G20 | FX rate snapshots enforce immutability after creation (immutable_flag=true) | Service + repo layer check for UPDATE guard |
| G21 | Approval uniqueness: two approvals on same expense require distinct finance reviewers of same company | ApprovalService logic inspection |
| G22 | Void flow at least one original reviewer OR FINANCE_ADMIN substitution with audit entry | Void flow code inspection |
| G23 | Carry-forward records skip two-person approval → PENDING_AMORTIZATION, priority=HIGH | CarryForwardService logic inspection |
| G24 | Settlements clear HIGH-priority carry-forward first, then FIFO; over-registration rejected | SettlementService logic inspection |
| G25 | State machine classes for expense/debt/settlement with allowed-transition matrices raising StateTransitionError | Code inspection of state_machines/ |
| G26 | Domain events outbox pattern via audit/domain_events | Code inspection of AuditService or domain_events model |
| G27 | Services publish events to outbox, not directly to notification channels | Code inspection of service classes |
| G28 | ProblemDetail-style RFC-7807 HTTPException subclasses | Code inspection of errors/ |
| G29 | Domain exception hierarchy present: ValidationError, PermissionDeniedError, BusinessRuleViolation, StateTransitionError, CrossCompanyAccessError, FxRateMissingError, DebtAllocationError | Verify all 7 classes exist in errors/ |
| G30 | Bearer-token middleware, JWT issuer, RBAC decorators | Code inspection of auth/ |
| G31 | Company-context middleware rejects unscoped requests | Route-level check |
| G32 | structlog bootstrap, per-request correlation id, company-scoped log binder | Code inspection of logging/ |
| G33 | Alembic env.py + ≥3 revisions (0001_initial, 0002_multi_company_partitions, 0003_amortization_versioning) | `ls migrations/versions/` |
| G34 | Console entry with subcommands: run-server, migrate, month-end-close, seed-fixtures, list-companies, list-pending-approvals | CLI code inspection |
| G35 | `SPEC_MAPPING.md` linking each spec chapter to implementing module | File presence + content inspection |
| G36 | `README.md` with quickstart | File presence + inspection |

### 1.4 Worker Distribution Gates

| # | Gate | Evidence Required |
|---|------|-------------------|
| G37 | ≥8 distinct worker_ids contributed files | Git blame or worker manifest log |
| G38 | No single worker owns >45% of files | Worker file-count distribution |

## 2. Non-Goals (Explicitly Excluded Scope)

The following are NOT required to pass acceptance:

- Unit/integration/e2e tests (test files MUST be absent — per G11)
- CI/CD configuration (no `.github/`, no Dockerfile)
- Real OCR/Tesseract integration (stubs/shims acceptable)
- Real email/webhook delivery (stubs acceptable)
- Production deployment config (no k8s, no docker-compose)
- UI/frontend (no HTML/JS/CSS)
- OpenAPI/Swagger customization beyond FastAPI defaults
- Files outside `src/finance_platform/` and the repo root (pyproject.toml, README.md, SPEC_MAPPING.md, migrations/)
- Cross-shard consistency validation (integrate step handles stitching)

## 3. Review Level Required for Closure

**Level: Full Gate Review**

All 38 gates (G1–G38) MUST pass. The reviewer MUST:
1. Run every structural gate (G1–G11) script commands and confirm output
2. Perform code inspections for functional gates (G15–G36) across at least one representative file per subsystem
3. Verify worker distribution (G37–G38) from the build log
4. Confirm no test artifacts remain (G11)
5. Sign off only when all gates pass

## 4. Required Evidence Package

The deliverable MUST produce (or the review MUST collect):

1. **File manifest**: `find src/finance_platform -name '*.py' | sort` for file count and worker attribution
2. **LOC report**: `find src -name '*.py' | xargs wc -l` for total, per-file, and mean
3. **Dep check**: `pip install -e .` log in clean venv
4. **Import check**: `python -c "import finance_platform; print(finance_platform.create_app())"`
5. **Route dump**: `python -c "from finance_platform import create_app; app=create_app(); [print(r.path, r.methods) for r in app.routes]"`
6. **Model scan**: grep for `_amount_minor` integer columns across models
7. **Migration list**: `ls -la migrations/versions/`
8. **Subsystem count**: directory listing per subsystem with file and LOC counts
9. **Worker attribution**: deployment/CI log showing worker_id per file
10. **Exclusion proof**: `find . -name 'test_*.py' -o -name 'conftest.py' -type d -name 'tests'` returning empty

## 5. Ambiguity Resolutions (Binding)

Per the brief's Open Ambiguities table, the following binding decisions are made:

| # | Decision |
|---|----------|
| A1 | The subsystem descriptions in the brief are the complete spec. No spec.md is needed. |
| A2 | `models/` is the single source of truth for SQLModel table classes (all ~25+ tables). Each subsystem re-imports from `finance_platform.models` as needed. |
| A3 | `services/` is a facade that delegates to per-subsystem service classes (e.g., `identity/services/identity_service.py`). Business logic lives in the per-subsystem services, not in the facade. |
| A4 | Use PyJWT for JWT operations. |
| A5 | REDIS_URL and OBJECT_STORE_URL are declared in config but stubbed (not actively used) until integrate stage wiring. |
| A6 | `schemas/` is a flat package with `_schema.py` suffix files per DTO group (e.g., `user_schema.py`). |

## 6. Failure Boundaries

The deliverable FAILS acceptance if:

- **F1**: Any structural gate (G1–G11) fails
- **F2**: Fewer than 15 of 24 subsystems pass G12–G14
- **F3**: Fewer than 25 routes on the FastAPI app (G15)
- **F4**: `pip install -e .` or `import finance_platform` fails (G8–G9)
- **F5**: Any test file shipped (G11)
- **F6**: Worker distribution violates G37–G38
- **F7**: Monetary columns not using `*_amount_minor` integer convention (G18)
