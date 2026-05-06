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
