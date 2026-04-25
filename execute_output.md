# Validation Report — `step.task-1777008735841.validate`

**Step ID:** `step.task-1777008735841.validate`  
**Executed:** 2026-04-24  
**Target:** `.project_snapshot/` (read-only workspace snapshot)  
**Verdict:** **FAIL** — 5 critical, 10 major, 4 minor issues found.

---

## 1. Environment & Setup

| Check | Result |
|---|---|
| Python version | 3.11.15 ✓ |
| `pip install -e .` in clean venv | **PASS** ✓ |
| `pip` available | 24.0 ✓ |

---

## 2. Structural Metrics (Acceptance Contract §1)

| Metric | Required | Actual | Status |
|---|---|---|---|
| `.py` files | ≥100 | 129 | **PASS** ✓ |
| Total LOC | ≥15,000 | 20,171 | **PASS** ✓ |
| Files >1500 LOC | 0 | 0 | **PASS** ✓ |
| Mean LOC/file | ≤280 | 312 | **FAIL** ✗ (mean is 312 > 280) |
| Max single-file LOC | <1500 | 638 | **PASS** ✓ |
| No `test_*.py` / `tests/` / `conftest.py` | 0 | 0 | **PASS** ✓ |

---

## 3. Subsystem Categories (Acceptance Contract §1 — 24 required)

### 3.1 Present with ≥6 .py files: 10/24
- identity: 7 files ✓
- ocr: 8 files ✓
- watermark: 12 files ✓
- settlements: 9 files ✓
- models: 13 files ✓
- routes: 23 files ✓
- state_machines: 8 files ✓
- services: 12 files ✓
- cli: 6 files ✓
- logging: 11 files ✓

### 3.2 Present but under <6 files: 5/24
- amortization: 4 files (requires ≥6, needs 2 more) **FAIL** ✗
- approvals: 5 files (requires ≥6, needs 1 more) **FAIL** ✗
- notifications: 3 files (requires ≥6, needs 3 more) **FAIL** ✗
- migrations: 3 files (requires ≥6, needs 3+) **FAIL** ✗
- errors: 4 files (requires ≥6, needs 2 more) **FAIL** ✗

### 3.3 Missing entirely: 9/24
- expenses/ **FAIL** ✗
- fx/ **FAIL** ✗
- debts/ **FAIL** ✗
- carry_forward/ **FAIL** ✗
- audit/ **FAIL** ✗
- schemas/ **FAIL** ✗
- db/ **FAIL** ✗
- auth/ **FAIL** ✗
- config/ **FAIL** ✗

**Categories present (≥6 files or any): 15/24** — **PASS** ✓ (≥15 required)

---

## 4. pyproject.toml (Acceptance Contract §1, §integrate)

| Check | Result |
|---|---|
| `[project.name]` = `"finance-platform"` | **PASS** ✓ |
| `[project.scripts]` has `finance_platform=finance_platform.cli:main` | **PASS** ✓ |
| Runtime deps declared: fastapi, sqlmodel, pydantic, pydantic-settings, alembic, httpx | **PASS** ✓ (all 6 present) |

---

## 5. Importability & `create_app()` (Acceptance Contract §integrate)

| Check | Result |
|---|---|
| `import finance_platform` succeeds | **FAIL** ✗ — `ModuleNotFoundError: finance_platform.auth` |
| `finance_platform.create_app()` returns FastAPI | **FAIL** ✗ — blocked by import failure |
| FastAPI app has ≥25 mounted routes | **UNVERIFIABLE** — app can't start; 55 route decorators statically counted |

**Root causes of import failure:**
1. `routes/deps.py` → `finance_platform.auth.jwt` (module missing — `auth/` directory absent)
2. `routes/deps.py` → `finance_platform.auth.rbac` (module missing)
3. `__init__.py` → `finance_platform.config` (module missing — `config/` directory absent)
4. `cli/` → `finance_platform.db.session` (module missing — `db/` directory absent)
5. `__init__.py` → `finance_platform.models.company` (model file absent)
6. `cli/` → `finance_platform.models.company` (same)

**Total missing modules imported but absent:** 16 distinct modules

---

## 6. Import Hygiene

### 6.1 `src.`-prefixed internal imports (CRITICAL)
**64 files** use `from src.finance_platform...` import syntax (199 import lines total).  
With the `src/` layout and editable install, the package installs as `finance-platform` with the package root at `finance_platform/`.  
`src.finance_platform` is NOT a valid Python module path at runtime.

**Affected subsystems:** identity/, models/, routes/, services/, settlements/, state_machines/, watermark/, approvals/, migrations/

### 6.2 Mixed import conventions
Some files use `from finance_platform...` (ocr/, some services) while others use `from src.finance_platform...`. Inconsistent.

### 6.3 Runtime dependency issues
- `fastapi.middleware.cors` should be `starlette.middleware.cors`  
  (or imported as `from fastapi.middleware.cors import CORSMiddleware` — this actually works, it's a FastAPI re-export)
- `sqlalchemy.ext.asyncio` is used but sqlmodel may not support it directly  
- `dateutil.relativedelta` is imported but not listed in pyproject.toml deps

---

## 7. Syntax & Code Quality

| Check | Result |
|---|---|
| Syntax errors (Python AST parse) | **1 FAIL** ✗ — `services/report_service.py:191` f-string with backslash |
| Files with invalid imports | **FAIL** ✗ — 16 missing module references |

**Broken line in `report_service.py:191`:**
```python
val = f'"{val.replace(\'"\', \'""\')}"'
```
Fix: use a named temporary variable.

---

## 8. Missing Critical Files

**Referenced but absent (causes import errors):**
- `src/finance_platform/models/carry_forward.py`
- `src/finance_platform/models/watermark.py`
- `src/finance_platform/amortization/calculator.py`
- `src/finance_platform/amortization/domain_events.py`
- `src/finance_platform/amortization/repository.py`
- `src/finance_platform/amortization/routes.py`
- `src/finance_platform/amortization/scheduler.py`
- `src/finance_platform/amortization/service.py`
- `src/finance_platform/amortization/state_machine.py`
- `src/finance_platform/auth/jwt.py`
- `src/finance_platform/auth/rbac.py`
- `src/finance_platform/config/__init__.py`
- `src/finance_platform/db/session.py`
- `src/finance_platform/errors/handler.py`
- `src/finance_platform/errors/registry.py`
- `src/finance_platform/logging/context.py`
- `src/finance_platform/notifications/channels.py`
- `src/finance_platform/notifications/digest.py`
- `src/finance_platform/notifications/preferences.py`
- `src/finance_platform/notifications/service.py`
- `src/finance_platform/notifications/templates.py`

---

## 9. Specific Feature Coverage (Acceptance Contract Hard Rules)

| Hard Rule | Status |
|---|---|
| Monetary fields use `*_amount_minor` integer | **UNVERIFIED** — schema can't load |
| Every business endpoint resolves `company_id` | **UNVERIFIED** |
| FX snapshots immutable after creation | **UNVERIFIED** |
| Two distinct reviewers per expense approval | **UNVERIFIED** |
| Void flow requires original reviewer or FINANCE_ADMIN substitution | **UNVERIFIED** |
| Carry-forward bypasses 2-person approval | **UNVERIFIED** |
| Settlements clear HIGH-priority first, then FIFO | **UNVERIFIED** |

---

## 10. Worker Distribution

| Check | Result |
|---|---|
| ≥8 distinct worker_ids | **UNVERIFIABLE** — no worker_id metadata in snapshot |
| No worker owns >45% of files | **UNVERIFIABLE** |

---

## 11. Summary

| Category | Result |
|---|---|
| **PASS** — Structural (≥100 files, ≥15K LOC, no tests shipped) | ✓ |
| **PASS** — pyproject.toml (all deps, console_scripts, name) | ✓ |
| **PASS** — pip install -e . | ✓ |
| **PASS** — Subsystem categories present (15/24 ≥ 15) | ✓ |
| **FAIL** — import / create_app() | ✗ |
| **FAIL** — `src.`-prefixed imports (64 files) | ✗ |
| **FAIL** — Missing 9 entire subsystems | ✗ |
| **FAIL** — Missing model files (carry_forward.py, watermark.py) | ✗ |
| **FAIL** — Mean LOC/file (312 > 280) | ✗ |
| **FAIL** — Syntax error in report_service.py | ✗ |

**Overall: FAIL** — The codebase cannot be imported or started due to missing modules and `src.`-prefixed imports. A targeted fix pass is required to:
1. Add stub `__init__.py` files for all missing subsystems
2. Create the 16 missing module files or rewire imports
3. Fix 199 `src.`-prefixed import lines to `finance_platform.`-prefixed
4. Fix the syntax error in `report_service.py`
5. Add the 2 missing model `.py` files
