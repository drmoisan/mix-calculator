# Code Review: mix-category-customer-mix-tieout (#20) — R4 Re-review

**Review Date:** 2026-05-28
**Review Type:** Remediation pass 1 (R4) re-review after test-module split
**Branch:** `fix/mix-category-customer-mix-tieout-20`
**Merge-base:** `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`
**Head:** `528dcbc37a0422cced21b70c61e0ce34ec1a120f`
**Scope:** full feature-branch diff against `origin/main`

---

## Executive Summary

The R4 remediation cleanly addressed the single Blocking finding from R3 (test-module size). The split is mechanical, additive, and preserves test count and behavior:

- `tests/test_mix_rollups.py`: 562 → 204 lines (eight rollup/layer/stage tests).
- `tests/_mix_rollups_fixtures.py`: new shared fixture module, 225 lines, with `__all__` enumerating the six exported helpers consumed by the two test modules.
- `tests/test_mix_rollups_tieout.py`: new peer test module, 167 lines, containing exactly the three AC8/single-scenario regression tests.

Production code is unchanged from R3. The full Python toolchain (Black, Ruff, Pyright, Pytest+coverage) was re-run by this reviewer and passes cleanly in a single pass; 220 tests pass with 100% line and 100% branch coverage. All R3 PASS findings (design, type safety, docstrings, determinism, scope discipline, confidentiality) hold unchanged. No new code-quality issues observed.

**Verdict: PASS.** 0 Blocking, 0 Non-Blocking findings.

---

## Changes Reviewed (against merge-base)

### Production code (unchanged in R4)

- `src/mix_rollups.py` (+58/-32) — `build_mix_2_category`, `build_mix_3_customer`, `build_mix_4_country` accept `mix_base` and aggregate at their own granularity.
- `src/_mix_rollups_helpers.py` (+21/-63) — removed now-unused `unstack_to_long`; helpers stay pure.
- `src/mix_pipeline_run.py` (+7/-4) — `run_transforms` threads `mix_base` to the changed builders.

### Tests (changed by R4 split)

- `tests/test_mix_rollups.py` — 562 → 204 lines. Retains the eight rollup/layer/stage tests; imports six shared fixtures from `tests/_mix_rollups_fixtures.py`.
- `tests/_mix_rollups_fixtures.py` — new, 225 lines. Module docstring states purpose and non-pytest nature. `__all__` enumerates the six exported helpers (`_f`, `_mix_base_rows`, `_mix_base_fixture`, `_rate_impacts_fixture`, `_single_scenario_mix_base_fixture`, `_unfiltered_group_lbs_le`).
- `tests/test_mix_rollups_tieout.py` — new, 167 lines. Contains exactly the three AC8/single-scenario regression tests (`test_category_layer_retains_single_scenario_volume`, `test_customer_layer_retains_single_scenario_volume`, `test_layer_mix_equals_full_aggregation_minus_rollup`); imports fixtures from `tests/_mix_rollups_fixtures.py`.
- `tests/mix_bottomsup_fixtures.py` (+4/-2) — call-site reconciliation for the changed builder signatures.

---

## Design Principles (`general-code-change.md`)

| Principle | Verdict | Notes |
|---|---|---|
| Simplicity | PASS | Aggregation rule is straightforward: each coarser layer groups `mix_base` by its own keys. Fixture split is mechanical with no design overhead. |
| Reusability | PASS | Shared fixtures consolidated into `tests/_mix_rollups_fixtures.py` and imported by both test modules; no duplication. |
| Extensibility | PASS | Builder signatures use keyword-style parameters with defaults; the rollup-subtraction join is a stable contract. |
| Separation of concerns | PASS | Builders remain pure; `main` is the only I/O boundary. The new fixture module is data-construction only. |

## Classes vs Functions

The new helpers are pure, stateless, and signature-stable. Functions are the appropriate primitive; no class abstraction is warranted. PASS.

## File-Size Limit

All seven changed files are below 500 lines (max 343 in `src/mix_rollups.py`, max 295 in `tests/mix_bottomsup_fixtures.py`). The previously-failing `tests/test_mix_rollups.py` is now 204 lines. PASS.

## Naming

Helper names follow `snake_case`; module-private helpers are `_`-prefixed; the `__all__` list mirrors the exact set of names imported by the two test modules. PASS.

## Public API & Compatibility

The builder signature change (`mix_base` parameter added/repositioned) is internal to the package: `run_transforms` is the only in-repo caller. Tests have been updated to match. CLI surface unchanged. PASS.

## Error Handling & Logging

No new error paths. Builders fail fast on shape violations via pandas; nothing silenced. PASS.

## Comments & Docstrings (`self-explanatory-code-commenting.md`)

- Every new function has a Google-style docstring covering purpose, args, returns, and (where relevant) shape constraints.
- `tests/_mix_rollups_fixtures.py` module docstring states purpose and explicitly notes it is not itself a pytest module.
- `tests/test_mix_rollups_tieout.py` module docstring states purpose (AC8 + single-scenario regression).
- Production docstrings in `src/mix_rollups.py` and `src/_mix_rollups_helpers.py` describe the corrected aggregation rule and reference issue #20.
- No numbered notes (`NOTE 1:`, `NOTE 2:`) detected.
- Loops and comprehensions in the new code are short and either obvious or already accompanied by intent comments.

PASS.

## Determinism & Test Hygiene (`general-unit-test.md`)

- Tests are independent and use function-scope fixtures.
- No temp files, no network, no wall-clock dependence.
- Inputs are fabricated via the shared helpers (`_mix_base_fixture`, `_rate_impacts_fixture`, `_single_scenario_mix_base_fixture`).
- Assertions are behavioral (mix totals, single-scenario volume retention, NPI-minus-rollup identity); no implementation-detail coupling.
- 220 tests pass; deterministic ordering verified via `pytest-randomly`'s seed printout (no failures across the 17.23s run).

PASS.

## Suppressions

Zero `noqa`, `type: ignore`, or `pyright: ignore` markers across `src/` and `tests/`. The `__all__` declaration is an export contract, not a suppression. PASS.

## Confidentiality

No confidential aggregate values or row-level figures in any changed file. The workbook filename `LE v AOP Gross to Net Decomp.xlsx` is documented in the original issue and is the bundled command argument. PASS.

## Scope Discipline

The R4 cycle modified only the three test files identified for the split plus the existing `tests/mix_bottomsup_fixtures.py` reconciliation that landed earlier. Production code unchanged. No drive-by edits. PASS.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| N/A | N/A | N/A | No code-quality issues identified in the R4 re-review. | No action required. | All R3 PASS findings hold; the R4 split is mechanical and preserves test count and behavior. | Reviewer toolchain rerun this audit (Black/Ruff/Pyright/Pytest+coverage all exit 0; 220 passed; 100/100 coverage). |

- **Blocking findings:** 0
- **Non-Blocking findings:** 0

---

## Verdict

**PASS.** The R4 remediation is mechanically sound and preserves all R3 PASS findings. No further code-quality remediation required.
