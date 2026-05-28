# Code Review: nrr-summary-mix-pipeline (Issue #15)

**Review Date:** 2026-05-27
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15`
**Feature Folder Selection Rule:** Active folder whose suffix (`-15`) matches the issue number in the branch name `feature/nrr-summary-mix-pipeline-15`.
**Base Branch:** `main` (merge-base `703de5170c37dadb8189eecc01398730d5c50e8d`)
**Head Branch:** `feature/nrr-summary-mix-pipeline-15` (`7f47625ef6a508f99541e0274e0068c1dd871eb6`)
**Review Type:** Initial review

---

## Executive Summary

This change appends a pure summary builder for the workbook's `NRR_Summary` tab to the existing issue #9 mix-decomposition pipeline. It adds `src/mix_nrr_summary.py` (block composition) and `src/_mix_nrr_summary_helpers.py` (scalar/row helpers), wires the builder into the transform runner `src/mix_pipeline_run.py`, and relies on the unchanged `src/mix_pipeline.py` persistence path through `src/pandas_io.py`. The builder reads six existing frames (`aop_vs_le`, `rate_impacts`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`, `mix_4_country`) and emits a tidy long table with one row per source-tab label. The change is additive, self-contained, and does not modify upstream decomposition math.

**What changed:**
- `src/mix_nrr_summary.py` (NEW, 439 lines): five block builders (`_attribute_summary_rows`, `_per_lb_row`, `_realization_rows`, `_net_pricing_rows`, `_mix_rows`, `_reconciliation_rows`) composed by `build_nrr_summary`.
- `src/_mix_nrr_summary_helpers.py` (NEW, 236 lines): `safe_ratio`, `column_sum`, `attribute_totals`, `Measure` dataclass, `row` factory, `all_in_ts`, `ts_basis_points`, `sum_optional`, `reconciles`.
- `src/mix_pipeline_run.py` (MODIFIED, +16/-1): builds `nrr_summary` as the final derived table and adds it to the returned dict.
- `src/mix_pipeline.py` (MODIFIED, +5/-4): docstring/comment updates; persistence path unchanged.
- `tests/test_mix_nrr_summary.py` (NEW, 453 lines): 14 deterministic unit tests with fabricated inputs.
- `quality-tiers.yml`, `README.md`: classification and documentation.

**Top 3 risks:**
1. The end-to-end `Check` resolves to `"ERROR"` on real data. This is verified to be a faithful surfacing of a pre-existing upstream issue #9 defect (tracked as issue #20), not a defect in this feature; the realization Price/Mix, pricing block, and SKU/Country mix totals all tie out while `mix_2_category` / `mix_3_customer` column totals do not.
2. The deliberate `mix_3_customer["Customer Mix"]` column mapping is load-bearing; if a future upstream rename reverts the column header, the builder raises `KeyError`. This is intentional fail-fast and is pinned by a test.
3. The pinned single-field `check` representation (result only in `check`, `value`/`pct` stay `None`) is a planner-selected convention; downstream consumers must read the `check` column, not `value`/`pct`, for the reconciliation result. Documented in the module docstring and README.

**PR readiness recommendation:** **Go** — The implementation is clean, fully typed, fully covered, and policy-compliant; the `Check == "ERROR"` is the correct, documented outcome under the recorded Option A decision.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/mix_nrr_summary.py` | `build_nrr_summary` line 406 | `import pandas as pd` is a function-local import (pandas is otherwise `TYPE_CHECKING`-only). | None required. | Keeps module import light and avoids a hard top-level pandas import while the rest of the module is type-only; consistent with sibling transforms. | Inspected `src/mix_nrr_summary.py:40-57,406`. |
| Info | `README.md` | line 153 | README "Coverage policy" line still reads ">= 80% repo / >= 90% new modules", which predates the uniform >= 85% line / >= 75% branch policy in `.claude/rules/quality-tiers.md`. | Optionally align the README wording in a future docs pass. Not blocking and not introduced by this feature. | README is documentation, not a policy source; the authoritative thresholds in `quality-tiers.md` govern. Actual coverage (100%) exceeds both. | Inspected `README.md:153`; `.claude/rules/quality-tiers.md`. |
| Info | `src/mix_nrr_summary.py` | `_mix_rows` line 305 | The `Customer Mix` column read is the deliberate Excel-to-pipeline rename mapping. | None required. | Correctly documented in code and pinned by `test_customer_mix_requires_customer_mix_column`; satisfies AC5. | Inspected `src/mix_nrr_summary.py:300-306`; `tests/test_mix_nrr_summary.py:245-266`. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The builder is genuinely pure: pandas is imported under `TYPE_CHECKING` plus one function-local import; there are no disk, DB, or network reads. Persistence and orchestration stay outside the transform, satisfying the separation-of-concerns principle.
- The 500-line constraint is respected by splitting scalar/row helpers into `_mix_nrr_summary_helpers.py` (236 lines) and keeping block assembly in `mix_nrr_summary.py` (439 lines). The split is cohesive rather than arbitrary.
- The three core SUMIF measures (`Lbs`, `Gross Sales`, `Net-Revenue $`) are computed once via the `Measure` dataclass and reused by both the attribute block and the realization block, avoiding recomputation.
- Zero-denominator handling is explicit and uniform: `safe_ratio` returns `None` on a zero divisor, and downstream rows propagate `None` rather than raising, which keeps the summary buildable on empty/fabricated inputs while the real data never hits the branch.
- The reconciliation `Check` is computed independently for the NR$ and %NR comparisons and requires both to reconcile, faithfully matching the source-tab criterion.

#### Typing and API notes

- All functions and the `Measure` dataclass carry complete type hints; `from __future__ import annotations` is used and `Any` does not appear. Pyright reports 0 errors on the changed files.
- Public surface is minimal and explicit: `__all__` exports `build_nrr_summary` and `NRR_SUMMARY_COLUMNS`; block helpers are `_`-prefixed; scalar helpers live in the `_`-prefixed helpers module with their own `__all__`.
- `Measure` is `@dataclass(frozen=True)` with a derived `pct` property — an appropriate value-object choice.
- No `# noqa`, `# type: ignore`, or `# pyright: ignore` suppressions appear in any changed file.

#### Error handling and logging

- Fail-fast is correct: a missing renamed column surfaces a natural `KeyError` (pinned by test), and zero denominators return `None` by documented design rather than silently producing misleading numbers.
- The pure modules do no logging or printing. The CLI `_print_summary` retains intentional `print` for operator stdout (documented as CLI output, not logging) and is otherwise unchanged.

---

## Test Quality Audit

The test module exercises each of the five blocks with fabricated, hand-computable inputs and asserts against independently derived expected values (for example, `Net Rev / Lb` AOP = 100/10 = 10). Edge coverage includes zero Lbs totals, zero Gross-Sales totals, zero Net-Revenue AOP, empty mix frames, the `Check == "ERROR"` divergence path, and the missing-`Customer Mix`-column `KeyError`. The pinned single-field `check` representation is asserted (`value`/`pct` remain empty on the `Check` row; all non-Check rows have an empty `check` cell).

### Reviewed test and QA artifacts

- `tests/test_mix_nrr_summary.py` — 14 deterministic unit tests; fabricated inputs only; AAA structure; no temp files or network. Verified passing (14 passed in 0.42s) this review.
- `evidence/qa-gates/pytest-final.2026-05-27T21-01.md` — full suite 199 passed; 100% line / 100% branch; new modules 100%/100%.
- `evidence/qa-gates/coverage-delta.2026-05-27T21-01.md` — baseline-vs-post-change comparison; no regression on changed lines.
- `evidence/other/e2e-run.2026-05-27T21-08.md` — end-to-end run (exit 0); `nrr_summary` written as the final table with 20 rows; `Check == "ERROR"` with a non-confidential root-cause diagnosis.
- `artifacts/python/lcov.info` — inspected directly: `mix_nrr_summary.py` LF/LH 82/82, BRF/BRH 8/8; helpers LF/LH 41/41, BRF/BRH 10/10.

### Quality assessment prompts

- **Determinism:** Inputs are hard-coded pandas frames; no clock, RNG, network, or filesystem dependency.
- **Isolation:** Each test targets a single block or edge; fixtures are per-test, no shared mutable state.
- **Speed:** 0.42s for the module; full suite 16.54s per the QA evidence.
- **Diagnostics:** Tight numeric tolerances and an explicit `AssertionError` message on the negative-path test make failures actionable.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No source numeric values, SKU descriptions, or category names in tracked files. Fabricated identifiers only (e.g. `SKU-001`, `Acme Foods`). Source workbooks and `mix.db` are gitignored; no `.xlsx`/`.db`/`.csv` tracked. The agent-memory dossier describes the upstream discrepancy qualitatively without disclosing magnitudes. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess or shell invocation in the changed code. |
| Input validation at boundaries | ✅ PASS | The builder is pure and reads frames produced by the validated upstream pipeline; the missing-column case fails fast with `KeyError`. |
| Error handling remains explicit | ✅ PASS | Explicit zero-denominator guards; no broad `except`. |
| Configuration / path handling is safe | ✅ PASS | No new path or config handling; the builder takes only in-memory frames. |
| Correctness of reconciliation | ✅ PASS | `Check` independently verified `"ERROR"` against the persisted `nrr_summary` table in `artifacts/mix.db` (20 rows, five sections, source-order metrics ending with `Check`). The result correctly surfaces upstream issue #20. |

---

## Research Log

No external research was required. All findings are grounded in the branch diff, the re-run toolchain output, the feature-folder evidence artifacts, the lcov coverage artifact, and direct inspection of the persisted `nrr_summary` table.

---

## Verdict

The change is ready for normal PR flow. The implementation is simple, fully typed, fully covered (100% line and branch on both new files), and compliant with the cross-language, Python, unit-test, and commenting policies. There are no Blocker or Major findings; the three Info items are observations, not defects. The end-to-end `Check == "ERROR"` is the correct and honest outcome under the recorded Option A decision — it faithfully surfaces a pre-existing upstream issue #9 mix tie-out defect that is tracked separately as issue #20 and is out of scope for this additive-summary feature. PR readiness: **Go**.
