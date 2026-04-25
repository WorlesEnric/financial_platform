# problem.md — why 5 subpackages shipped broken

Run: `arpg_ae7b3d682326`, 2026-04-23.
Artifact: `artifacts/financial_platform/src/finance_platform/`.

Five subpackages contain only `__init__.py`, and each of those
`__init__.py` files re-exports from siblings that do not exist:

| Subpackage | `__init__.py` re-exports from | Siblings shipped |
|---|---|---|
| `audit/` | `.models`, `.schemas`, `.service`, `.repository`, `.routes` | none |
| `carry_forward/` | `.models`, `.schemas`, `.service`, `.repository`, `.routes` | none |
| `expenses/` | `.models`, `.schemas`, `.service`, `.repository`, `.state_machine`, `.routes` | none |
| `fx/` | `.models`, `.schemas`, `.service`, `.repository`, `.adapters`, `.routes` | none |
| `debts/` | `.models`, `.schemas`, `.service`, `.repository`, `.state_machine`, `.routes` | none |

`import finance_platform` still succeeds because the top-level
`__init__.py` does not walk into these subpackages, and `create_app()`
wires every router through `finance_platform.routes.*_routes` (the
centralized layout), so nothing at runtime trips the broken imports.
But any downstream caller writing `from finance_platform.audit import
AuditService` crashes on `ModuleNotFoundError: finance_platform.audit.service`.

The real business logic exists — just in a *different* layout:
`models/audit_log.py`, `services/audit_service.py`,
`routes/audit_routes.py`, and the parallel files for the other four
subsystems. There are no missing features. There is a layout
split that integrate never reconciled.

## The timeline across leases

All evidence is in `tests/artifacts/arpg_ae7b3d682326/workspaces/shards/`.

1. **`lease-0d9e2311f0bf` — `models_and_schemas` (ars-?)**
   - writable_globs: `src/finance_platform/models/**`,
     `src/finance_platform/schemas/**`,
     `src/finance_platform/__init__.py` (permissive `**`).
   - Stopped after writing 10 model files
     (`models/audit_log.py`, `models/carry_forward.py*`,
     `models/expense.py`, `models/fx_rate.py`, `models/debt.py`, …).
     Wrote **zero** schema files despite the shard being called
     "models_and_schemas". The harness.stdout for this lease
     ends mid-sentence: `"Now I'll create all the model and schema
     files. Let me start with the models:"` — then the worker's
     output budget is consumed by the 10 large model files and it
     exits without reaching schemas.
     (*) `models/carry_forward.py` and `models/watermark.py` were
     not in this lease's output either; they were added later by
     `fix_missing_subsystems`.
2. **Per-subsystem `isa:author.scoped-module@v0` shards** ran in
   parallel (`expense_service`, `fx_service`, `audit_service`,
   `carry_forward_service`, etc.). Each wrote its business logic
   into the centralized locations
   (`services/<name>_service.py`, `routes/<name>_routes.py`), not
   into per-subsystem directories. This was consistent with the
   layout that `models/` already imposed.
3. **`validate` step** (run from a snapshot after #1 and #2):
   reported 9 missing subsystems —
   `expenses/`, `fx/`, `debts/`, `carry_forward/`, `audit/`,
   `schemas/`, `db/`, `auth/`, `config/` — plus 16 missing module
   files *referenced by existing imports*. See
   `execute_output.md` §3.3 and §8.
4. **`lease-9f3183f3b223` — `fix_missing_subsystems` (ars-0)**.
   Instruction `isa:author.structured-batch@v0`. writable_globs
   were 29 **enumerated literal file paths** (see
   `PROMPT_META.json:8-37`). For `auth/`, `db/`, `amortization/`,
   `notifications/`, `errors/`, `models/`, `logging/`: both the
   `__init__.py` AND the referenced siblings were on the list
   (e.g. `auth/__init__.py`, `auth/jwt.py`, `auth/rbac.py`). For
   `audit/`, `carry_forward/`, `expenses/`, `fx/`, `debts/`: only
   `<pkg>/__init__.py` — no siblings.
5. **Worker commit** — the cpmr-runtime log records
   `slot_result lease=lease-9f3183f3b223 → SUCCEEDED (37 files committed)`.
   37, despite 29 in writable_globs. The worker wrote 8 extra
   schema files (`schemas/user_schema.py`, `schemas/common.py`,
   etc.) on its own initiative, plus the 29 enumerated ones.
   **The dispatcher committed all 37 unconditionally** — see the
   next section for why.
6. **`integrate` shard** runs last; stitches `pyproject.toml`,
   top-level `__init__.py`, `README.md`, `SPEC_MAPPING.md`. It
   does NOT import or resolve the subpackages it inherits from
   the snapshot, so the broken re-exports survive.

## The ISA dispatch bug — writable_globs unenforced for the fix shard

`src/echothink/core/cpmr/dispatcher/service.py:117-123` defines the
set of instruction ids that the commit gate enforces:

```python
_SHARD_INSTRUCTIONS = frozenset(
    {
        "isa:author.scoped-module@v0",
        "isa:author.scoped-level@v0",
        "isa:author.integrate-codebase@v0",
    }
)
```

`_commit_shard` at line 679 gates the writable_globs check on
membership in that set:

```python
is_shard = inflight.instruction_id in _SHARD_INSTRUCTIONS
...
for fp in candidates:
    rel = str(fp.relative_to(scratch))
    if is_shard and not _matches_any(rel, inflight.writable_globs):
        if _is_permitted_init_py(rel, inflight.writable_globs):
            ...
        else:
            violations.append(rel)
            continue
    target = project / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fp, target)
    committed.append(rel)
```

`fix_missing_subsystems` was dispatched under instruction id
**`isa:author.structured-batch@v0`** (`PROMPT_META.json:3`), which is
NOT in `_SHARD_INSTRUCTIONS`. Therefore `is_shard = False`, the
writable_globs check is skipped entirely, and every scratch file is
copied into the project directory.

That explains the 8 extra schema files that made it through — the
glob contract is decorative for this instruction class. More
importantly, it meant the planner had no safety net when the
writable_globs list under-specified the fix recipe. A build that
*does* enforce globs would have rejected the 8 schema files as
violations, causing the planner to re-emit a follow-on shard with
the right globs; here it shipped.

## Why only `__init__.py` for audit / carry_forward / expenses / fx / debts

The validate step's recipe for writable_globs appears to be:

- a `<pkg>/__init__.py` for every subpackage flagged as "missing
  entirely" in §3.3 of the validation report, plus
- every missing module file that some *existing* source file
  *already imported from*.

For `auth/` and `db/`, existing code did
`from finance_platform.auth.jwt import ...` and
`from finance_platform.db.session import ...` (see
`routes/deps.py`, `cli/main.py`, etc.), so `auth/jwt.py`,
`auth/rbac.py`, `db/session.py` were added to the fix list.

For `audit/`, `carry_forward/`, `expenses/`, `fx/`, `debts/`,
**no existing source file imported from these subpackages** —
because the earlier shards had already centralized that logic into
`services/audit_service.py`, `models/audit_log.py`,
`routes/audit_routes.py`, and the parallel paths for the other
four. The validate step had nothing to enumerate as "referenced
but missing". So it gave the worker one target per subpackage:
`<pkg>/__init__.py`.

The LLM author for the fix shard, seeing a target like
`src/finance_platform/audit/__init__.py` and the spec's per-subsystem
description ("audit/ — audit_logs + domain_events + outbox pattern"),
wrote a canonical re-export stub:

```python
from finance_platform.audit.models import AuditLog, DomainEvent, ...
from finance_platform.audit.service import AuditService
from finance_platform.audit.routes import router as audit_router
```

The worker was coding against the spec's mental model, not against
the filesystem state. It assumed it or a sibling shard would land
the `.models` / `.service` / `.routes` files; no sibling shard did.

## Responsibility summary

| Layer | Defect | Evidence |
|---|---|---|
| Dispatcher | `isa:author.structured-batch@v0` not in `_SHARD_INSTRUCTIONS`; writable_globs are unenforced, so the platform never rejected the under-specified fix. | `dispatcher/service.py:117-123`, commit log `37 files committed` on lease with 29 declared paths |
| Planner (validate step) | Derives writable_globs from "referenced-but-missing" imports. Five subpackages had no references, so only `__init__.py` was enumerated. No cross-check against spec-described module layout. | `lease-9f3183f3b223/PROMPT_META.json:8-37` |
| Worker (fix shard, LLM) | Wrote `__init__.py` re-exports pointing at `.models`/`.service`/etc. without verifying those siblings were in writable_globs or on disk. | the five broken `__init__.py` files themselves |
| Integrate shard | Did not resolve the subpackage `__init__.py` files (no import probe). Trusted snapshot as-is. | `execute_output.md` §5 (import check failed, but integrate ran to produce the `snapshot` artifact anyway) |
| Gate order | Multi-worker share gate trips before the post-gate that would actually `import finance_platform.audit`; the broken subpackages never reached the probe. | `problems.md` §Problem 1 |

Only the dispatcher defect is a platform bug we can fix in-repo.
The other layers are content quality issues that compound because
the dispatcher silently accepts the result.

## Proper fixes (not executed here)

1. **Add `isa:author.structured-batch@v0` to `_SHARD_INSTRUCTIONS`**
   in `dispatcher/service.py:117-123`, OR explicitly document it as
   a non-shard (reviewer-side) instruction. If the former, the
   write-out pattern in `_commit_shard` will then refuse the 8
   schema files and the 5 broken `__init__.py` stubs' underspecified
   writable_globs will surface as an ingress-time planner error.

2. **Validate step should include spec-implied siblings**, not only
   "files referenced by existing imports". When the spec names a
   subsystem with `models / service / routes` components, the fix
   recipe should enumerate all of them — either as concrete globs
   or as a `<pkg>/**` wildcard — otherwise the worker has no
   latitude to ship a working subpackage.

3. **Integrate shard should import-probe** every subpackage's
   `__init__.py` against the snapshot before stitching
   `SPEC_MAPPING.md`. Broken re-exports become a validate-step
   failure instead of a silent post-gate bomb.

None of these is in scope for this PR — this PR only repairs the
artifact copy so the 5 broken `__init__.py` files re-export from
the real (centralized) locations where the logic actually ships.
