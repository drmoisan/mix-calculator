# Feature Audit: nrr-summary-mix-pipeline (Issue #15)

**Audit Date:** 2026-05-27
**Feature Folder:** `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15`
**Base Branch:** `main`
**Head Branch:** `feature/nrr-summary-mix-pipeline-15`
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `703de5170c37dadb8189eecc01398730d5c50e8d`)
- **Head branch/commit:** `feature/nrr-summary-mix-pipeline-15` (commit `7f47625ef6a508f99541e0274e0068c1dd871eb6`)
- **Merge base:** `703de5170c37dadb8189eecc01398730d5c50e8d`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/evidence/**`
  - Additional evidence: `artifacts/python/lcov.info`; direct inspection of `artifacts/mix.db`
- **Feature folder used:** `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15`
- **Requirements source:** `issue.md` (`## Acceptance Criteria`, AC1–AC10) — minor-audit
- **Work mode resolution note:** `issue.md` carries `- Work Mode: minor-audit`. Per the work-mode contract, the only authoritative AC source is the explicit `## Acceptance Criteria` section in `issue.md`. `spec.md` and `user-story.md` are not present and are not consulted.
- **Scope note:** AC10 was revised by the recorded "Option A" user decision (2026-05-27, `issue.md` Scope Decision) to verify that the internal `Check` is computed and reported accurately rather than requiring `Check == "CHECK"`. The audit is performed against the full branch diff `703de51..7f47625`; no scope narrowing was accepted.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/issue.md` — only source (minor-audit)

### Acceptance criteria

1. **AC1**: A new pure builder module `src/mix_nrr_summary.py` exposes a function that builds the `nrr_summary` frame from the existing pipeline frames (`aop_vs_le`, `rate_impacts`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`, `mix_4_country`) and performs no I/O. The module stays within the 500-line limit.
2. **AC2**: The attribute-summary block reproduces `Lbs`, `Gross Sales`, `Net-Revenue $` (AOP/LE/Abs as `aop_vs_le` SUMIF-by-`Attribute` sums, `%` = Abs/AOP), the derived `GS / Lb` and `Net Rev / Lb` ratios (Abs = LE − AOP), and `All in TS%` (AOP = 1 − NetRev/GrossSales, LE likewise, Abs = (LE − AOP) × 10000 basis points, no `%`).
3. **AC3**: The Net Revenue Realization block reproduces `Volume Impact` (`Lbs.Abs × NetRevPerLb.AOP`) and `Price/Mix` (`NetRev.Abs − VolumeImpact`), each with `%NR = value / NetRev.AOP`.
4. **AC4**: The Net Pricing Breakdown block reproduces `Gross Pricing`, `OI Rate`, `Promo Rate`, `Non-trade Rate` as `rate_impacts` column totals and `Total Net Pricing` as their sum, each with `%NR = value / NetRev.AOP`.
5. **AC5**: The Mix Breakdown block reproduces `SKU Mix`, `Category Mix`, `Customer Mix`, `Country Mix` as the column-total of each level table and `Total Mix` as their sum. The `Customer Mix` value reads the `mix_3_customer["Customer Mix"]` column; a code comment records the deliberate Excel-to-pipeline rename mapping.
6. **AC6**: The reconciliation block reproduces `Price / Mix` (build-up = `Total Mix + Total Net Pricing`; `%NR` = `%Total Mix + %Total Net Pricing`) and the `Check` row, which is `"CHECK"` when `round(realization − buildup, 0) == 0` (computed independently for NR$ and %NR) and `"ERROR"` otherwise.
7. **AC7**: `src/mix_pipeline.py` builds `nrr_summary` after the existing derived tables and persists it as the final derived table through `src/pandas_io.py`; the stdout summary lists `nrr_summary`; the existing CLI exit semantics are unchanged.
8. **AC8**: Deterministic Pytest unit tests with fabricated inputs cover each block, the division-by-zero / empty-input edges of the per-Lb and `%` derivations, and the `Check == "ERROR"` divergence path. No temp files, no network. Changed-code line coverage >= 85% and branch coverage >= 75%.
9. **AC9**: The Python toolchain passes in one clean pass (Black, Ruff, Pyright, Pytest). `src/mix_nrr_summary.py` is classified in `quality-tiers.yml` (T2) and `README.md` documents the appended `nrr_summary` table.
10. **AC10 (revised, Option A)**: An end-to-end `mix-pipeline` run against the real workbook writes `nrr_summary` as the final derived table, and the internal `Check` value is computed and reported accurately. AC10 is satisfied when `nrr_summary` is written and `Check` reflects the true reconciliation state; the upstream tie-out defect is tracked separately as issue #20.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Pure builder module, no I/O, < 500 lines | PASS | `src/mix_nrr_summary.py` defines `build_nrr_summary` reading the six frames; pandas under `TYPE_CHECKING` + one local import; 439 lines. Helpers split into `_mix_nrr_summary_helpers.py` (236 lines). | `wc -l src/mix_nrr_summary.py src/_mix_nrr_summary_helpers.py` | No disk/DB/network reads in the builder. |
| 2 | Attribute-summary block (core measures, per-Lb ratios, All-in-TS% basis points) | PASS | `_attribute_summary_rows` + `_per_lb_row` + `ts_basis_points` (`BASIS_POINT_SCALE = 10000`). Asserted in `test_attribute_summary_core_measures_are_sumif_totals` and `test_attribute_summary_per_lb_and_ts_derivations`. | `poetry run pytest tests/test_mix_nrr_summary.py` | `All in TS%` carries no `%` column; SUMIF aggregation confirmed by two-row-per-attribute fixture. |
| 3 | Net-Revenue Realization block (Volume Impact, Price/Mix, %NR) | PASS | `_realization_rows`; asserted in `test_net_revenue_realization_block` (Volume 20, Price/Mix 10, %NR 0.20/0.10). | `poetry run pytest tests/test_mix_nrr_summary.py` | Zero Lbs.AOP path yields `None`. |
| 4 | Net Pricing Breakdown block (four column totals + Total Net Pricing, %NR) | PASS | `_net_pricing_rows`; Promo Rate reads `Trade Rate Impact`. Asserted in `test_net_pricing_breakdown_block` (totals 4/1/1/1, Total 7). | `poetry run pytest tests/test_mix_nrr_summary.py` | Column-to-label mapping explicit. |
| 5 | Mix Breakdown block + deliberate Customer Mix mapping | PASS | `_mix_rows` reads `mix_3_customer["Customer Mix"]` with a rationale comment; asserted in `test_mix_breakdown_block_reads_customer_mix_column` and the `KeyError` negative test. | `poetry run pytest tests/test_mix_nrr_summary.py` | Mapping pinned by `test_customer_mix_requires_customer_mix_column`. |
| 6 | Reconciliation block + Check (CHECK/ERROR, NR$ and %NR independently) | PASS | `_reconciliation_rows` + `reconciles`; both CHECK and ERROR paths asserted (`test_reconciliation_check_passes_when_buildup_ties_out`, `test_reconciliation_check_errors_when_buildup_diverges`). | `poetry run pytest tests/test_mix_nrr_summary.py` | `round(realization − buildup, 0) == 0` per comparison; both must reconcile. |
| 7 | Pipeline persists `nrr_summary` as final derived table; stdout lists it; CLI exit unchanged | PASS | `mix_pipeline_run.run_transforms` returns `nrr_summary` last; `mix_pipeline._persist_all` writes it via `pandas_io.write_table`; `_print_summary` lists each derived table; `main` exit semantics unchanged. E2E stdout shows `nrr_summary: 20 rows`. | `poetry run python -m src.mix_pipeline --input ... --output artifacts/mix.db` (exit 0) | Independently verified: `artifacts/mix.db` contains `nrr_summary` with 20 rows. |
| 8 | Deterministic unit tests cover blocks + zero/empty edges + ERROR path; changed-code coverage >= 85% line / >= 75% branch | PASS | 14 tests; zero-denominator and empty-frame edges and ERROR path covered. lcov: `mix_nrr_summary.py` 100% line/branch, helpers 100% line/branch. | `poetry run pytest tests/test_mix_nrr_summary.py`; inspect `artifacts/python/lcov.info` | No temp files, no network. Coverage exceeds threshold. |
| 9 | Toolchain clean single pass; T2 classification; README documents table | PASS | Black/Ruff/Pyright/Pytest re-run clean this audit (0 errors). `quality-tiers.yml` lists `src/mix_nrr_summary.py: T2` and `src/_mix_nrr_summary_helpers.py: T2`. `README.md` documents `nrr_summary`. | `poetry run black --check`; `ruff check`; `pyright`; `pytest` | All four stages exit 0 on the changed files. |
| 10 | E2E writes `nrr_summary`; `Check` computed and reported accurately (Option A) | PASS | E2E run exit 0; `nrr_summary` written as final table; `Check == "ERROR"` independently confirmed in `artifacts/mix.db`. The `"ERROR"` faithfully surfaces the pre-existing upstream issue #9 defect (issue #20), not a defect in this feature; realization Price/Mix, pricing block, and SKU/Country mix totals tie out per the e2e diagnosis. | inspect `artifacts/mix.db` `nrr_summary.[check]` for metric `Check` | Satisfied under the recorded Option A revision; upstream tie-out tracked as issue #20. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 10 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Track issue #20 (`mix-category-customer-mix-tieout`) so the upstream `mix_2_category` / `mix_3_customer` tie-out is corrected; once fixed, the live `Check` should resolve to `"CHECK"` without any change to this feature.
2. Optionally align the `README.md` "Coverage policy" line with the uniform >= 85% line / >= 75% branch thresholds in `.claude/rules/quality-tiers.md` in a future docs pass (Info-level, non-blocking).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, all ten criteria are evaluated PASS and are represented as markdown checkboxes in `issue.md`. They were already checked off `[x]` during execution; this audit confirms the check-off state is consistent with the verified PASS evaluations. No checkbox state change was required.

### AC Status Summary

- Source: `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/issue.md`
- Total AC items: 10
- Checked off (delivered): 10
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 10 | 10 | 0 | Checkbox-backed; minor-audit `## Acceptance Criteria`. All already `[x]`; audit confirms PASS. |
