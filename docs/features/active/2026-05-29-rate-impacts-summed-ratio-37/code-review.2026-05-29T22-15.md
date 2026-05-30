# Code Review: rate-impacts-summed-ratio (Issue #37)

**Review Date:** 2026-05-29
**Reviewer:** Claude (feature-review agent)
**Feature Folder:** `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37`
**Feature Folder Selection Rule:** Suffix `-37` matches the issue number in the branch name and the autoclose target.
**Base Branch:** `main`
**Head Branch:** `mix-calculator-wt-2026-05-29-21-48` @ `9fffb6b`
**Review Type:** Initial review

---

## Executive Summary

This change fixes a logic defect in `build_rate_impacts` (issue #37). The transform previously read carried per-unit and %GS ratio columns that `stack_pivot` had combined with `aggfunc="sum"`. Summing a ratio across a SKU's split fine-grain sub-rows is mathematically invalid: a zero-volume deduction sub-row can collapse the carried `Net Rev Per Lb - Diff` (and %GS diffs) to zero, understating the SKU's rate impact and inflating the SKU Mix residual. The fix recomputes the per-Lb and %GS AOP/LE/Diff metrics at the `{Customer, SKU #}` grain from the additive dollar/volume wide columns, then feeds the unchanged six impact formulas from those recomputed values.

**What changed:**
- `src/mix_rate_impacts.py` (+89/-20): new private `_guarded_div` helper; a recompute block for `net_rev_per_lb`, `gross_per_lb`, `oi_pct`, `trade_pct`, `non_trade_pct` (AOP/LE/Diff); the six formula expressions re-sourced to recomputed locals; `pandas` moved from a `TYPE_CHECKING` import to a runtime import and `numpy` added.
- `tests/test_mix_rate_impacts.py` (+160/-0): a zero-volume-deduction fixture plus three new tests (dollar-derived net-price impact, single-SKU rollup reconciliation, single-fine-grain behavior preservation).

The full Python toolchain was re-run during review and passes (Black, Ruff, Pyright, Pytest 7/7); changed-file coverage is 100% line.

**Top 3 risks:**
1. `_guarded_div` duplicates the `_safe_div` guard rather than sharing it; the two could drift if `_safe_div` semantics change later. Documented as an intentional scope-lock decision (Minor).
2. The reconciliation test (AC4) covers only the single-SKU group case where the rollup equality is trivially exact; a multi-SKU non-trivial reconciliation is left to the deferred integration scenario (Info).
3. The guard treats a negative denominator as zero-output (returns `0.0`), matching `_safe_div`; for these dollar/volume inputs negative `Lbs`/`Gross Sales` are not expected, so the behavior is acceptable but untested for negatives (Info).

**PR readiness recommendation:** **Go** — The change is correct, minimal, fully typed, well-commented, and covered; no blocking or major findings.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | `src/mix_rate_impacts.py` | lines 37-62 (`_guarded_div`) | `_guarded_div` is a local copy of `_mix_transforms_helpers._safe_div` rather than a shared symbol. | Acceptable under the one-production-file scope lock; consider a shared thin wrapper in a future change if a third call site appears. | Duplicated guard logic could drift from `_safe_div` if its semantics change. | Diff inspection; plan task P1-T4 documents the binary decision. |
| Info | `tests/test_mix_rate_impacts.py` | lines 251-275 | AC4 reconciliation is verified only for a single-SKU group, where the rollup equals the SKU value exactly. | Track the deferred end-to-end top-down/bottoms-up reconciliation (issue.md unchecked integration item). | Single-SKU equality is necessary but does not exercise a multi-SKU residual. | `issue.md` integration item left unchecked; test docstring states the single-SKU scope. |
| Info | `src/mix_rate_impacts.py` | lines 60-61 | Negative-denominator path (`den > 0` false for negatives) returns `0.0` but is exercised only for zero denominators. | None required; matches `_safe_div`. | Negative `Lbs`/`Gross Sales` are not expected inputs for this transform. | Test fixture uses zero, not negative, denominators. |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The recompute correctly addresses the root cause: deriving each ratio from summed dollars over summed volume at the `{Customer, SKU #}` grain is the mathematically valid operation, replacing the invalid summed-ratio read.
- The six impact formula expressions are preserved verbatim except for their inputs, so the change is auditable as input re-sourcing rather than a formula rewrite (satisfies AC1's "formulas unchanged" requirement).
- The guard semantics (`den > 0` => quotient else `0.0`) are explicitly aligned to `calc_ratios`/`_safe_div` and documented in both the helper docstring and the inline comment, satisfying AC2.
- The `np.errstate(divide="ignore", invalid="ignore")` wrapper is correct: `np.where` evaluates both branches, so the masked-out divide would otherwise emit a spurious warning. The comment explains exactly this.

#### Typing and API notes

- `_guarded_div(num: pd.Series, den: pd.Series) -> pd.Series` is fully annotated; the returned Series is constructed with `dtype="float64"` and aligned to `num.index`, which is correct and Pyright-clean.
- The public API surface is unchanged: `__all__` still exports only `RATE_IMPACT_COLUMNS` and `build_rate_impacts`. The new helper is correctly private (`_`-prefixed).
- Moving `pandas` from `TYPE_CHECKING` to a runtime import is necessary because `_guarded_div` now uses `pd.Series` at runtime; this is the correct fix rather than a workaround.

#### Error handling and logging

- The module remains a pure transform with no I/O or logging, consistent with the stated boundary (I/O in `pandas_io`/`mix_pipeline`). The zero/non-positive-denominator case is handled by returning `0.0` by design rather than raising, matching the established `calc_ratios` contract. No broad exception handling is present or needed.

---

## Test Quality Audit

The added tests are deterministic, isolated, and fast (0.50s for the module). Each builds its own in-memory DataFrame fixture with synthetic proportional values; no confidential workbook figures, no filesystem/network access, and no mocks. The zero-volume-deduction fixture is the key regression artifact: it splits one SKU across a volume-bearing sub-row and a zero-volume deduction sub-row so `stack_pivot` sums them, reproducing the defect, and asserts the recomputed dollar-derived net-price impact is non-zero.

### Reviewed test and QA artifacts

- `tests/test_mix_rate_impacts.py` — seven tests; covers filtering, all six derived columns, column presence, the zero-volume regression (AC3), single-SKU rollup reconciliation (AC4), single-fine-grain behavior preservation (AC5), and SKU enrichment. 100% line coverage of the module.
- `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/evidence/regression-testing/fail-before.2026-05-29T21-59.md` — confirms the two new regression tests fail against the pre-fix code (EXIT_CODE 1), proving the tests exercise the defect.
- `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/evidence/regression-testing/pass-after.2026-05-29T21-59.md` — confirms the same tests pass after the fix (EXIT_CODE 0).
- `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/evidence/qa-gates/coverage-delta.2026-05-29T21-59.md` — no regression on changed lines; module remains 100% line.
- `artifacts/python/lcov.info` — `SF:src\mix_rate_impacts.py`, `LF:43`, `LH:43` (100% line, 0 branches).

### Quality assessment prompts

- **Determinism:** No clock, RNG, network, or filesystem; pure DataFrame arithmetic. Deterministic.
- **Isolation:** Each test asserts one behavior with its own fixture.
- **Speed:** 0.50s for the seven-test module.
- **Diagnostics:** Tolerance asserts on named columns identify the specific failing impact and its expected value.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Only schema column names and synthetic numbers; module docstring notes values are never confidential here. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess or shell invocation in the diff. |
| Input validation at boundaries | ✅ PASS | The zero/non-positive denominator guard prevents `inf`/`NaN` propagation from invalid divisions. |
| Error handling remains explicit | ✅ PASS | Guard returns `0.0` by design; no broad catches introduced. |
| Configuration / path handling is safe | N/A | No configuration or path handling in the diff. |

---

## Research Log

No external research was required. The fix mirrors an upstream Power Query (M) correction described in `issue.md` and reuses the documented `_safe_div`/`calc_ratios` guard semantics already present in the repository.

---

## Verdict

The change is ready for normal PR flow. It is a focused, correct bugfix that recomputes ratio metrics from additive dollars/volume to eliminate the summed-ratio defect, preserves the six impact formulas, and adds targeted regression, reconciliation, and behavior-preservation tests with fail-before/pass-after evidence. Toolchain is clean and changed-file coverage is 100% line. The single Minor finding (local guard duplication) is an intentional, documented scope-lock decision and does not block merge.
