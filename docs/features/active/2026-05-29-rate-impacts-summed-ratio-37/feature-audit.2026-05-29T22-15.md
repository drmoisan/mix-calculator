# Feature Audit: rate-impacts-summed-ratio (Issue #37)

**Audit Date:** 2026-05-29
**Feature Folder:** `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37`
**Base Branch:** `main`
**Head Branch:** `mix-calculator-wt-2026-05-29-21-48`
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (merge-base commit `ae52c3f48f6233a91b6613ceb1c390c291a0a6db`)
- **Head branch/commit:** `mix-calculator-wt-2026-05-29-21-48` (commit `9fffb6b82366407dae6207faaae15ee28ff1447d`)
- **Merge base:** `ae52c3f48f6233a91b6613ceb1c390c291a0a6db`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/evidence/**`
  - Additional evidence: `artifacts/python/lcov.info`; independent re-run of Black/Ruff/Pyright/Pytest during this review
- **Feature folder used:** `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37`
- **Requirements source:** `issue.md` (`## Acceptance Criteria`, AC1–AC6)
- **Work mode resolution note:** `issue.md` carries the explicit marker `- Work Mode: minor-audit`. Per the work-mode contract, the only authoritative AC source is the `## Acceptance Criteria` section in `issue.md`. No `spec.md` or `user-story.md` exists in the feature folder, consistent with minor-audit.
- **Scope note:** Audit scope is the full branch diff `ae52c3f..9fffb6b` against `main`. Changed source files: `src/mix_rate_impacts.py` and `tests/test_mix_rate_impacts.py` (Python only). No scope narrowing was accepted.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/issue.md` — only source (minor-audit)

### Acceptance criteria

1. AC1 — `build_rate_impacts` computes `net_rev_per_lb` (AOP and LE), `gross_sales_per_lb`, `OI %GS`, `Trade %GS`, and `Non-Trade %GS` from the additive dollar/volume wide columns at the `{Customer, SKU #}` grain rather than reading the carried/summed ratio columns. The six impact formulas (`RATE_IMPACT_COLUMNS`) are unchanged.
2. AC2 — A zero-denominator guard consistent with `calc_ratios` is applied so a zero (or non-positive) denominator yields 0 rather than `inf`/`NaN`.
3. AC3 — Regression test (synthetic proportional values only; no confidential workbook figures): for a SKU whose net-revenue change originates from a zero-volume deduction sub-row, `Net Rev Per Lb - Diff`/`Calc Net Price Impact` is the dollar-derived value (non-zero), not zero.
4. AC4 — Reconciliation test: the SKU-level `Calc Net Price Impact` summed to the Customer x Category grain equals the category-level net-price impact for a single-SKU group (SKU Mix nets to 0).
5. AC5 — Behavior is unchanged for SKUs with a single fine-grain row (recomputed ratio equals the previously carried ratio); existing `build_rate_impacts` tests continue to pass.
6. AC6 — Python toolchain passes (Black, Ruff, Pyright, Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Metrics recomputed from additive dollar/volume columns; six formulas unchanged | PASS | `src/mix_rate_impacts.py` lines 144-164 recompute `net_rev_per_lb_*`, `gross_per_lb_*`, `oi_pct_*`, `trade_pct_*`, `non_trade_pct_*` from `Net-Revenue $`/`Lbs`/`Gross Sales`/`Off Invoice $`/`Trade Spend $`/`Non-Trade $` per scenario; lines 170-181 feed the six formulas from these locals; the carried `... - Diff`/`%GS - AOP` columns are no longer read. | `git diff ae52c3f..9fffb6b -- src/mix_rate_impacts.py` | `RATE_IMPACT_COLUMNS` list and formula arithmetic unchanged. |
| 2 | Zero/non-positive denominator guard consistent with `calc_ratios` | PASS | `_guarded_div` (lines 37-62) returns `np.where(denominator > 0, num/den, 0.0)`; docstring states `den > 0` semantics matching `_safe_div`/`CalcRatios`. | Diff inspection; `test_zero_volume_deduction_yields_dollar_derived_net_price_impact` | Negative denominators also map to `0.0` (matches `_safe_div`). |
| 3 | Regression test: zero-volume deduction yields dollar-derived non-zero net-price impact | PASS | `test_zero_volume_deduction_yields_dollar_derived_net_price_impact` asserts `Calc Net Price Impact != 0.0` and `== 2.0 * 10.0`; fixture uses synthetic proportional values only. Fail-before evidence (EXIT_CODE 1) and pass-after (EXIT_CODE 0). | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py::test_zero_volume_deduction_yields_dollar_derived_net_price_impact` | `evidence/regression-testing/fail-before.*`, `pass-after.*`. |
| 4 | Reconciliation: SKU-level rolls up to category net-price impact (SKU Mix = 0) for single-SKU group | PASS | `test_single_sku_group_rolls_up_to_category_net_price_impact` groups by `{Customer, Category}` and asserts `category - sku < 1e-9`. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py::test_single_sku_group_rolls_up_to_category_net_price_impact` | Single-SKU equality is exact; multi-SKU end-to-end reconciliation is a deferred integration item (noted in code review). |
| 5 | Single-fine-grain behavior unchanged; existing tests pass | PASS | `test_single_fine_grain_recompute_equals_carried_ratio` asserts recomputed impacts equal the carried-ratio hand-computed values; the three pre-existing tests (`filters_non_normal_rows`, `derived_columns_match_hand_computed`, `includes_all_six_impact_columns`, `enriches_with_sku_lookup`) continue to pass. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rate_impacts.py -q` | 7/7 module tests pass. |
| 6 | Python toolchain passes with coverage thresholds and no regression on changed lines | PASS | Black (no changes), Ruff (all checks passed), Pyright (0 errors/0 warnings), Pytest (510 suite / 7 module pass). Changed file 100% line (lcov `LF:43`/`LH:43`); repo-wide 99% line / ~98.9% branch; no regression on changed lines. | `black --check`; `ruff check`; `pyright src/mix_rate_impacts.py`; `pytest --cov --cov-branch` | Re-run independently during review; matches `evidence/qa-gates/*`. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 6 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Track the deferred end-to-end top-down/bottoms-up reconciliation integration scenario (unchecked in `issue.md` under Proposed Fix / Validation Ideas), exercising a multi-SKU group where the SKU Mix residual is non-trivial.
2. Confirm CI green run on the PR once opened (no workflow files changed, so the `modified-workflow-needs-green-run` rule did not fire).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** may be checked off in the authoritative source file(s) if they are represented as markdown checkboxes and are not already checked.
- Criteria evaluated as **PARTIAL**, **FAIL**, or **UNVERIFIED** must remain unchecked.
- If the source uses prose or numbered requirements instead of checkbox items, do not rewrite the source file; record status only in this audit.

All six acceptance criteria in `issue.md` were already marked `[x]` by the executor when the work was verified. This audit confirms each criterion as PASS based on independently inspected evidence; no checkbox change was required because all items were already correctly checked.

### AC Status Summary

- Source: `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/issue.md`
- Total AC items: 6
- Checked off (delivered): 6
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-29-rate-impacts-summed-ratio-37/issue.md` | 6 | 6 | 0 | Checkbox-backed; all already `[x]` and confirmed PASS by this audit. |
