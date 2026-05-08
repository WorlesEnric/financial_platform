# Finance Platform

Enterprise Financial Reimbursement + Amortization Platform.

## Quickstart

```bash
# Install the package
pip install -e .

# Start the server
finance_platform run-server

# Apply database migrations
finance_platform migrate

# Seed demo data
finance_platform seed-fixtures
```

## System Requirements

- Python >= 3.11
- PostgreSQL (for production) or SQLite (for development)

## Configuration

Set environment variables or create a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./finance.db` | Database connection string |
| `SECRET_KEY` | (auto-generated) | JWT signing key |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |

## CLI Commands

- `run-server` — Start the FastAPI development server
- `migrate` — Apply Alembic database migrations
- `month-end-close` — Run month-end carry-forward and settlement sweep
- `seed-fixtures` — Seed demo companies, users, and expenses
- `list-companies` — List all registered companies
- `list-pending-approvals` — List pending approvals

## Frontend

The platform includes a lightweight **Jinja2 + HTMX** frontend served directly by FastAPI:

- **Dashboard** (`/`) — Overview with summary statistics, recent expenses, pending approvals, and settlement status.
- **Expenses** (`/expenses`) — List, search, and filter expenses by status. Detail view with line items, attachments, and action buttons.
- **Approvals** (`/approvals/pending`) — Pending approval queue with decision actions.
- **Settlements** (`/settlements`) — Settlement runs and allocation status.

The frontend leverages HTMX for dynamic interactions (inline updates, pagination, form submissions) without a full JavaScript framework dependency. Company context is resolved via the `X-Company-Id` header.

### Frontend Strategy

This Jinja2 + HTMX frontend complements the existing API documentation surfaces:

- Interactive API docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc

**Scope note:** The repository brief.md originally specified "No UI/frontend — FastAPI APIs only, no HTML/JS/CSS" as a non-goal. This frontend addition intentionally overrides that constraint per domain work intent (priority=high). The override is documented here for auditability.

## API

Once the server is running, visit:

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Company Context

All business endpoints require the `X-Company-Id` header. Unscoped requests return 400.

## Frontend Strategy

This platform is **backend-first by design**. The API *is* the product.

### Official User Interfaces

The following interfaces are the official, supported ways to interact with the platform:

| Interface | URL | Audience |
|---|---|---|
| **Swagger UI** | `/docs` | Developers, integrators, power users |
| **ReDoc** | `/redoc` | API consumers, documentation readers |
| **CLI** | `finance_platform <command>` | Operators, administrators |

All platform capabilities — expense submission, approval workflows, amortization schedules, settlement runs, FX rate management, and audit trails — are exposed through REST endpoints documented at `/docs` and `/redoc`. There is no separate HTML/JS/CSS frontend, and adding one is explicitly out of scope for the current acceptance baseline (see `acceptance.md` §2, Non-Goals).

### Design Rationale

- **Python-only ecosystem**: the entire stack lives in Python ≥3.11. Introducing a JavaScript/Node build chain would add a new toolchain, CI pipeline, and test infrastructure — a significant scope increase not budgeted for this phase.
- **Clean separation of concerns**: the service layer, auth middleware, state machines, and domain exceptions already form a complete backend. `/docs` provides an interactive, auto-generated UI for every endpoint with zero additional code.
- **CLI-first operations**: month-end close, migrations, seeding, and listing are operator workflows best served by a CLI. The CLI is the primary operations interface.
- **API-first consumption model**: the platform is designed to be consumed by other systems (ERP integrations, reporting tools, downstream services). A well-documented REST API with OpenAPI specs is the correct interface for that consumption pattern.

### Roadmap Considerations

If a graphical frontend becomes necessary for non-technical users (e.g., expense submitters who cannot use Swagger UI), the following options preserve the Python-only constraint:

1. **Server-rendered Jinja2 templates** — add `jinja2` to `pyproject.toml`, create server-rendered HTML pages served from FastAPI route handlers. Stays in Python, no JS build step. Requires template maintenance discipline.
2. **htmx-enhanced server UI** — build on Jinja2 with a single htmx JS file (no build step) for inline approvals, live filtering, and partial-page updates. Keeps logic in Python.
3. **Separate SPA** — a React/Vue frontend in a new repository consuming the FastAPI endpoints. Requires JS/Node toolchain, CORS configuration, and a separate deployment pipeline.

These options are documented for planning purposes only. None are currently in scope.

## Architecture

- **models/** — SQLModel table definitions (single source of truth)
- **schemas/** — Pydantic DTOs with Decimal string serialization for monetary fields
- **routes/** — FastAPI routers with company-context resolution
- **services/** — Facade layer delegating to per-subsystem service classes
- **errors/** — Domain exception hierarchy with RFC-7807 ProblemDetail formatting
- **state_machines/** — Explicit state machines for expense/debt/settlement transitions
- **config/** — Pydantic-settings based configuration
- **logging/** — Structlog with per-request correlation IDs and company-scoped binders
- **auth/** — JWT bearer-token middleware with RBAC decorators
- **db/** — Async SQLAlchemy engine and session factory
- **migrations/** — Alembic migration scripts

## Project Scope

The current acceptance baseline (see `acceptance.md`) defines the following scope boundaries:

**In scope:** backend services, REST API, CLI, database models, auth, state machines, audit logging, migrations, OpenAPI documentation via FastAPI defaults.

**Out of scope:** HTML/JS/CSS frontend, CI/CD configuration, real OCR/Tesseract integration, real email/webhook delivery, production deployment config, test files, OpenAPI customization beyond FastAPI defaults.

Refer to `acceptance.md` for the full gate list (G1–G38) and `SPEC_MAPPING.md` for the spec-to-module mapping.
