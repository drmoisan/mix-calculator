# mix-category-customer-mix-tieout (Spec)

- **Issue:** #20
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T21-54
- **Status:** Draft
- **Version:** 0.1

## Context
The mix-decomposition pipeline's `mix_2_category["Category Mix"]` and
`mix_3_customer["Customer Mix"]` column totals do not tie out to the source
workbook's authoritative mix totals, whereas the `mix_1_sku["SKU Mix"]` and
`mix_4_country["Country Mix"]` totals do. This was discovered while replicating
the `NRR_Summary` tab (issue #15): the summary's internal reconciliation `Check`
resolves to `"ERROR"` solely because of these two layers.

Environment:
- OS/version: Windows, PowerShell 7+
- Python version: 3.13 (Poetry in-project `.venv`)
- Command/flags used: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db`
- Data source or fixture: confidential `LE v AOP Gross to Net Decomp.xlsx` (gitignored)

Impact / Severity:
- [ ] Blocker
- [x] High
- [ ] Medium
- [ ] Low

Rationale: the category and customer mix decomposition figures are incorrect
relative to the source of truth, which undermines the mix-attribution output of
the pipeline. It does not block the `NRR_Summary` feature (issue #15), which
faithfully reports the discrepancy.


## Repro & Evidence
Steps to Reproduce:
1. Run the mix pipeline end-to-end against the real workbook (command above).
2. Compare the column total of `mix_2_category["Category Mix"]` and
   `mix_3_customer["Customer Mix"]` in `artifacts/mix.db` against the workbook's
   `NRR_Summary` tab `Category Mix` / `Customer Mix` figures (equivalently, the
   `3-Category-Mix-TopDown` / `4-Customer-Mix-TopDown` table totals).
3. Repeat for `mix_1_sku["SKU Mix"]` vs `2-SKU-Mix-TopDown` and
   `mix_4_country["Country Mix"]` vs `5-Country-Mix`.

Expected:
All four mix-layer column totals tie out to the workbook's authoritative TopDown
snapshot totals (as the SKU and Country layers already do), so that the
`NRR_Summary` reconciliation `Check` resolves to `"CHECK"`.

Actual:
`mix_1_sku["SKU Mix"]` and `mix_4_country["Country Mix"]` match the workbook
exactly. `mix_2_category["Category Mix"]` and `mix_3_customer["Customer Mix"]`
differ from the workbook figures by several orders of magnitude (including a sign
difference), so the `Total Mix` build-up does not equal the realization-derived
`Price/Mix` and the `Check` resolves to `"ERROR"`. (Exact figures omitted: they
are confidential derived aggregates.)

Logs / Screenshots:
- [x] Attached minimal logs or screenshot
- Snippet: see `docs/features/active/2026-05-27-nrr-summary-mix-pipeline-15/evidence/other/e2e-run.2026-05-27T21-08.md` (qualitative, no confidential values).


## Scope & Non-Goals
- In scope: correct the `mix_2_category`, `mix_3_customer`, and `mix_4_country`
  layer aggregation so each layer's volume/revenue totals (and the recomputed
  `Calc Net Price Impact` and mix column) tie out to the workbook's authoritative
  TopDown table totals; update the affected builders, their runner wiring, and
  the tests; verify the `NRR_Summary` `Check` then resolves to `"CHECK"`.
- Out of scope / non-goals: any change to `mix_1_sku` (already correct), to the
  `NRR_Summary` builder (`src/mix_nrr_summary.py`, issue #15 — it faithfully sums
  the layer totals and needs no change), or to the rate-impact / lookup
  transforms; no new dependencies; no CLI/schema changes.
- Explicitly excluded: the SKU and Country mix layers' arithmetic identity (the
  Country layer is already 0 and ties out; SKU already ties out).

## Root Cause Analysis

Confirmed by direct comparison of `artifacts/mix.db` against the workbook
(values are confidential and are not reproduced here; the relationship is
described qualitatively).

The mix cascade feeds each coarser layer the **filtered, reshaped output of the
prior finer layer** rather than the unfiltered detail:

- `build_mix_2_category` builds its stage from `unstack_to_long(mix_1_sku, …)`.
- `build_mix_3_customer` builds its stage from `unstack_to_long(mix_2_category, …)`.
- `build_mix_4_country` builds its stage from `unstack_to_long(mix_3_customer, …)`.

`build_mix_stage` applies a nonzero-Lbs filter (`Lbs - AOP != 0 & Lbs - LE != 0`)
at each grouping. At the SKU layer this correctly drops empty SKU lines, but it
also removes lines that exist in only one scenario (for example a SKU new in LE
with zero AOP Lbs). Because each coarser layer re-aggregates the **already
filtered** prior layer, that dropped volume never reaches the category and
customer aggregates. The result is an understated LE-side `Lbs` and
`Net-Revenue $` at the coarser layers, which corrupts the recomputed
`Net Rev Per Lb - Diff`, the `Calc Net Price Impact`, and therefore the mix
column.

Verification (qualitative): for a representative customer, aggregating the
unfiltered `mix_base` by `{Customer}` reproduces the workbook's category-level
`Lbs - AOP/LE` and `Net-Revenue $ - AOP/LE` exactly, and the resulting recomputed
`Calc Net Price Impact` matches the workbook's category `Calc Net Price Impact`;
aggregating the filtered `mix_1_sku` instead understates the LE side. The SKU
layer is correct because it is the first layer and aggregates `mix_base`
directly; the Country layer ties out because its workbook mix is 0.


## Proposed Fix

### Design summary (what changes where):
Each coarser mix layer must aggregate the **unfiltered `mix_base`** at its own
granularity instead of re-aggregating the prior filtered layer. The
rollup-subtraction target is unchanged: it remains the sum of the prior finer
layer's `Calc Net Price Impact` (via `group_net_price_impact`), so the mix
column stays `(this layer's recomputed NPI) - (sum of finer-layer NPI)`.

### Boundaries and invariants to preserve:
- Transform purity: builders stay I/O-free; `main` remains the only I/O boundary.
- `mix_1_sku` (SKU layer) is unchanged and must remain tied out.
- The customer and country layers' `_apply_fill_zero_and_recompute`
  (`fill_zero_with_avg`) step is preserved where currently applied; the category
  layer continues to apply no zero-fill (full-aggregation recompute already
  matches the workbook there).
- The deliberate `mix_3_customer["Customer Mix"]` column name (issue #9 rename of
  the Excel "Category Mix" label) is preserved.
- The persisted table schemas (column names) and the derived-table set are
  unchanged; `mix_4_country` remains a single-row table.

### Dependencies or blocked work: none. Validation reuses the issue #15
`NRR_Summary` `Check`.

### Implementation strategy (what changes, not sequencing):

#### Files/modules to change:
- `src/mix_rollups.py` — `build_mix_2_category`, `build_mix_3_customer`,
  `build_mix_4_country`: accept `mix_base` and build the stage from it grouped by
  the layer keys (`{Customer, Country}`, `{Country}`, all-rows respectively);
  keep the rollup join/subtract using the prior layer.
- `src/_mix_rollups_helpers.py` — `unstack_to_long` becomes unused by the fixed
  builders; remove it (and its references) if nothing else uses it, or retain
  only if still required by the rollup-target computation.
- `src/mix_pipeline_run.py` — pass `mix_base` to the changed builders in
  `run_transforms`.

#### Functions/classes/CLI commands impacted:
The three rollup builders and `run_transforms`. CLI surface unchanged.

#### Data flow and validation changes:
Coarser layers source volume/revenue from `mix_base`; rollup targets still come
from the prior layer. No validation removed.

#### Error handling and logging updates: none required.

#### Rollback/feature-flag considerations: none; behavior-correcting fix.

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:
Builder signatures change to take `mix_base: pd.DataFrame` (in addition to, or in
place of, the prior-layer argument used only for the rollup). Output frame
columns are unchanged.

#### Required configuration keys and defaults: none.

#### Backward-compatibility expectations:
Output table schemas unchanged; only the (previously incorrect) values change.

#### Performance constraints: none material (small frames).

## Assumptions, Constraints, Dependencies
- Assumptions (environment, data, access):
- Constraints (budget, performance, compatibility):
- External dependencies (services, libraries, releases):

## Data / API / Config Impact
- User-facing or API changes:
- Data or migration considerations:
- Logging/telemetry updates (if any):
- Compatibility notes (CLI flags, config schemas, versioning):

## Test Strategy
Seeded from issue:

- [ ] Unit coverage areas: per-layer mix-column derivation for the category and
  customer levels with fabricated inputs that reproduce the bottoms-up method.
- [ ] Integration scenario to retest: end-to-end run where the `NRR_Summary`
  `Check` resolves to `"CHECK"` once the two layers tie out.
- [ ] Manual verification notes: compare each layer's mix-column total to the
  corresponding workbook TopDown total (SKU and Country already match).

- Regression tests to add or update:
- Unit tests (pytest) for the fixed behavior and boundaries:
- Edge cases and negative scenarios (invalid inputs, missing data, boundary values):
- Error handling and logging verification:
- Coverage impact and targets for changed lines/modules:
- Toolchain commands to run (format → lint → type-check → test):
- Manual validation steps (if required):


## Acceptance Criteria
- [x] AC1: `build_mix_2_category`, `build_mix_3_customer`, and `build_mix_4_country`
  aggregate volume/revenue from the unfiltered `mix_base` at their own
  granularity (not from the prior filtered layer); the builders remain pure
  (I/O-free) and within the 500-line file limit.
- [x] AC2: The rollup-subtraction contract is preserved — each layer's mix column
  equals its recomputed `Calc Net Price Impact` minus the sum of the prior finer
  layer's `Calc Net Price Impact`.
- [x] AC3: `mix_1_sku["SKU Mix"]` is unchanged (no regression on the SKU layer);
  the `mix_3_customer["Customer Mix"]` column name and the `mix_4_country`
  single-row shape are preserved.
- [x] AC4: Deterministic Pytest unit tests with fabricated inputs prove that a
  single-scenario line (zero AOP Lbs / nonzero LE Lbs, and the reverse) is
  retained in the coarser-layer aggregates — i.e. the volume-loss regression is
  covered — and that each layer's recomputed NPI and mix follow the
  full-aggregation-minus-rollup identity. No temp files, no network.
- [x] AC5: Changed-code line coverage >= 85% and branch coverage >= 75%; no
  coverage regression on changed lines.
- [x] AC6: The Python toolchain passes in one clean pass (Black, Ruff, Pyright,
  Pytest).
- [x] AC7: End-to-end: `poetry run python -m src.mix_pipeline --input "artifacts/LE v AOP Gross to Net Decomp.xlsx" --output artifacts/mix.db` writes the mix tables and the appended `nrr_summary` table, and the `nrr_summary` internal `Check` resolves to `"CHECK"`. Evidence recorded without exposing confidential source values (report `Check`, table presence/row counts, and per-layer tie-out pass/fail only).
- [x] AC8: Each of `mix_2_category["Category Mix"]`, `mix_3_customer["Customer Mix"]`,
  `mix_1_sku["SKU Mix"]`, and `mix_4_country["Country Mix"]` column totals ties out
  to the corresponding workbook TopDown table total (verified during the
  end-to-end check; pass/fail recorded without disclosing the figures).
- [x] AC9: `README.md` / docstrings updated only as needed to reflect the
  corrected layer-aggregation description; no unintended behavior changes outside
  scope.

## Risks & Mitigations
- Technical or operational risks: changing the layer-source could perturb the
  customer/country `fill_zero_with_avg` behavior or the rollup join keys.
- Mitigations and rollbacks: the `NRR_Summary` `Check` and the per-layer tie-out
  assertions are an exact end-to-end gate; unit tests pin the single-scenario
  retention and the NPI-minus-rollup identity. The change is value-correcting
  with unchanged schemas, so rollback is a straightforward revert.

## Rollout & Follow-up
- Release/rollout steps: standard PR + CI; merge closes #20.
- Post-fix monitoring or clean-up tasks: confirm issue #15's `nrr_summary` `Check`
  is green on the next pipeline run.
- Links: issue #20; discovered via #15; mix pipeline from #9.
