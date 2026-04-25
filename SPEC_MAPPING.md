# SPEC_MAPPING

The following table maps each specification requirement chapter to its implementing module(s) in `src/finance_platform/`.

| Spec Chapter | Implementing Module(s) | Description |
|---|---|---|
| 1. Identity & Companies | `identity/`, `models/user.py`, `models/__init__.py` | Users, companies, company memberships, roles, finance groups |
| 2. Expenses | `expenses/`, `models/expense.py` | Expense CRUD, line items, attachments, policy validation |
| 3. Approvals | `approvals/`, `models/approval.py`, `state_machines/approval.py` | Approval chains, steps, workflow, delegation, uniqueness rules |
| 4. Amortization | `amortization/`, `models/amortization.py`, `state_machines/amortization.py` | Amortization schedules, entries, calculators, forecasting |
| 5. OCR | `ocr/`, `models/ocr_record.py` | Document OCR, field extraction, confidence scoring |
| 6. Watermark | `watermark/`, `models/watermark.py` | Document watermarking, detection, policy enforcement |
| 7. FX Rates | `fx/`, `models/fx_rate.py` | FX rate management, immutable snapshots, conversion |
| 8. Debts | `debts/`, `models/debt.py`, `state_machines/debt.py` | Debt tracking, repayment, write-off |
| 9. Carry Forward | `carry_forward/`, `models/carry_forward.py` | Period carry-forward with HIGH priority bypass |
| 10. Settlements | `settlements/`, `models/settlement.py`, `state_machines/settlement.py` | Settlement runs, allocations, priority queuing |
| 11. Notifications | `notifications/`, `models/notification.py` | Notification templates, channels, digest, preferences |
| 12. Audit | `audit/`, `models/audit_log.py` | Audit logging, domain event outbox pattern |
| 13. Routes | `routes/` | FastAPI route registration, middleware, company context |
| 14. Auth | `auth/` | JWT bearer tokens, RBAC decorators, company resolution |
| 15. Config | `config/` | Pydantic-settings configuration classes |
| 16. DB | `db/` | Async engine, session factory, connection management |
| 17. Errors | `errors/` | Domain exception hierarchy, RFC-7807 ProblemDetail |
| 18. State Machines | `state_machines/` | Explicit transition matrices for expense/debt/settlement |
| 19. Services | `services/` | Facade layer delegating to per-subsystem services |
| 20. CLI | `cli/` | Click-based CLI with subcommands |
| 21. Logging | `logging/` | Structlog, correlation IDs, company-scoped binders |
| 22. Migrations | `migrations/` | Alembic migration scripts |
| 23. Schemas | `schemas/` | Pydantic DTOs with Decimal string monetary serialization |
| 24. Models | `models/` | SQLModel table definitions (single source of truth) |
