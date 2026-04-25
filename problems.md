# Problems in this run

Run: `arpg_ae7b3d682326`, 2026-04-23, pytest exit 1 at 3320.43s (55:20).
16 workers on a DeepSeek-v4-pro + opencode stack.

## Build bulk

| | |
|---|---|
| `.py` files | **165** |
| Total LOC | **23,092** |
| Distinct subsystem packages committed | **24** (all required) |
| Distinct worker ids on the commit ledger | **11** of 16 |

The spec target was 20k–30k LOC across ≥100 files; the build landed squarely inside that range.

## Failure surface

Pytest terminated at the content-shape gate with one assertion:

```
[e2e] content-shape gate failed: multi-worker: worker 'ars-0' owns 64% of files (> cap 45%)
```

Running the remaining gates offline against the committed output surfaces a second real defect, and a third one that would have tripped the post-gate had the run gotten there.

## Problem 1 — multi-worker share 64% > 45% cap (test-config miscalibration)

Worker distribution from `task.contributions.jsonl`:

```
ars-0:   239 files  63.7%   ← owned the integrate shard + the services megashard
ars-1:    33 files   8.8%
ars-4:    26 files   6.9%
ars-13:   20 files   5.3%
ars-2:    17 files   4.5%
ars-9:     9 files   2.4%
ars-8:     8 files   2.1%
ars-14:    8 files   2.1%
ars-7:     8 files   2.1%
ars-3:     4 files   1.1%
ars-6:     3 files   0.8%
```

### Why this is not really a build defect

A worker is *credited* with a file the moment **its lease committed** that file, not the moment the file was authored. The **integrate shard** runs last; its job is to start from a snapshot of the whole project directory, rewrite `pyproject.toml`, stitch `__init__.py` re-exports, fix cross-package imports, and emit `SPEC_MAPPING.md`. When its lease completes, the dispatcher credits every file the integrate shard touched back to the integrate worker — *including files that other workers originally authored*.

So the single worker that happens to draw the integrate shard collects a big commit share automatically. In this run, `ars-0` drew **both** the integrate shard **and** the earlier 1.6MB-stderr `services` megashard (the nine business-service facades), which double-stacked its commit count.

### The cap we set vs. existing tests

The test's `max_worker_share=0.45` was stricter than any other bootstrap-e2e scenario:

| Test | `max_worker_share` |
|---|---|
| `test_bootstrap_arpg.py` | 0.60 |
| `test_bootstrap_etl.py` | 0.60 |
| `test_bootstrap_rest_api.py` | 0.65 |
| `test_bootstrap_financial_platform.py` | **0.45** (too tight) |

The other scenarios hit 60%+ share for exactly the same reason (their integrate shards consolidate a lot), and calibrated up. This test was set against a build with a *bigger* integrate surface and a tighter cap, which is why it tripped.

### Proper fix

Raise `max_worker_share` to 0.65 to match the REST-API scenario's shape (integrate-heavy). A more accurate gate would measure fan-out by **shard_key ownership** rather than commit attribution, but that's a bigger gate rewrite.

## Problem 2 — FX immutability invariant missed (real spec miss)

The `_assert_spec_invariants` gate (AST-level) raises:

```
spec-invariant: no FX snapshot module ships an ``immutable_flag``;
                the spec mandates FX-lock immutability.
```

### Why this invariant exists

Read `spec.md` §8.4 (Immutable FX Locking Principle) and §11.3.1 (`fx_rate_snapshots` table). In a reimbursement system, the FX rate is the locked exchange rate used to convert a foreign-currency receipt into CNY. A malicious or sloppy actor could rewrite the historical rate *after* approval — e.g., change USD→CNY on an old $100 receipt from 7.0 to 100.0 — and silently inflate their reimbursement 14×. The same rate cascades into amortization debts, month-end balances, and settlement allocations, so mutating it manipulates the whole ledger.

The spec therefore mandates three defences:
- column `immutable_flag` on `fx_rate_snapshots` — once flipped true, the row's FX fields become read-only.
- repository layer: refuses `UPDATE` against the row.
- data layer: a DB trigger or constraint blocks in-place mutation. Corrections go through **void-old + create-new**, never direct update.

### What the model actually shipped

`src/finance_platform/models/fx_rate.py`:

```python
class FxRateSnapshot(TimestampMixin):
    base_currency: CurrencyCode
    snapshot_date: date
    source: str = "ecb"
    rates: Dict[str, float] = Field(default_factory=dict)
```

No `immutable_flag`, no `is_locked` method, no repository method that raises on update. Fully mutable pydantic model. The shape of an FX snapshot is there; the entire anti-fraud backbone is not.

### What the gate did

`_assert_spec_invariants` walks every `.py` file under the output tree and looks for a module that mentions both an `FxRateSnapshot`/`fx_rate_snapshot` identifier **and** the word `immutable`/`immutable_flag` in the same file. It's deliberately loose (any reasonable encoding counts). No such module exists in the committed output, so the gate correctly fails.

This is exactly the kind of thing the structural gates exist to re-surface: an LLM drowning in 24 subsystems' worth of requirements quietly dropped the most critical anti-fraud contract while satisfying everything else.

### Proper fix

Keep the invariant. Broaden the acceptance surface slightly — also accept a repository/service module that declares an `update` method which raises on FX-snapshot mutation — so the model has more than one way to satisfy the contract. But do not weaken the requirement: if the build ships no immutability enforcement anywhere, the gate should fail.

## Problem 3 — broken `fx/` subpackage imports (would have tripped the post-gate)

While tracing Problem 2, we also noticed the integrate step shipped:

```python
# src/finance_platform/fx/__init__.py
from finance_platform.fx.models import FxRateSnapshot, ...
from finance_platform.fx.service import FxRateService
from finance_platform.fx.repository import FxRateRepository
from finance_platform.fx.adapters import (
    CorporateTableAdapter, BankApiAdapter, ThirdPartyAdapter, get_fx_source_adapter,
)
from finance_platform.fx.routes import router as fx_router
```

But `src/finance_platform/fx/` contains **only `__init__.py`** — no `models.py`, `service.py`, `repository.py`, `adapters.py`, or `routes.py`. The actual FX model lives at `src/finance_platform/models/fx_rate.py` (outside the `fx/` package) and is only partially wired there.

### Symptom

`import finance_platform` would blow up the first time Python walks into `finance_platform.fx`, on the first line of that `__init__.py`.

### Why the content-shape gate didn't catch it

The structural gates (`_assert_scale`, `_assert_has_categories`, `_assert_spec_invariants`) only inspect file shape, LOC counts, identifier presence, and specific AST patterns. They do not execute the package. The **post-gate** (`_financial_post_gate`) is what exercises `pip install + import + create_app()` — and it would have tripped on exactly this import. But post-gate never ran because the multi-worker gate tripped first.

### Likely root cause

The `fx` authoring shard only produced `__init__.py` before exiting (either a harness crash, a token-budget exhaustion, or a planner misrouting), and the integrate shard trusted the `__init__.py` it found in the snapshot without validating the imports. This is the kind of bug the existing `docs/gaps.md` integrate-step hardening work is targeting; this run's `fx` shard was a casualty of that gap.

### Proper fix

Nothing in the test — the post-gate already catches it. Ensure the next run's `fx` shard doesn't drop half its files on the floor (either by re-running or by a planner-level constraint that every `<cat>/__init__.py` must co-ship the siblings it imports).

## Summary

| # | Surface | Actual cause | Fix location |
|---|---|---|---|
| 1 | `worker 'ars-0' owns 64%` > 45% cap | test cap stricter than any existing scenario; integrate-shard commit-ledger inflation | `test_bootstrap_financial_platform.py`: raise `max_worker_share` → 0.65 |
| 2 | `no FX snapshot module ships immutable_flag` | build genuinely dropped the §8.4 anti-fraud contract | LLM build; gate is correct and should stay |
| 3 | `fx/__init__.py` references non-existent siblings | `fx` authoring shard only emitted the `__init__.py`; integrate trusted it | LLM build; post-gate catches this on re-run |

Of these, only #1 is the test's fault. #2 and #3 are real build defects — and the test structure (AST invariants + post-gate) is exactly what's supposed to surface them.
