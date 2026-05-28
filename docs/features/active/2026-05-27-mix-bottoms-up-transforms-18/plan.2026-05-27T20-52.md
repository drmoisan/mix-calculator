# mix-bottoms-up-transforms — Plan

- **Issue:** #18
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T20-52
- **Status:** Ready for preflight
- **Version:** 1.0
- **Work Mode:** full-feature

## Required References

- Spec (authoritative): [`spec.md`](spec.md) — output columns, grains, derived arithmetic, Classification sourcing, SUMIFS join keys, divide-by-zero guards, `fillna(0)` behavior. Data & State section is verbatim contract.
- User story / AC mirror: [`user-story.md`](user-story.md) — AC1–AC14 (spec governs on divergence).
- Research (authoritative for current-pipeline facts, column names, file:line references): [`artifacts/research/mix-bottoms-up-transforms-18.2026-05-27T00-00-00.md`](../../../../artifacts/research/mix-bottoms-up-transforms-18.2026-05-27T00-00-00.md)
- Cross-language policy: `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`
- Python policy: `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
- Quality tiers: `.claude/rules/quality-tiers.md` (new modules are T2: line >= 85%, branch >= 75%, >= 1 property test per pure function)
- Commenting/docstrings: `.claude/rules/self-explanatory-code-commenting.md`
- Tonality: `.claude/rules/tonality.md`

**All work must comply with these policies; do not duplicate their content here. Detailed formulas live in `spec.md` Data & State and research sections 4, 5, 9, 11 — do not restate confidential data anywhere.**

## Confidentiality (hard constraint)

The source workbook `artifacts/LE v AOP Gross to Net Decomp.xlsx` is confidential. No form of its data may be persisted in any source file, test, or fixture. All test data must be fabricated (`SKU-001`, `Widget A`, `Category X`; `US`/`Canada` are not secret). No task in this plan instructs reading or loading the workbook. AC13 (confidentiality review) is enforced in the final phase.

## Scope summary (locked — do not redesign)

- New `src/mix_bottomsup.py`: `build_mix_2_sku_bottomsup`, `build_mix_3_category_bottomsup`, `build_mix_4_customer_bottomsup`.
- New `src/_mix_bottomsup_helpers.py`: `build_contribution_columns`, `_classify_from_lbs`.
- Wire three builder calls into `run_transforms` in `src/mix_pipeline_run.py` after `mix_0_detail`; extend the return dict. No change to `src/mix_pipeline.py` or `src/pandas_io.py`.
- Add `src/mix_bottomsup.py: T2` and `src/_mix_bottomsup_helpers.py: T2` to `quality-tiers.yml`.
- Update the mix-pipeline section of `README.md` (table list and derived-table count: nineteen → twenty-two).
- New `tests/test_mix_bottomsup.py` (AC1–AC11, AC13); extend `tests/test_mix_pipeline.py` `_DERIVED_TABLES` for AC12.

## Batch-budget note (Python engineer cap: 3 production .py + 3 test .py per batch)

- Production `.py` files in scope: `src/_mix_bottomsup_helpers.py`, `src/mix_bottomsup.py`, `src/mix_pipeline_run.py` (3 — at the cap).
- Test `.py` files in scope: `tests/test_mix_bottomsup.py`, `tests/test_mix_pipeline.py` (2).
- `quality-tiers.yml` and `README.md` are config/docs (not production `.py`) and do not consume the production-file budget.
- Phases 1–4 are sequenced so each phase's edits stay within one batch: Phase 1 touches helper + its tests; Phase 2 touches `mix_bottomsup.py` + its tests; Phase 3 touches `mix_pipeline_run.py` + `quality-tiers.yml` + `tests/test_mix_pipeline.py`; Phase 4 touches `README.md` (docs). No single phase exceeds the cap.

## Toolchain loop (run for every code/test-touching task)

Run in this exact order and restart from step 1 on any failure or any file auto-modified:

1. `poetry run black .`
2. `poetry run ruff check .`
3. `poetry run pyright`
4. `poetry run pytest --cov --cov-branch --cov-report=term-missing`

A task is complete only when format, lint, type-check, and test all pass in a single uninterrupted pass. Prefix Poetry with `env -u VIRTUAL_ENV` if the global `VIRTUAL_ENV` shadows the in-project venv.

## Evidence locations (canonical — non-overridable)

All evidence artifacts MUST be written under `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/evidence/<kind>/` per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing to `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, `artifacts/evidence/`, or any other non-canonical path is a policy violation. Timestamp format: `yyyy-MM-ddTHH-mm`. Each command-step artifact MUST include `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`. Baseline and final-QC test artifacts MUST include numeric coverage headline values (overall line/branch percent and new-module percent where applicable).

---

## Implementation Plan (Atomic Tasks)

### Phase 0 — Baseline Capture & Policy Reading

- [x] [P0-T1] Read the repository policy files in the required order and record an evidence artifact listing each file read.
  - Files read (order): `CLAUDE.md`; `.claude/rules/general-code-change.md`; `.claude/rules/general-unit-test.md`; `.claude/rules/python.md`; `.claude/rules/python-suppressions.md`; `.claude/rules/quality-tiers.md`; `.claude/rules/self-explanatory-code-commenting.md`; `.claude/rules/tonality.md`.
  - Acceptance: `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/evidence/baseline/phase0-instructions-read.2026-05-27T20-52.md` exists with `Timestamp:`, `Policy Order:`, and the explicit list of files read.

- [x] [P0-T2] Capture the baseline Black formatting state.
  - Command: `poetry run black --check .`
  - Acceptance: `evidence/baseline/black-baseline.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (pass/fail and files-would-reformat count).

- [x] [P0-T3] Capture the baseline Ruff lint state.
  - Command: `poetry run ruff check .`
  - Acceptance: `evidence/baseline/ruff-baseline.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count).

- [x] [P0-T4] Capture the baseline Pyright type-check state.
  - Command: `poetry run pyright`
  - Acceptance: `evidence/baseline/pyright-baseline.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning count).

- [x] [P0-T5] Capture the baseline Pytest + coverage state with numeric headline values.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `evidence/baseline/pytest-coverage-baseline.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including baseline total line coverage % and branch coverage % (numeric, not placeholders), and the passed-test count. New modules do not exist yet, so their coverage is recorded as N/A at baseline.

- [x] [P0-T6] Confirm the in-scope file inventory and current line counts to support the 500-line limit check later.
  - Files inspected: `src/mix_pipeline_run.py` (currently 98 lines), `quality-tiers.yml`, `README.md`, `tests/test_mix_pipeline.py`, `tests/test_mix_rollups.py` (fixture source).
  - Acceptance: `evidence/baseline/file-inventory-baseline.<ts>.md` records `Timestamp:` and the current line count of `src/mix_pipeline_run.py` and confirms `src/mix_bottomsup.py` / `src/_mix_bottomsup_helpers.py` / `tests/test_mix_bottomsup.py` do not yet exist.

### Phase 1 — Shared Contribution Helper (`src/_mix_bottomsup_helpers.py`)

Batch: 1 production file (`src/_mix_bottomsup_helpers.py`) + 1 test file (`tests/test_mix_bottomsup.py`, created here for the property test).

- [x] [P1-T1] Create `src/_mix_bottomsup_helpers.py` with `_classify_from_lbs(lbs_aop: float, lbs_le: float) -> str` implementing the four-branch zero-test exactly as specified.
  - Formula source: `spec.md` Classification sourcing block / research section 5 (`if lbs_aop == 0: "eliminated" if lbs_le == 0 else "new distribution"; else "lost distribution" if lbs_le == 0 else "normal"`). Lowercase tokens only.
  - File: `src/_mix_bottomsup_helpers.py`. Include module docstring, function docstring, and branch decision-logic comments per commenting policy. Full type hints; no `Any`; no suppressions.
  - Toolchain gate: run the full loop (Black → Ruff → Pyright → Pytest).
  - Acceptance: function returns the correct token for each of the four `(lbs_aop, lbs_le)` zero/nonzero combinations; toolchain passes in a single pass. Advances AC8, AC10 (Classification re-derivation prerequisite).

- [x] [P1-T2] Add `build_contribution_columns(frame: pd.DataFrame) -> pd.DataFrame` to `src/_mix_bottomsup_helpers.py` computing Share - AOP/LE, Share Shift, Mix Rate, New/Disco/Normal Contribution, and SKU Mix from an input frame already carrying Classification, Lbs - AOP/LE, Net Rev Per Lb - AOP/LE, Blended Rate - AOP/LE, Lbs Subtotal - AOP/LE.
  - Formula source: `spec.md` Data & State "Derived arithmetic" block and research section 9. Every division guarded to `0.0` when denominator is `0` (mirror existing `_safe_div` pattern from `src/_mix_transforms_helpers.py`). Use `numpy.where` for the conditional contribution branches. Classification matching is case-sensitive against lowercase tokens `"new"`, `"new distribution"`, `"lost distribution"`, `"eliminated"`, `"normal"`. SKU Mix = New + Disco + Normal.
  - File: `src/_mix_bottomsup_helpers.py`. Function does not mutate its input frame (returns a new/augmented frame). Loop/branch intent comments required.
  - Toolchain gate: full loop.
  - Acceptance: returned frame carries the eight derived columns; toolchain passes in a single pass; `src/_mix_bottomsup_helpers.py` is under 500 lines. Advances AC2, AC3, AC4, AC5, AC11.

- [x] [P1-T3] Create `tests/test_mix_bottomsup.py` with the property-based test `test_build_contribution_columns_sku_mix_equals_sum` using `hypothesis` over arbitrary valid float inputs, asserting `SKU Mix == New Contribution + Disco Contribution + Normal Contribution`.
  - File: `tests/test_mix_bottomsup.py`. Fabricated/synthetic float inputs only (no workbook data). Use a seeded/reproducible hypothesis strategy; assert with a float tolerance appropriate to the arithmetic. Arrange–Act–Assert; descriptive name; docstring.
  - Toolchain gate: full loop.
  - Acceptance: property test passes; toolchain passes in a single pass. Satisfies AC11 and the T2 property-test-per-pure-function requirement.

- [x] [P1-T4] Add a unit test `test_classify_from_lbs_branches` (parametrized) to `tests/test_mix_bottomsup.py` covering all four `_classify_from_lbs` branches.
  - File: `tests/test_mix_bottomsup.py`. `pytest.mark.parametrize` over the four zero/nonzero combinations and expected tokens.
  - Toolchain gate: full loop.
  - Acceptance: all four cases pass; toolchain passes in a single pass. Advances AC8, AC10 branch coverage.

### Phase 2 — Builder Functions (`src/mix_bottomsup.py`)

Batch: 1 production file (`src/mix_bottomsup.py`) + 1 test file (`tests/test_mix_bottomsup.py`).

- [x] [P2-T1] Create `src/mix_bottomsup.py` with module docstring, `__all__`, imports, and `build_mix_2_sku_bottomsup(mix_0_detail, mix_base, mix_1_sku) -> pd.DataFrame`.
  - Behavior source: `spec.md` Data & State `mix_2_sku_bottomsup` (22 columns, exact order, one row per `mix_0_detail` row) and research sections 3 and 11. Pass-through identity/measure columns from `mix_0_detail`; `Classification` joined from `mix_base` via `drop_duplicates(["Customer","SKU #","Classification"])` on `(Customer, SKU #)`; Blended Rate / Lbs Subtotal aggregated from `mix_1_sku` over `(Customer, Category)` and left-merged, then `fillna(0)` on those four columns; derived columns produced by `build_contribution_columns`. Output column order exactly per spec.
  - File: `src/mix_bottomsup.py`. Document the SUMIFS single-`(Customer, Category)` join expectation in the builder docstring (per spec Constraints & Risks); optional non-fatal data-quality warning permitted but must not emit confidential data and must not hard-fail. Full type hints; no `Any`; no suppressions; docstrings and branch/loop comments per policy.
  - Toolchain gate: full loop.
  - Acceptance: function returns a frame with the 22 spec columns in order; toolchain passes in a single pass. Advances AC1, AC6.

- [x] [P2-T2] Add `build_mix_3_category_bottomsup(mix_0_detail, mix_2_category) -> pd.DataFrame` to `src/mix_bottomsup.py`.
  - Behavior source: `spec.md` Data & State `mix_3_category_bottomsup` and research sections 3, 6, 11. Row set = groupby-sum of `mix_0_detail` over `["CustCatCountry","Customer","Category","Country"]` summing `Lbs - AOP/LE` and `Net-Revenue $ - AOP/LE`; `Net Rev Per Lb - AOP/LE` derived as `Net-Revenue $ / Lbs` guarded to `0`; `Classification` re-derived via `_classify_from_lbs`; Blended Rate / Lbs Subtotal aggregated from `mix_2_category` over `(Customer, Country)`, left-merged, `fillna(0)`; derived columns via `build_contribution_columns`. Output column order exactly per spec.
  - File: `src/mix_bottomsup.py`. Docstrings and decision-logic comments required.
  - Toolchain gate: full loop.
  - Acceptance: function returns a frame with the spec category columns in order, one row per distinct `CustCatCountry`; toolchain passes in a single pass. Advances AC7, AC8.

- [x] [P2-T3] Add `build_mix_4_customer_bottomsup(mix_0_detail, mix_3_customer) -> pd.DataFrame` to `src/mix_bottomsup.py`.
  - Behavior source: `spec.md` Data & State `mix_4_customer_bottomsup` and research sections 3, 6, 11. Same structure as the category builder grouped over `["CustCountry","Customer","Country"]`; Blended Rate / Lbs Subtotal aggregated from `mix_3_customer` over `(Country)`, left-merged on `Country`, `fillna(0)`; `Classification` re-derived via `_classify_from_lbs`; derived columns via `build_contribution_columns`. Output column order exactly per spec.
  - File: `src/mix_bottomsup.py`. Docstrings and decision-logic comments required.
  - Toolchain gate: full loop.
  - Acceptance: function returns a frame with the spec customer columns in order, one row per distinct `CustCountry`; toolchain passes in a single pass; `src/mix_bottomsup.py` is under 500 lines. Advances AC9, AC10.

- [x] [P2-T4] Add the SKU-table fixture and unit tests to `tests/test_mix_bottomsup.py`: `test_build_mix_2_sku_bottomsup_columns_present` and `test_build_mix_2_sku_bottomsup_row_count_matches_detail`.
  - File: `tests/test_mix_bottomsup.py`. Build a fabricated `mix_base` (reuse the `_mix_base_rows`/`_mix_base_fixture` pattern from `tests/test_mix_rollups.py`, replicated locally or imported; fabricated data only), run the real chain builders to produce `mix_0_detail`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`, then call the BottomsUp builders. No temp files; in-memory DataFrames only.
  - Toolchain gate: full loop.
  - Acceptance: column-presence test asserts all 22 columns in order; row-count test asserts output rows == `mix_0_detail` rows; toolchain passes in a single pass. Satisfies AC1.

- [x] [P2-T5] Add SKU contribution-branch and guard tests to `tests/test_mix_bottomsup.py`: `test_build_mix_2_sku_bottomsup_normal_sku_mix_tieout`, `test_build_mix_2_sku_bottomsup_new_contribution_active_when_new`, `test_build_mix_2_sku_bottomsup_disco_contribution_active_when_lost`, `test_build_mix_2_sku_bottomsup_zero_lbs_subtotal_share_is_zero`, `test_build_mix_2_sku_bottomsup_classification_joined_correctly`.
  - File: `tests/test_mix_bottomsup.py`. Fixture must include at least one SKU of each classification (`"normal"`, `"new"`/`"new distribution"`, `"lost distribution"`/`"eliminated"`) to exercise every branch. Normal tie-out uses a hand-calculated expected value asserted with a float tolerance; new/disco tests assert the active column is nonzero and the other two are zero; zero-subtotal test asserts Share columns are `0.0` not `NaN`; classification-join test asserts output `Classification` matches `mix_base` for the same `(Customer, SKU #)`. Fabricated data only.
  - Toolchain gate: full loop.
  - Acceptance: all five tests pass; toolchain passes in a single pass. Satisfies AC2, AC3, AC4, AC5, AC6.

- [x] [P2-T6] Add category and customer tests to `tests/test_mix_bottomsup.py`: `test_build_mix_3_category_bottomsup_columns_present`, `test_build_mix_3_category_bottomsup_row_count_matches_distinct_keys`, `test_build_mix_3_category_bottomsup_sku_mix_tieout`, `test_build_mix_4_customer_bottomsup_columns_present`, `test_build_mix_4_customer_bottomsup_row_count_matches_distinct_keys`, `test_build_mix_4_customer_bottomsup_sku_mix_tieout`.
  - File: `tests/test_mix_bottomsup.py`. Column-presence tests assert the exact spec column order; row-count tests assert one row per distinct `CustCatCountry` / `CustCountry`; tie-out tests hand-calculate `SKU Mix` for a normal group (with `Net Rev Per Lb` derived as `Net-Revenue $ / Lbs` and Classification re-derived from aggregated Lbs) and assert with a float tolerance. Fabricated data only.
  - Toolchain gate: full loop.
  - Acceptance: all six tests pass; toolchain passes in a single pass. Satisfies AC7, AC8, AC9, AC10.

- [x] [P2-T7] Verify new-module coverage meets thresholds and record an interim coverage artifact for `src/mix_bottomsup.py` and `src/_mix_bottomsup_helpers.py`.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `evidence/qa-gates/coverage-new-modules.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` with numeric line and branch coverage for `src/mix_bottomsup.py` and `src/_mix_bottomsup_helpers.py`, both >= 85% line / >= 75% branch. If below threshold, add targeted tests in `tests/test_mix_bottomsup.py` and rerun before completing. Advances AC14.

### Phase 3 — Pipeline Wiring & Tier Classification

Batch: 1 production file (`src/mix_pipeline_run.py`) + config (`quality-tiers.yml`) + 1 test file (`tests/test_mix_pipeline.py`).

- [x] [P3-T1] Wire the three builders into `run_transforms` in `src/mix_pipeline_run.py`: import them, add three call sites after `mix_0_detail` is computed (passing the in-scope `mix_0_detail`, `mix_base`, `mix_1_sku`, `mix_2_category`, `mix_3_customer`), and add the three tables to the return dict.
  - Behavior source: `spec.md` Implementation Strategy and research section 7. No signature change (`mix_base` is already a parameter). Update the `run_transforms` docstring and `__all__`/import block. Add `mix_2_sku_bottomsup`, `mix_3_category_bottomsup`, `mix_4_customer_bottomsup` to the returned mapping. No change to `src/mix_pipeline.py` or `src/pandas_io.py`.
  - File: `src/mix_pipeline_run.py`. Call-site comments describing the new step per commenting policy.
  - Toolchain gate: full loop.
  - Acceptance: `run_transforms` returns the three new keys; `src/mix_pipeline_run.py` is under 500 lines; toolchain passes in a single pass. Advances AC12.

- [x] [P3-T2] Add `src/mix_bottomsup.py: T2` and `src/_mix_bottomsup_helpers.py: T2` to the `projects` mapping in `quality-tiers.yml`, in the mix-decomp section, with a brief comment consistent with the existing rationale.
  - File: `quality-tiers.yml`. Both modules classified T2 (Core), matching the other pure-transform mix modules.
  - Toolchain gate: full loop (the tier-classification rule requires every project be classified; verify no unclassified-project failure).
  - Acceptance: both new module paths appear with `T2`; toolchain passes in a single pass. Satisfies the spec Definition-of-Done tier requirement.

- [x] [P3-T3] Extend `_DERIVED_TABLES` in `tests/test_mix_pipeline.py` to include `mix_2_sku_bottomsup`, `mix_3_category_bottomsup`, and `mix_4_customer_bottomsup`, so the end-to-end test asserts the three tables appear in `sqlite_master` after a single-connection `mix-pipeline` run.
  - File: `tests/test_mix_pipeline.py`. Add the three names to the existing `_DERIVED_TABLES` list (the existing loop at the `sqlite_master` assertion validates presence). Update the module/test docstring count ("nineteen derived tables" → "twenty-two") if it states a count.
  - Toolchain gate: full loop.
  - Acceptance: the end-to-end test passes with the three new tables present; toolchain passes in a single pass. Satisfies AC12.

### Phase 4 — Documentation

Batch: docs only (`README.md`); no production `.py` budget consumed.

- [x] [P4-T1] Update the mix-pipeline section of `README.md` to list the three new BottomsUp tables and update the derived-table count.
  - File: `README.md` (mix-decomposition section, around lines 99–104). Change "nineteen derived tables" to "twenty-two", and append `mix_2_sku_bottomsup`, `mix_3_category_bottomsup`, `mix_4_customer_bottomsup` to the enumerated list. Keep the existing confidentiality note. No confidential data added.
  - Toolchain gate: full loop (README is Markdown; the gate confirms no code/test regression was introduced by the doc edit).
  - Acceptance: the three table names and the updated count appear in `README.md`; toolchain passes in a single pass. Satisfies the spec Definition-of-Done README requirement.

### Phase 5 — Final QA, Coverage Gate, Limits & AC Checkoff

Run the full QA loop unconditionally; restart from step 1 if any step fails or modifies files. No final-QC command task may be reported as SKIPPED.

- [x] [P5-T1] Run final Black formatting check and record the QA-gate artifact.
  - Command: `poetry run black --check .`
  - Acceptance: `evidence/qa-gates/black-final.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` (all files formatted). Advances AC14.

- [x] [P5-T2] Run final Ruff lint check and record the QA-gate artifact.
  - Command: `poetry run ruff check .`
  - Acceptance: `evidence/qa-gates/ruff-final.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` (0 errors, no unauthorized suppressions). Advances AC14.

- [x] [P5-T3] Run final Pyright type-check and record the QA-gate artifact.
  - Command: `poetry run pyright`
  - Acceptance: `evidence/qa-gates/pyright-final.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` (0 errors, no new `Any`). Advances AC14.

- [x] [P5-T4] Run final Pytest with coverage and record numeric post-change coverage in the QA-gate artifact.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `evidence/qa-gates/pytest-coverage-final.<ts>.md` records `Timestamp:`, `Command:`, `EXIT_CODE: 0`, `Output Summary:` with numeric overall line coverage % and branch coverage %, and the per-module line/branch % for `src/mix_bottomsup.py` and `src/_mix_bottomsup_helpers.py`. All tests pass. Advances AC14.

- [x] [P5-T5] Verify the coverage delta and thresholds against the Phase 0 baseline.
  - Acceptance: `evidence/qa-gates/coverage-delta.<ts>.md` records baseline coverage (from P0-T5), post-change coverage (from P5-T4), and new/changed-code coverage; confirms overall line >= 85%, branch >= 75%, no regression on changed lines, and new-module coverage >= 85% line / >= 75% branch. If any threshold is unmet, mark the plan outcome remediation-required (not PASS) and add targeted tests before re-running Phase 5. Satisfies AC14.

- [x] [P5-T6] Verify the 500-line file-size limit for all new and changed production/test files.
  - Files checked: `src/mix_bottomsup.py`, `src/_mix_bottomsup_helpers.py`, `src/mix_pipeline_run.py`, `tests/test_mix_bottomsup.py`, `tests/test_mix_pipeline.py`.
  - Acceptance: `evidence/qa-gates/file-size-check.<ts>.md` records each file's line count; all <= 500. Satisfies AC14.

- [x] [P5-T7] Perform a confidentiality review of all new and changed test and fixture files.
  - Files reviewed: `tests/test_mix_bottomsup.py`, any fixture additions, and `tests/test_mix_pipeline.py` diff.
  - Acceptance: `evidence/qa-gates/confidentiality-review.<ts>.md` records `Timestamp:` and confirms only fabricated example data appears (`SKU-001`, `Widget A`/`Widget X`, `Category X`, `US`/`Canada`); no value traceable to `artifacts/LE v AOP Gross to Net Decomp.xlsx` is present; no task in this feature read or loaded the workbook. Satisfies AC13.

- [x] [P5-T8] Map every acceptance criterion to its verifying test and record the AC checkoff.
  - Acceptance: `evidence/qa-gates/ac-checkoff.<ts>.md` records the AC1–AC14 → test/artifact mapping: AC1 (P2-T4), AC2/AC3/AC4/AC5 (P2-T5), AC6 (P2-T5), AC7/AC8 (P2-T6), AC9/AC10 (P2-T6), AC11 (P1-T3), AC12 (P3-T3), AC13 (P5-T7), AC14 (P5-T1..T6). All marked verified with the corresponding passing evidence; any unverified AC blocks PASS.

## Test Plan

- Unit (`tests/test_mix_bottomsup.py`): column-presence and row-count for all three tables; SKU normal tie-out; New/Disco contribution-branch activation; zero-subtotal Share guard; Classification join; category and customer tie-outs; `_classify_from_lbs` four-branch parametrized test.
- Property-based (`tests/test_mix_bottomsup.py`, hypothesis): `test_build_contribution_columns_sku_mix_equals_sum` — `SKU Mix = New + Disco + Normal` for arbitrary valid floats (AC11, T2 requirement).
- Integration (`tests/test_mix_pipeline.py`): the three new tables appear in `sqlite_master` after an end-to-end `mix-pipeline` run on a single in-memory connection (AC12) via extended `_DERIVED_TABLES`.
- Confidentiality review: AC13, all new/changed test and fixture files (P5-T7).
- Coverage evidence:
  - Baseline: `evidence/baseline/pytest-coverage-baseline.<ts>.md`
  - Post-change: `evidence/qa-gates/pytest-coverage-final.<ts>.md`
  - Delta/threshold comparison: `evidence/qa-gates/coverage-delta.<ts>.md`

## Open Questions / Notes

- SUMIFS single-`(Customer, Category)` join for the SKU-table Blended Rate / Lbs Subtotal (research section 10, Risk 1; spec Constraints & Risks): implement the `(Customer, Category)` left-merge to match the Excel formula faithfully and document the single-country expectation in the builder docstring. A non-fatal data-quality warning at the builder boundary is permitted but optional; it must not hard-fail and must not emit confidential data. Production-data validation of this assumption is the implementer's responsibility and is noted, not blocking.
- The final-column name `SKU Mix` is retained on all three tables per the Excel seed (spec Data & State), even at the category and customer levels.
