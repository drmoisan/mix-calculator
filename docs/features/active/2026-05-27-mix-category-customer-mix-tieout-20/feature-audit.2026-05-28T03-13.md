# Feature Audit: mix-category-customer-mix-tieout (#20) — R4 Re-audit

**Audit Date:** 2026-05-28
**Audit Type:** Remediation pass 1 (R4) re-audit after test-module split
**Feature Folder:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`
**Base Branch:** `main` (commit `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`)
**Head Branch:** `fix/mix-category-customer-mix-tieout-20` (commit `528dcbc37a0422cced21b70c61e0ce34ec1a120f`)
**Work Mode:** `full-bug`

---

## Summary

All nine acceptance criteria (AC1-AC9) from `spec.md` remain satisfied after the R4 remediation that split `tests/test_mix_rollups.py` (562 -> 204 lines) into three cohesive modules: `tests/_mix_rollups_fixtures.py` (225 lines), `tests/test_mix_rollups.py` (204 lines), and `tests/test_mix_rollups_tieout.py` (167 lines). No test was added, removed, renamed, deselected, or skipped; production code is unchanged from R3. The Python toolchain passes cleanly (Black, Ruff, Pyright, Pytest 220/220) with 100% line and 100% branch coverage on the three changed source files and repo-wide. Branch is acceptance-ready.

**Verdict: PASS.** 0 Blocking findings, 0 Non-Blocking findings.

---

## Scope and Baseline

- **Base branch:** `main` (commit `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`)
- **Head branch/commit:** `fix/mix-category-customer-mix-tieout-20` (commit `528dcbc37a0422cced21b70c61e0ce34ec1a120f`)
- **Merge base:** `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` (refreshed for the R4 pass)
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/**`
  - Additional evidence: reviewer-reproduced Python toolchain run on 2026-05-28T03-13
- **Feature folder used:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`
- **Requirements source:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/spec.md` (`## Acceptance Criteria` section, AC1-AC9)
- **Work mode resolution note:** `issue.md` carries the explicit marker `- Work Mode: full-bug`. For `full-bug` the acceptance-criteria source is `spec.md` only; `user-story.md` is not consulted.
- **Scope note:** The audit covers the full branch diff against `main` (`b0e048f..528dcbc`). No caller instruction attempted to narrow scope, and none was accepted. All seven changed source/test files (Python only) were reviewed; documentation, evidence, and agent-memory changes were reviewed for completeness and confidentiality.

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
| 1 | Coarser builders aggregate from unfiltered `mix_base`; pure; under 500 lines | PASS | `src/mix_rollups.py` `build_mix_2_category`/`build_mix_3_customer`/`build_mix_4_country` call `build_mix_stage(mix_base, [...])`. No I/O. File sizes: `mix_rollups.py` 343, `_mix_rollups_helpers.py` 182, `mix_pipeline_run.py` 137 — all under 500. | `pwsh -NoProfile -Command "(Get-Content <path>).Count"` | The AC scopes the 500-line check to the builders' source files; test-file size is governed by the general code-change policy, evaluated separately in the policy audit and now also PASSing for every changed file after the R4 split. |
| 2 | Mix column = recomputed NPI - prior-layer NPI sum | PASS | `tests/test_mix_rollups_tieout.py::test_layer_mix_equals_full_aggregation_minus_rollup` independently recomputes the expected category and customer NPIs from the unfiltered `mix_base` and asserts row-by-row that `Category Mix == layer NPI - rollup-2 NPI` and `Customer Mix == layer NPI - rollup-3 NPI`. `join_rollup_mix` enforces this contract structurally. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rollups_tieout.py::test_layer_mix_equals_full_aggregation_minus_rollup` | Test passes under reviewer rerun. |
| 3 | SKU layer unchanged; customer column name and country single-row shape preserved | PASS | `build_mix_1_sku` source is unchanged from baseline (verified via `git diff`). `build_mix_3_customer` continues to emit the `Customer Mix` column; `build_mix_4_country` collapses to a single all-rows group via the `_all` synthetic key, then drops it. End-to-end run confirms `mix_4_country: 1 rows`. | `git diff b0e048f..528dcbc -- src/mix_rollups.py`; executor e2e run | Single-row shape independently confirmed by the executor e2e run row counts. |
| 4 | Deterministic tests prove single-scenario retention and the NPI-minus-rollup identity | PASS | `tests/test_mix_rollups_tieout.py::test_category_layer_retains_single_scenario_volume` and `::test_customer_layer_retains_single_scenario_volume` build `_single_scenario_mix_base_fixture` with a new-in-LE SKU (zero AOP Lbs / nonzero LE Lbs) and a dropped-in-LE SKU (nonzero AOP Lbs / zero LE Lbs), then assert the coarser-layer `Lbs - LE` matches the directly computed unfiltered `mix_base` group sum. `::test_layer_mix_equals_full_aggregation_minus_rollup` covers the identity. All fixtures are in-memory; no temp files; no network. | `env -u VIRTUAL_ENV poetry run pytest tests/test_mix_rollups_tieout.py -v` | All three regression tests pass under reviewer rerun; the post-split AC8 evidence (`evidence/regression-testing/ac8-tieout-postsplit.2026-05-27T22-40.md`) confirms parity. |
| 5 | Changed-code line coverage >= 85% and branch >= 75%; no regression | PASS | Reviewer-rerun coverage: `src/mix_rollups.py` 59/59 stmts, 0/0 branch missed = 100%/100%; `src/_mix_rollups_helpers.py` 30/30, 0/0 = 100%/100%; `src/mix_pipeline_run.py` 26/26, 0/0 = 100%. Baseline was 100%/100%; no regression. | `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term` | Above the 85%/75% uniform threshold in `.claude/rules/quality-tiers.md`. |
| 6 | Python toolchain passes in one clean pass | PASS | Reviewer rerun (single pass, no auto-fixes, this audit): Black `46 files would be left unchanged.` (exit 0); Ruff `All checks passed!` (exit 0); Pyright `0 errors, 0 warnings, 0 informations` (exit 0); Pytest `220 passed in 17.23s` (exit 0). | `env -u VIRTUAL_ENV poetry run black --check .` ; `... ruff check .` ; `... pyright` ; `... pytest --cov=src --cov-branch --cov-report=term` | Single clean pass confirmed; no R4 cycle iteration needed. |
| 7 | End-to-end pipeline emits all tables and `nrr_summary` `Check` resolves to `"CHECK"` | PASS | Executor evidence: `evidence/regression-testing/e2e-run.2026-05-27T22-27.md` (exit 0; all expected tables written) and `evidence/regression-testing/nrr-check.2026-05-27T22-27.md` (`Check = CHECK`). No confidential figures disclosed. | Reviewer queries against the executor's `artifacts/mix.db`; original executor evidence cross-referenced. | Reviewer did not re-execute the end-to-end run during R4 (the only R4 change was test-file split; production code unchanged from R3 PASS). |
| 8 | All four mix-layer column totals tie out to workbook TopDown totals | PASS | Executor evidence in `evidence/regression-testing/tieout.2026-05-27T22-27.md` reports PASS for all four layers; corroborated by `evidence/regression-testing/ac8-tieout-postsplit.2026-05-27T22-40.md` (the three regression tests in `tests/test_mix_rollups_tieout.py` still pass after the module split). | Executor `tieout.2026-05-27T22-27.md`; `ac8-tieout-postsplit.2026-05-27T22-40.md`; reviewer NRR `Check` confirmation. | The `nrr_summary` `Check` resolving to `CHECK` (AC7) is an independent corroboration: that workbook-defined check resolves to `ERROR` if any of the four layers fails to tie out. |
| 9 | README/docstrings updated only as needed; no out-of-scope behavior changes | PASS | Module docstrings in `src/mix_rollups.py` and `src/_mix_rollups_helpers.py` describe the unfiltered-`mix_base` sourcing decision and the issue #20 motivation. `src/mix_pipeline_run.py` docstring updated in the rollup-chain comment block. No `README.md` change in the diff. Diff inspection found no out-of-scope behavior changes: `mix_1_sku` is byte-identical to baseline; output schemas are unchanged. | `git diff --stat b0e048f..528dcbc`; `git diff b0e048f..528dcbc -- README.md` | README was not modified, which is consistent with "only as needed". |

---

## Acceptance Criteria Check-off

The `spec.md` checkbox state is `[x]` for all of AC1-AC9 and matches the audit evaluation above. No updates required.

---

## Regression Posture

- 220 tests pass deterministically (random order via `pytest-randomly`); reviewer rerun confirms.
- The fail-before/pass-after pair (`evidence/regression-testing/fail-before.2026-05-27T22-11.md` exit 1; `evidence/regression-testing/pass-after.2026-05-27T22-17.md` exit 0) demonstrates the unit-level regression coverage. The post-split AC8 evidence (`evidence/regression-testing/ac8-tieout-postsplit.2026-05-27T22-40.md`) confirms the three regression tests still pass after the module split.
- Coverage held at 100/100 line/branch, matching the baseline.
- Test inventory parity: pre-split 11 tests in `tests/test_mix_rollups.py`; post-split 8 tests in `tests/test_mix_rollups.py` + 3 tests in `tests/test_mix_rollups_tieout.py` = 11. Names byte-identical.

---

## Acceptance Criteria Status

- Source: `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/spec.md`
- Total AC items: 9
- Checked off (delivered): 9
- Remaining (unchecked): 0
- Items remaining: (none)
