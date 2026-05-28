# Feature Audit: mix-bottoms-up-transforms (Issue #18)

**Audit Date:** 2026-05-27
**Feature Folder:** `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/`
**Base Branch:** `main` (resolved `origin/main` @ `703de5170c37dadb8189eecc01398730d5c50e8d`)
**Head Branch:** `mix-calculator-wt-2026-05-27-20-32` @ `5ad987cd0df42df534c79248e99042ec8fe33b80`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `703de5170c37dadb8189eecc01398730d5c50e8d`)
- **Head branch/commit:** `mix-calculator-wt-2026-05-27-20-32` (commit `5ad987cd0df42df534c79248e99042ec8fe33b80`)
- **Merge base:** `703de5170c37dadb8189eecc01398730d5c50e8d`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/evidence/**`
  - Coverage artifact: `artifacts/python/lcov.info`
  - Reviewer toolchain re-run: Black/Ruff/Pyright/Pytest against the six changed `.py` files
- **Feature folder used:** `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/`
- **Requirements source:** `spec.md` and `user-story.md` (full-feature)
- **Work mode resolution note:** `issue.md` carries the explicit marker `- Work Mode: full-feature`, so the authoritative AC sources are `spec.md` and `user-story.md`. `spec.md` governs if the two diverge; they are in sync (AC1–AC14 verbatim).
- **Scope note:** Full feature-vs-base audit over the entire branch diff. Python is the only language with changed source files; coverage verdicts apply to Python.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `spec.md` — primary (governs on divergence)
- `user-story.md` — secondary (reproduces AC1–AC14 verbatim)

### Acceptance criteria (AC1–AC14, from spec.md)

1. **AC1 — SKU table columns and grain.** `mix_2_sku_bottomsup` carries the 22 columns listed in Data & State, one row per `mix_0_detail` row.
2. **AC2 — SKU normal tie-out.** For a fabricated `"normal"` SKU, `SKU Mix` equals `Normal Contribution` and ties out to a hand-calculated expected value.
3. **AC3 — New Contribution branch.** A `"new distribution"` or `"new"` SKU row produces nonzero `New Contribution` (and zero Disco/Normal).
4. **AC4 — Disco Contribution branch.** A `"lost distribution"` or `"eliminated"` SKU row produces nonzero `Disco Contribution` (and zero New/Normal).
5. **AC5 — Zero-subtotal share guard.** When `Lbs Subtotal` is `0`, the `Share` columns are `0` (not `NaN`).
6. **AC6 — Classification join.** `Classification` on `mix_2_sku_bottomsup` matches the `mix_base` value for the same `(Customer, SKU #)`.
7. **AC7 — Category table columns and grain.** `mix_3_category_bottomsup` carries the columns listed in Data & State, one row per distinct `CustCatCountry`.
8. **AC8 — Category tie-out.** A fabricated normal category group ties out `SKU Mix` to a hand-calculated expected value, with `Net Rev Per Lb` derived as `Net-Revenue $ / Lbs` and Classification re-derived from aggregated Lbs.
9. **AC9 — Customer table columns and grain.** `mix_4_customer_bottomsup` carries the columns listed in Data & State, one row per distinct `CustCountry`.
10. **AC10 — Customer tie-out.** A fabricated normal customer group ties out `SKU Mix` to a hand-calculated expected value.
11. **AC11 — SKU Mix identity (property-based).** For arbitrary valid float inputs, `SKU Mix = New + Disco + Normal` holds (T2 property-test requirement).
12. **AC12 — Pipeline persistence.** The three tables appear in `sqlite_master` after an end-to-end `mix-pipeline` run on a single connection.
13. **AC13 — Confidentiality.** No confidential source data appears in any file, test, or fixture; tests use fabricated example data only.
14. **AC14 — Toolchain and limits.** Black, Ruff, Pyright, and Pytest pass with coverage thresholds (>= 85% line / >= 75% branch) met, and no production file exceeds 500 lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC1 SKU columns/grain | PASS | `_SKU_COLUMNS` (22 cols) projected by `build_mix_2_sku_bottomsup`; `test_..._columns_present` + `_row_count_matches_detail` pass | `poetry run pytest tests/test_mix_bottomsup.py` | Column list matches spec Data & State verbatim. |
| 2 | AC2 SKU normal tie-out | PASS | `test_build_mix_2_sku_bottomsup_normal_sku_mix_tieout` passes; SKU Mix == Normal Contribution, others 0 | `poetry run pytest ...` | Hand-calc tolerance 1e-9. |
| 3 | AC3 New Contribution branch | PASS | `test_..._new_contribution_active_when_new` passes (SKU-003, new distribution) | `poetry run pytest ...` | Only New active; Disco/Normal zero. |
| 4 | AC4 Disco Contribution branch | PASS | `test_..._disco_contribution_active_when_lost` passes (SKU-004, lost distribution) | `poetry run pytest ...` | Only Disco active. |
| 5 | AC5 Zero-subtotal share guard | PASS | `test_..._zero_lbs_subtotal_share_is_zero` passes; Share is 0.0, not NaN | `poetry run pytest ...` | Exercises `_safe_div` + `fillna(0)`. |
| 6 | AC6 Classification join | PASS | `test_..._classification_joined_correctly` passes; output matches mix_base per `(Customer, SKU #)` | `poetry run pytest ...` | drop_duplicates join. |
| 7 | AC7 Category columns/grain | PASS | `_CATEGORY_COLUMNS` projected; `test_..._columns_present` + `_row_count_matches_distinct_keys` pass | `poetry run pytest ...` | One row per CustCatCountry. |
| 8 | AC8 Category tie-out | PASS | `test_build_mix_3_category_bottomsup_sku_mix_tieout` passes; Net Rev Per Lb derived, Classification re-derived | `poetry run pytest ...` | Re-derives to normal. |
| 9 | AC9 Customer columns/grain | PASS | `_CUSTOMER_COLUMNS` projected; `test_..._columns_present` + `_row_count_matches_distinct_keys` pass | `poetry run pytest ...` | One row per CustCountry. |
| 10 | AC10 Customer tie-out | PASS | `test_build_mix_4_customer_bottomsup_sku_mix_tieout` passes | `poetry run pytest ...` | Hand-calc tie-out. |
| 11 | AC11 SKU Mix identity (property) | PASS | `test_build_contribution_columns_sku_mix_equals_sum` (hypothesis, 200 examples) passes | `poetry run pytest ...` | Satisfies T2 property-test-per-pure-function. |
| 12 | AC12 Pipeline persistence | PASS | `_DERIVED_TABLES` extended; `test_mix_pipeline_end_to_end` asserts all three tables in `sqlite_master` | `poetry run pytest tests/test_mix_pipeline.py` | Single in-memory connection. |
| 13 | AC13 Confidentiality | PASS | Diff scan: only the workbook *filename* (schema) appears in docs/evidence; no data values. Workbook gitignored and absent from diff. `confidentiality-review.2026-05-27T20-52.md` | `git diff <base>..<head> \| grep -iE 'LE v AOP\|Gross to Net Decomp'`; `git check-ignore`; `git ls-files --error-unmatch` | Fabricated data only (SKU-001.., Widget, Category X/Y, Acme Foods, US/Canada). |
| 14 | AC14 Toolchain and limits | PASS | Black exit 0, Ruff exit 0, Pyright 0 errors, Pytest 23 pass; coverage 100% line/branch on new modules; all files < 500 lines | see Appendix B of policy-audit | Reviewer re-run reproduced clean pass. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 14 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Optional: add a non-fatal data-quality warning at the SKU builder boundary for the single-country-per-(Customer,Category) expectation (spec permits it; must emit no confidential values).
2. None required for merge.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All 14 criteria evaluate to PASS.
- The criteria were already checked off `[x]` in both authoritative source files (`spec.md` and `user-story.md`) by the executor at delivery time; the reviewer verified each independently and confirms the checked state is accurate. No checkbox change was required.

### AC Status Summary

- Source: `spec.md` and `user-story.md`
- Total AC items: 14 (each file)
- Checked off (delivered): 14 (each file)
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 14 | 14 | 0 | Checkbox-backed; authoritative; all verified PASS, already checked. |
| `user-story.md` | 14 | 14 | 0 | Checkbox-backed; reproduces spec AC1–AC14 verbatim; already checked. |

No source-file checkbox change was made because all 14 criteria were already checked `[x]` and the reviewer independently confirmed each evaluates to PASS.
