# Feature Audit: mix-category-customer-mix-tieout (#20)

**Audit Date:** 2026-05-27
**Feature Folder:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`
**Base Branch:** `main` (commit `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`)
**Head Branch:** `fix/mix-category-customer-mix-tieout-20` (commit `98399b6b61efae4eb4fa9784925a8975dcb356ca`)
**Work Mode:** `full-bug`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`)
- **Head branch/commit:** `fix/mix-category-customer-mix-tieout-20` (commit `98399b6b61efae4eb4fa9784925a8975dcb356ca`)
- **Merge base:** `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` (refreshed 2026-05-27T22-33)
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/**`
  - Additional evidence: reviewer-reproduced Python toolchain run and end-to-end pipeline run on 2026-05-27T22-34
- **Feature folder used:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`
- **Requirements source:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/spec.md` (`## Acceptance Criteria` section, AC1-AC9)
- **Work mode resolution note:** `issue.md` carries the explicit marker `- Work Mode: full-bug`. For `full-bug` the acceptance-criteria source is `spec.md` only; `user-story.md` is not consulted.
- **Scope note:** The audit covers the full branch diff against `main` (`b0e048f..98399b6`). No caller instruction attempted to narrow the scope, and none was accepted. All five changed source/test files (Python only) were reviewed; documentation, evidence, and agent-memory changes were reviewed for completeness and confidentiality.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/spec.md` — only source (work mode `full-bug`)

### Acceptance criteria

1. **AC1:** `build_mix_2_category`, `build_mix_3_customer`, and `build_mix_4_country` aggregate volume/revenue from the unfiltered `mix_base` at their own granularity (not from the prior filtered layer); the builders remain pure (I/O-free) and within the 500-line file limit.
2. **AC2:** The rollup-subtraction contract is preserved — each layer's mix column equals its recomputed `Calc Net Price Impact` minus the sum of the prior finer layer's `Calc Net Price Impact`.
3. **AC3:** `mix_1_sku["SKU Mix"]` is unchanged (no regression on the SKU layer); the `mix_3_customer["Customer Mix"]` column name and the `mix_4_country` single-row shape are preserved.
4. **AC4:** Deterministic Pytest unit tests with fabricated inputs prove that a single-scenario line (zero AOP Lbs / nonzero LE Lbs, and the reverse) is retained in the coarser-layer aggregates — i.e. the volume-loss regression is covered — and that each layer's recomputed NPI and mix follow the full-aggregation-minus-rollup identity. No temp files, no network.
5. **AC5:** Changed-code line coverage >= 85% and branch coverage >= 75%; no coverage regression on changed lines.
6. **AC6:** The Python toolchain passes in one clean pass (Black, Ruff, Pyright, Pytest).
7. **AC7:** End-to-end: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db` writes the mix tables and the appended `nrr_summary` table, and the `nrr_summary` internal `Check` resolves to `"CHECK"`. Evidence recorded without exposing confidential source values.
8. **AC8:** Each of `mix_2_category["Category Mix"]`, `mix_3_customer["Customer Mix"]`, `mix_1_sku["SKU Mix"]`, and `mix_4_country["Country Mix"]` column totals ties out to the corresponding workbook TopDown table total (verified during the end-to-end check; pass/fail recorded without disclosing the figures).
9. **AC9:** `README.md` / docstrings updated only as needed to reflect the corrected layer-aggregation description; no unintended behavior changes outside scope.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Coarser builders aggregate from unfiltered `mix_base`; pure; under 500 lines | PASS | `src/mix_rollups.py` lines 113-138 (category), 155-188 (customer), 203-236 (country) all call `build_mix_stage(mix_base, [...])`. No I/O. File sizes: `mix_rollups.py` 343, `_mix_rollups_helpers.py` 182, `mix_pipeline_run.py` 137 lines — all under 500. | `wc -l src/mix_rollups.py src/_mix_rollups_helpers.py src/mix_pipeline_run.py` | The AC scopes the 500-line check to the builders' source files; test-file size is governed by the general code-change policy, evaluated separately in the policy audit. |
| 2 | Mix column = recomputed NPI - prior-layer NPI sum | PASS | `tests/test_mix_rollups.py::test_layer_mix_equals_full_aggregation_minus_rollup` independently recomputes the expected category and customer NPIs from the unfiltered `mix_base` and asserts row-by-row that `Category Mix == layer NPI - rollup-2 NPI` and `Customer Mix == layer NPI - rollup-3 NPI`. `join_rollup_mix` enforces this contract structurally. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rollups.py::test_layer_mix_equals_full_aggregation_minus_rollup` | Test passes under reviewer rerun. |
| 3 | SKU layer unchanged; customer column name and country single-row shape preserved | PASS | `build_mix_1_sku` source (lines 76-97) is unchanged from baseline (verified via `git diff`). `build_mix_3_customer` continues to emit the `Customer Mix` column (lines 183-188, joined via `"Customer Mix"`). `build_mix_4_country` collapses to a single all-rows group via the `_all` synthetic key, then drops it (lines 228-236); the country DataFrame is single-row. End-to-end run confirms `mix_4_country: 1 rows`. | `git diff b0e048f..98399b6 -- src/mix_rollups.py`; reviewer e2e run | Single-row shape independently confirmed by the reviewer e2e run row counts. |
| 4 | Deterministic tests prove single-scenario retention and the NPI-minus-rollup identity | PASS | `tests/test_mix_rollups.py::test_category_layer_retains_single_scenario_volume` and `::test_customer_layer_retains_single_scenario_volume` build `_single_scenario_mix_base_fixture` with a new-in-LE SKU (zero AOP Lbs / nonzero LE Lbs) and a dropped-in-LE SKU (nonzero AOP Lbs / zero LE Lbs), then assert the coarser-layer `Lbs - LE` matches the directly computed unfiltered `mix_base` group sum. `::test_layer_mix_equals_full_aggregation_minus_rollup` covers the identity. All fixtures are in-memory; no temp files; no network. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rollups.py -q` | All three regression tests pass under reviewer rerun. |
| 5 | Changed-code line coverage >= 85% and branch >= 75%; no regression | PASS | Reviewer-rerun coverage: `src/mix_rollups.py` 59/59 stmts, 0/0 branch missed = 100%/100%; `src/_mix_rollups_helpers.py` 30/30, 0/0 = 100%/100%; `src/mix_pipeline_run.py` 26/26, 0/0 = 100%. Baseline was 100%/100%; no regression. Coverage delta evidence: `evidence/qa-gates/coverage-delta.2026-05-27T22-19.md`. | `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing` | Above the 85%/75% uniform threshold in `.claude/rules/quality-tiers.md` and `.claude/rules/general-unit-test.md`. |
| 6 | Python toolchain passes in one clean pass | PASS | Reviewer rerun (single pass, no auto-fixes): Black `5 files would be left unchanged` (exit 0); Ruff `All checks passed!` (exit 0); Pyright `0 errors, 0 warnings, 0 informations` (exit 0); Pytest `220 passed in 20.48s` (exit 0). | `env -u VIRTUAL_ENV poetry run black --check ...`, `... ruff check ...`, `... pyright ...`, `... pytest --cov ...` | Toolchain itself is clean; the file-size policy violation on `tests/test_mix_rollups.py` is enforced by `general-code-change.md` rather than by Black/Ruff/Pyright/Pytest and is recorded separately in the policy audit. |
| 7 | End-to-end pipeline emits all tables and `nrr_summary` `Check` resolves to `"CHECK"` | PASS | Reviewer rerun produced `mix_review.db` with all expected tables (mix_1_sku, mix_2_category, mix_3_customer, mix_4_country, nrr_summary, plus rollups, detail, BottomsUp, and Q1). A scan of every string cell in `nrr_summary` for the reconciliation token returned `['CHECK']` only (no `ERROR` present). Original executor evidence: `evidence/regression-testing/e2e-run.2026-05-27T22-27.md` and `nrr-check.2026-05-27T22-27.md`. | `env -u VIRTUAL_ENV poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix_review.db` followed by a `SELECT` over `nrr_summary` for `CHECK`/`ERROR` tokens | The reviewer's throwaway probe script was deleted after use. No confidential figures were printed or persisted. |
| 8 | All four mix-layer column totals tie out to workbook TopDown totals | PASS | Executor evidence in `evidence/regression-testing/tieout.2026-05-27T22-27.md` reports PASS for all four layers using a documented per-layer mapping (including the AC8 mapping from `mix_3_customer["Customer Mix"]` to the workbook's mislabeled "Category Mix" column per issue #9). The `nrr_summary` `Check` resolving to `CHECK` (AC7, reviewer-reproduced) is an independent corroboration: that workbook-defined check resolves to `ERROR` if any of the four layers fails to tie out. | Executor `tieout.2026-05-27T22-27.md`; reviewer NRR `Check` confirmation | The reviewer attempted an independent column-sum probe against the workbook. The probe's naive header-column-sum methodology produced a false `FAIL` on the out-of-scope, known-good SKU layer (which was already tied out before this branch), confirming the probe was non-authoritative rather than evidence of regression. The executor's documented per-layer extraction is the authoritative source; the reviewer-reproduced NRR `CHECK` corroborates it indirectly. |
| 9 | README/docstrings updated only as needed; no out-of-scope behavior changes | PASS | Module docstrings in `src/mix_rollups.py` and `src/_mix_rollups_helpers.py` updated to describe the unfiltered-`mix_base` sourcing decision and the issue #20 motivation. `src/mix_pipeline_run.py` docstring updated in the rollup-chain comment block. No `README.md` change in the diff. Diff inspection found no out-of-scope behavior changes: `mix_1_sku` is byte-identical to baseline; output schemas are unchanged; only the previously-incorrect category/customer mix values change. | `git diff --stat b0e048f..98399b6`; `git diff b0e048f..98399b6 -- README.md` | README was not modified, which is consistent with "only as needed". |

---

## Summary

**Overall Feature Readiness:** NEEDS REVISION

**Criteria summary:**
- **PASS:** 9 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

All nine acceptance criteria pass. Feature readiness is NEEDS REVISION (not PASS) because of a separate general-code-change policy violation outside the AC set: `tests/test_mix_rollups.py` is 562 lines and exceeds the 500-line file-size limit. The acceptance-criteria contract itself is met; the readiness gate is held by the general-policy violation.

**Top gaps preventing PASS:**

1. General code-change policy violation: `tests/test_mix_rollups.py` 562 lines (over 500-line limit). Split into a sibling test module before merge.

**Recommended follow-up verification steps:**

1. After splitting `tests/test_mix_rollups.py`, re-run Black, Ruff, Pyright, and Pytest with branch coverage to confirm no regression.
2. Re-validate this feature audit after the split to upgrade overall readiness to PASS.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- Criteria evaluated as **PASS** may be checked off in the authoritative source file(s) if they are represented as markdown checkboxes and are not already checked.
- Criteria evaluated as **PARTIAL**, **FAIL**, or **UNVERIFIED** must remain unchecked.
- If the source uses prose or numbered requirements instead of checkbox items, do not rewrite the source file; record status only in this audit.

All nine acceptance criteria in `spec.md` were already checked off as `[x]` by the executor before review. The reviewer evaluated each against actual evidence and confirms all nine evaluate to PASS, so the existing checkbox state in `spec.md` is correct and no source-file change is required. The reviewer did not modify `spec.md` because no PARTIAL/FAIL/UNVERIFIED criterion required unchecking.

### AC Status Summary

- Source: `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/spec.md`
- Total AC items: 9
- Checked off (delivered): 9
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/spec.md` | 9 | 9 | 0 | Checkbox-backed; all nine already `[x]` by executor and confirmed PASS by reviewer. |
