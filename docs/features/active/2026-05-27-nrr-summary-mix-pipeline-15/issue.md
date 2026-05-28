# nrr-summary-mix-pipeline (Issue #15)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/nrr-summary-mix-pipeline/ (Issue #15)

- Issue: #15
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/15
- Last Updated: 2026-05-28
- Work Mode: minor-audit

## Problem / Why

The end-to-end mix pipeline (`src/mix_pipeline.py`, issue #9) replicates most tabs
of the confidential `LE v AOP Gross to Net Decomp.xlsx` workbook into SQLite
tables, but it does not yet produce the `NRR_Summary` tab. `NRR_Summary` is the
headline summary of the analysis: it ties the Net-Revenue change between AOP and
LE back to its drivers (volume, net pricing, and mix) and carries an internal
reconciliation CHECK. It is derived entirely from tabs the pipeline already
replicates, so it can be appended as a final pure summary step.

## Proposed Behavior

Add a pure transform that builds an `nrr_summary` table from existing pipeline
tables and persist it as the final derived table in `mix_pipeline`. No new I/O
paths and no source-workbook reads beyond what the pipeline already performs.

### Source-tab logic (replicated from `NRR_Summary`)

The Excel tab is a 30-row labeled grid. Columns: `AOP`, `LE`, `Abs` change,
`%` change (top block); `NR $` and `%NR` (lower blocks). All inputs come from
tables the pipeline already writes. The `[[#Totals]]` references in Excel are
plain column sums of the corresponding pandas tables.

Top block — AOP-vs-LE attribute summary (source: `aop_vs_le`, SUMIF by
`Attribute`):

- `Lbs`, `Gross Sales`, `Net-Revenue $`: for each label, `AOP = sum(aop_vs_le.AOP where Attribute==label)`, `LE = sum(LE)`, `Abs = sum(Diff)`, `% = Abs/AOP`.
- `GS / Lb`: `AOP = GrossSales.AOP / Lbs.AOP`; `LE = GrossSales.LE / Lbs.LE`; `Abs = LE - AOP`; `% = Abs/AOP`.
- `Net Rev / Lb`: `AOP = NetRev.AOP / Lbs.AOP`; `LE = NetRev.LE / Lbs.LE`; `Abs = LE - AOP`; `% = Abs/AOP`.
- `All in TS%`: `AOP = 1 - NetRev.AOP/GrossSales.AOP`; `LE = 1 - NetRev.LE/GrossSales.LE`; `Abs = (LE - AOP) * 10000` (basis-point scaling; no `%` column).

Net Revenue Realization block (`NR $`, `%NR` where `%NR = NR$ / NetRev.AOP`):

- `Volume Impact`: `NR$ = Lbs.Abs * NetRevPerLb.AOP` (i.e. Lbs `Diff` x AOP Net Rev per Lb).
- `Price/Mix`: `NR$ = NetRev.Abs - VolumeImpact.NR$`.

Net Pricing Breakdown block (source: `rate_impacts` column totals):

- `Gross Pricing` = sum(`Calc Gross Price Impact on Net`).
- `OI Rate` = sum(`OI Rate Impact`).
- `Promo Rate` = sum(`Trade Rate Impact`).
- `Non-trade Rate` = sum(`Non-Trade Rate Impact`).
- `Total Net Pricing` = sum of the four rows above.
- `%NR` for each = `NR$ / NetRev.AOP`.

Mix Breakdown block (source: per-level mix table totals):

- `SKU Mix` = sum(`mix_1_sku["SKU Mix"]`).
- `Category Mix` = sum(`mix_2_category["Category Mix"]`).
- `Customer Mix` = sum(`mix_3_customer["Customer Mix"]`). Note: the Excel formula
  references the `Category Mix` column header in the customer table; the pipeline
  already renamed that column to `Customer Mix`, so the replication reads
  `Customer Mix`. This mapping must be preserved deliberately.
- `Country Mix` = sum(`mix_4_country["Country Mix"]`).
- `Total Mix` = sum of the four rows above.

Reconciliation block:

- `Price / Mix` (build-up) `NR$ = Total Mix + Total Net Pricing`; `%NR = %Total Mix + %Total Net Pricing`.
- `Check`: `"CHECK"` when `round(PriceMix_realization.NR$ - PriceMix_buildup.NR$, 0) == 0` else `"ERROR"`; same comparison for the `%NR` column. This is the internal tie-out between the realization-derived Price/Mix and the pricing+mix build-up.

### Recommended output schema

To remove ambiguity, `nrr_summary` should faithfully represent the labeled grid
as a tidy long table with one row per source-tab label, in source order. The
recommended columns are:

- `section` (str): one of `attribute_summary`, `net_revenue_realization`,
  `net_pricing_breakdown`, `mix_breakdown`, `reconciliation`.
- `metric` (str): the row label exactly as on the tab (for example `Lbs`,
  `Gross Sales`, `Net-Revenue $`, `GS / Lb`, `Net Rev / Lb`, `All in TS%`,
  `Volume Impact`, `Price/Mix`, `Gross Pricing`, `OI Rate`, `Promo Rate`,
  `Non-trade Rate`, `Total Net Pricing`, `SKU Mix`, `Category Mix`,
  `Customer Mix`, `Country Mix`, `Total Mix`, `Price / Mix`, `Check`).
- `aop` (float | None): column C value where the row defines it, else `None`.
- `le` (float | None): column D value where the row defines it, else `None`.
- `value` (float | None): column E value — the `Abs` change in the attribute
  block, or the `NR $` figure in the realization/pricing/mix/reconciliation
  blocks. `None` where the row defines no column-E value.
- `pct` (float | None): column F value — `%` change in the attribute block or
  `%NR` in the lower blocks. `None` where the row defines no column-F value.
- `check` (str | None): `"CHECK"` / `"ERROR"` for the reconciliation `Check`
  row; `None` for every other row. The `Check` row stores its NR$-column and
  %NR-column results in `value` and `pct` as strings, mirrored into `check` for
  convenience, OR the planner may choose a single `check`-only representation —
  the executor selects one and tests pin it. The reconciliation logic itself is
  non-negotiable.

The exact column set may be refined by the plan, but the table must represent
every labeled row and its computed values, including the `Check` result.

## Acceptance Criteria

- [x] AC1: A new pure builder module `src/mix_nrr_summary.py` exposes a function
  that builds the `nrr_summary` frame from the existing pipeline frames
  (`aop_vs_le`, `rate_impacts`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`,
  `mix_4_country`) and performs no I/O. The module stays within the 500-line
  limit.
- [x] AC2: The attribute-summary block reproduces `Lbs`, `Gross Sales`,
  `Net-Revenue $` (AOP/LE/Abs as `aop_vs_le` SUMIF-by-`Attribute` sums, `%` =
  Abs/AOP), the derived `GS / Lb` and `Net Rev / Lb` ratios (Abs = LE − AOP),
  and `All in TS%` (AOP = 1 − NetRev/GrossSales, LE likewise, Abs = (LE − AOP) ×
  10000 basis points, no `%`).
- [x] AC3: The Net Revenue Realization block reproduces `Volume Impact`
  (`Lbs.Abs × NetRevPerLb.AOP`) and `Price/Mix` (`NetRev.Abs − VolumeImpact`),
  each with `%NR = value / NetRev.AOP`.
- [x] AC4: The Net Pricing Breakdown block reproduces `Gross Pricing`,
  `OI Rate`, `Promo Rate`, `Non-trade Rate` as `rate_impacts` column totals
  (`Calc Gross Price Impact on Net`, `OI Rate Impact`, `Trade Rate Impact`,
  `Non-Trade Rate Impact`) and `Total Net Pricing` as their sum, each with
  `%NR = value / NetRev.AOP`.
- [x] AC5: The Mix Breakdown block reproduces `SKU Mix`, `Category Mix`,
  `Customer Mix`, `Country Mix` as the column-total of each level table and
  `Total Mix` as their sum. The `Customer Mix` value reads the
  `mix_3_customer["Customer Mix"]` column; a code comment records that this maps
  the Excel tab's `Mix_3_Customer[[#Totals],[Category Mix]]` reference (the
  pipeline renamed the column).
- [x] AC6: The reconciliation block reproduces `Price / Mix` (build-up =
  `Total Mix + Total Net Pricing`; `%NR` = `%Total Mix + %Total Net Pricing`)
  and the `Check` row, which is `"CHECK"` when
  `round(PriceMix_realization − PriceMix_buildup, 0) == 0` (computed
  independently for the NR$ and %NR comparisons) and `"ERROR"` otherwise.
- [x] AC7: `src/mix_pipeline.py` builds `nrr_summary` after the existing derived
  tables and persists it as the final derived table through `src/pandas_io.py`;
  the stdout summary lists `nrr_summary`; the existing CLI exit semantics are
  unchanged.
- [x] AC8: Deterministic Pytest unit tests with fabricated inputs cover each
  block, the division-by-zero / empty-input edges of the per-Lb and `%`
  derivations, and the `Check == "ERROR"` divergence path. No temp files, no
  network. Changed-code line coverage >= 85% and branch coverage >= 75%.
- [x] AC9: The Python toolchain passes in one clean pass (Black, Ruff, Pyright,
  Pytest). `src/mix_nrr_summary.py` is classified in `quality-tiers.yml` (T2,
  matching the sibling transforms) and `README.md` documents the appended
  `nrr_summary` table.
- [x] AC10 (revised 2026-05-27, Option A): An end-to-end `mix-pipeline` run
  against the real workbook writes `nrr_summary` as the final derived table, and
  the internal `Check` value is computed and reported accurately. On the current
  pipeline the `Check` resolves to `"ERROR"` because two upstream issue #9 tables
  — `mix_2_category["Category Mix"]` and `mix_3_customer["Customer Mix"]` — do not
  tie out to the workbook's authoritative mix totals, while `mix_1_sku` and
  `mix_4_country` do. The NRR_Summary replication faithfully sums the mix columns
  exactly as the workbook tab does (the workbook's own `Check` reconciles), so the
  `"ERROR"` correctly surfaces the upstream defect rather than indicating a defect
  in this feature. AC10 is satisfied when `nrr_summary` is written and `Check`
  reflects the true reconciliation state; the upstream tie-out defect is tracked
  as a separate follow-up bug (see Scope Decision below). Evidence:
  `evidence/other/e2e-run.2026-05-27T21-08.md` (no confidential values disclosed).

## Scope Decision (2026-05-27)

The new `Check` surfaced a pre-existing discrepancy in the issue #9 rollup
cascade: the `mix_2_category["Category Mix"]` and `mix_3_customer["Customer Mix"]`
column totals do not match the workbook's authoritative TopDown snapshot totals
(verified directly against the workbook and `mix.db`; `SKU Mix` and `Country Mix`
match). Per the user's Option A decision, this feature lands as a faithful
replication of the `NRR_Summary` tab logic, and the upstream tie-out defect is
filed and tracked as a separate bug (**issue #20**, `Bug:
mix-category-customer-mix-tieout`) rather than fixed under this additive-summary
scope. Modifying the issue #9 decomposition math is explicitly out of scope here.

## Implementation Notes

- Pattern parity: the builder mirrors the existing pure `src/mix_*` transforms;
  the orchestration call and the persist go in `src/mix_pipeline.py` (or its
  `src/mix_pipeline_run.py` runner), keeping `main` I/O-only.
- The `[[#Totals]]` Excel references are plain pandas column sums.
- Guard the per-Lb and `%` divisions against a zero denominator explicitly
  (fail-fast or `None`/`NaN` per the plan), since `aop_vs_le` AOP totals are
  non-zero for the real data but tests will exercise the zero path.

## Constraints & Risks

- Confidentiality: no source numeric values in tests, fixtures, or docs; use
  fabricated examples only. Table/column names and formula labels are schema.
- The builder must be pure (no I/O); all reads/writes route through the existing
  `mix_pipeline` orchestrator and `src/pandas_io.py`.
- File-size limit 500 lines per module; coverage >= 85% line / >= 75% branch.
- The `mix_3_customer` "Category Mix" -> "Customer Mix" column mapping must be
  preserved deliberately and documented.

## Test Conditions to Consider

- [ ] Unit coverage of each block (attribute summary, realization, pricing, mix, reconciliation) with fabricated inputs.
- [ ] Division-by-zero / empty-input edge handling for per-Lb and `%` derivations.
- [ ] CHECK returns `"ERROR"` when the build-up and realization Price/Mix diverge.
- [ ] End-to-end: `mix_pipeline` writes `nrr_summary` and the CHECK passes on the real run.

## Next Step

- [x] Promote to GitHub issue (feature request template)
- [x] Create `docs/features/active/nrr-summary-mix-pipeline/` folder from the template