# Atomic Implementation Plan — mix-decomp-transforms (Issue #9)

- Issue: #9
- Feature folder: `docs/features/active/2026-05-26-mix-decomp-transforms-9/`
- Work Mode: full-feature (resolved from `issue.md` metadata marker `- Work Mode: full-feature`)
- Plan generated: 2026-05-26T20-00
- Requirements sources: `spec.md`, `user-story.md`, `artifacts/research/2026-05-26-mix-decomp-transforms-9.md`
- Implementing worker: `python-typed-engineer`
- Per-batch budget (hard): 3 production files + 3 test files per phase
- Language in scope: Python (Black -> Ruff -> Pyright strict -> Pytest with coverage)
- Coverage gate: line >= 85%, branch >= 75%, no regression on changed lines

## Evidence Location Invariant

All evidence artifacts for this plan are written under the canonical feature evidence root:
`docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/<kind>/`
per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Non-canonical
locations (`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, etc.)
are forbidden and any supplied non-canonical path is rejected and replaced with
the canonical path.

## Reused Modules (do not duplicate)

- `src/normalize_le.py` — LE loader; reused by the pipeline, not modified.
- `src/load_aop.py`, `src/_load_aop_helpers.py` — AOP loader; reused, not modified.
- `src/pandas_io.py` — `read_excel_sheet`, `read_table`, `write_table` I/O boundary.
- `src/etl_columns.py` — `normalize_name`, `resolve_columns` for position-independent column resolution.
- `src/etl_key.py`, `src/etl_totals.py` — KEY resolution and blank-total fill seams.

## Confidentiality Invariant (per-phase acceptance check)

No real customer names, SKU descriptions, category names, SKU numbers, prices, or
discounts may appear in any new source file, test file, fixture, or doc. `SKU Description`
and `Category` from `SKU_LU` are confidential. Fabricated values only (for example
`Acme Foods`, `Globex Market`, `Initech Grocers`, `SKU-001`, `Widget A`, `Category X`).
The `Country` values `US` and `Canada` are not secret.

---

### Phase 0 — Baseline Capture and Policy Reads

- [x] [P0-T1] Read repository policy files in the required order and record an evidence artifact at `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/other/phase0-instructions-read.2026-05-26T20-00.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/benchmark-baselines.md`, `.claude/rules/tonality.md`. Acceptance: artifact exists with all three fields populated.
- [x] [P0-T2] Capture the Black baseline by running `poetry run black --check .` and write the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/baseline/black.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact exists with all four fields; `Output Summary:` states pass/fail and count of files that would be reformatted.
- [x] [P0-T3] Capture the Ruff baseline by running `poetry run ruff check .` and write the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/baseline/ruff.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact exists with all four fields; `Output Summary:` records the error count.
- [x] [P0-T4] Capture the Pyright baseline by running `poetry run pyright` and write the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/baseline/pyright.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact exists with all four fields; `Output Summary:` records error and warning counts.
- [x] [P0-T5] Capture the Pytest coverage baseline by running `poetry run pytest --cov --cov-branch --cov-report=term-missing` and write the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/baseline/pytest-coverage.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact exists with all four fields; `Output Summary:` records numeric baseline line-coverage % and branch-coverage % and the passed/failed test counts.

---

### Phase 1 — Pure Transform Primitives and SkuLu Loader

Budget: 2 production files, 2 test files. DAG layer: primitives plus the `SkuLu`
leaf loader (evaluation steps 1-4 source-shaping helpers and the SKU lookup).

- [x] [P1-T1] Create `src/mix_transforms.py` with the pure primitives `negate_column`, `calc_ratios`, `classify_table`, `stack_pivot`, `add_ratios`, and `fill_zero_with_avg`, each fully type-annotated (`pandas.DataFrame` in/out), with Google-style docstrings, no I/O, and `__all__` declared. Implement `calc_ratios` divide-by-zero guards with `numpy.where(den > 0, num/den, 0.0)` for the eight ratio columns (`Gross Sales Per Lb`, `OI Per Lb`, `Trade Per Lb`, `Non-Trade Per Lb`, `Net Rev Per Lb`, `OI %GS`, `Trade %GS`, `Non-Trade %GS`) per research §3.2. Implement `classify_table` two-level logic (SKU-level inactive/eliminated/new/exists then customer-SKU inactive/normal/lost distribution/new distribution) using exact zero tests per research §3.3. Acceptance: `src/mix_transforms.py` exists, is <= 500 lines, imports cleanly, and exposes the six named functions.
- [x] [P1-T2] Add the pivot primitives `pivot_le` and `pivot_aop` to `src/mix_transforms.py` per research §4.1-§4.2: long->wide pivot on `GtN Mapping`/`YTG` (LE) and `Type`/`YTG` (AOP), `fillna(0)`, rename deductions to `$` names, drop the AOP `%` types, rename `LBs`->`Lbs`, negate `Off Invoice $`/`Trade Spend $`/`Non-Trade $`, add `Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $`, apply `calc_ratios`, then melt back to long Attribute/Value form. Implement the `YTG`-absent fallback in `pivot_aop` that sums `May..Dec` (`YTG_MONTHS`) per research §6.8 / spec versioning note. Acceptance: both functions present in `src/mix_transforms.py`; file remains <= 500 lines.
- [x] [P1-T3] Create `src/load_skulu.py` mirroring the `src/load_aop.py` structure: a `load_skulu(source, *, sheet="SKU_LU")` reader using `src.pandas_io.read_excel_sheet` (header row 1 -> `header=0`), column resolution via `src.etl_columns`, rename `International`->`Country`, cast `SKU`/`SKU Description`/`Category`/`Country` to text, replace `Country` `"0"`->`"US"` and `"1"`->`"Canada"`; and a `persist_skulu(df, db_path, table="sku_lu", if_exists="replace")` writer using `src.pandas_io.write_table`. Pure-vs-I/O separation per spec; full type hints and docstrings. Acceptance: `src/load_skulu.py` exists, is <= 500 lines, exposes `load_skulu` and `persist_skulu`, and reuses `pandas_io` and `etl_columns` (no re-implemented helpers).
- [x] [P1-T4] Create `tests/test_mix_transforms.py` with unit tests (Arrange-Act-Assert, function-scope fixtures, fabricated data only) covering every primitive: `negate_column`; `calc_ratios` positive, zero-Lbs, and zero-Gross-Sales guard branches; `classify_table` every SKU-level branch (inactive/eliminated/new/exists) and every customer-SKU branch (inactive/normal/lost distribution/new distribution); `stack_pivot` header join and sum aggregation; `add_ratios` append-only invariant (no original-row duplication); `fill_zero_with_avg` zero-replacement and zero-Lbs-sum edge; `pivot_le` and `pivot_aop` including the `pivot_aop` `YTG`-absent `May..Dec` fallback. Acceptance: `tests/test_mix_transforms.py` exists, is <= 500 lines, all tests pass, and contains no confidential data values.
- [x] [P1-T5] Create `tests/test_load_skulu.py` covering `load_skulu` (column rename `International`->`Country`, the `"0"`->`"US"`/`"1"`->`"Canada"` replacement, text casts) using an in-memory `BytesIO` Excel fixture, and `persist_skulu` using an in-memory `sqlite3.connect(":memory:")` connection (no temp files). Fixtures use fabricated SKU codes, descriptions, and categories only. Acceptance: `tests/test_load_skulu.py` exists, is <= 500 lines, all tests pass, and contains no confidential data values.
- [x] [P1-T6] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; no suppression added unless it matches a pre-authorized pattern in `.claude/rules/python-suppressions.md`; coverage remains >= 85% line / >= 75% branch with no regression on changed lines; confidentiality check passes (no secret data values in `src/mix_transforms.py`, `src/load_skulu.py`, or their tests).

---

### Phase 2 — Lookups, Normalization, AopVsLe, and Mix_Base

Budget: 1 production file, 1 test file. DAG layer: evaluation steps 3, 5-8
(`CustomerLU`, `AOP_NORM`, `LE_NORM`, `AopVsLe`, `Mix_Base`).

- [x] [P2-T1] Create `src/mix_lookups.py` with pure functions `build_customer_lu` (distinct `{Customer, Customer Master}` per research §4.3), `build_aop_norm` (research §4.5: drop to `{Customer, SKU #, Attribute, Value}`, add `Scenario="AOP"`), `build_le_norm` (research §4.6: same shape, `Scenario="LE"`), `build_aop_vs_le` (research §4.7: concat, pivot Scenario on Value, `fillna(0)`, filter `Attribute != "Cases"`, add `Diff = LE - AOP`, then `classify_table` from `src.mix_transforms`), and `build_mix_base` (research §4.8: cast `SKU #` to `str`, left-join `sku_lu` on `SKU # == SKU`, reorder, filter to the six measure attributes and exclude `Classification == "inactive"`). All functions take/return `pandas.DataFrame`, no I/O, full type hints and docstrings, `Cases` filter and exact-equality classification preserved. Acceptance: `src/mix_lookups.py` exists, is <= 500 lines, exposes the five `build_*` functions, and imports `classify_table` from `src.mix_transforms` (no re-implementation).
- [x] [P2-T2] Create `tests/test_mix_lookups.py` covering `build_customer_lu` (distinct pairs), `build_aop_norm`/`build_le_norm` (column drop and `Scenario` literal), `build_aop_vs_le` (concat+pivot, `fillna(0)`, `Cases` row excluded, `Diff = LE - AOP`, classification column present), and `build_mix_base` (`SKU #` str cast, left-join enrichment with unmatched->null, six-attribute filter, `inactive` exclusion). Arrange-Act-Assert; fabricated data only; SkuLu fixture uses fabricated `SKU Description`/`Category`. Acceptance: `tests/test_mix_lookups.py` exists, is <= 500 lines, all tests pass, and contains no confidential data values.
- [x] [P2-T3] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; coverage >= 85% line / >= 75% branch with no regression on changed lines; no unauthorized suppressions; confidentiality check passes for `src/mix_lookups.py` and `tests/test_mix_lookups.py`.

---

### Phase 3 — Rate Impacts

Budget: 1 production file, 1 test file. DAG layer: evaluation step 9 (`Rate_Impacts`).

- [x] [P3-T1] Create `src/mix_rate_impacts.py` with a pure `build_rate_impacts(aop_vs_le, sku_lu)` per research §4.9: filter `Classification == "normal"`, melt `AOP`/`LE`/`Diff` to Scenario/Value, `stack_pivot({Attribute, Scenario}, "Value")` to wide `"Attr - Scenario"` columns, compute the six derived impact columns (`Calc Gross Price Impact on Gross`, `Calc Gross Price Impact on Net`, `OI Rate Impact`, `Trade Rate Impact`, `Non-Trade Rate Impact`, `Calc Net Price Impact`) with the exact formulas in research §4.9 step 5, then left-join `sku_lu` on `SKU #` to expand `{SKU Description, Category, Country}`. Reuse `stack_pivot` from `src.mix_transforms`. Full type hints, docstrings, no I/O. Acceptance: `src/mix_rate_impacts.py` exists, is <= 500 lines, exposes `build_rate_impacts`, produces all six named impact columns, and imports `stack_pivot` from `src.mix_transforms`.
- [x] [P3-T2] Create `tests/test_mix_rate_impacts.py` covering `build_rate_impacts` with a fabricated `aop_vs_le` fixture containing `normal` and non-`normal` rows: assert non-normal rows are filtered out, assert each of the six derived impact columns matches the hand-computed expected value (within `1e-9` for ratio-derived columns), and assert the `sku_lu` enrichment columns are present. Arrange-Act-Assert; fabricated data only. Acceptance: `tests/test_mix_rate_impacts.py` exists, is <= 500 lines, all tests pass, and contains no confidential data values.
- [x] [P3-T3] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; coverage >= 85% line / >= 75% branch with no regression on changed lines; no unauthorized suppressions; confidentiality check passes for `src/mix_rate_impacts.py` and `tests/test_mix_rate_impacts.py`.

---

### Phase 4 — Mix Rollup Chain and Mix-0-Detail

Budget: up to 2 production files, 1 test file. DAG layer: evaluation steps
10-18 (`Mix-Rollup-1..4`, `Mix-1-SKu`, `Mix-2-Category`, `Mix-3-Customer`,
`Mix-4-Country`, `Mix-0-Detail`). If the single rollups module would exceed
500 lines, split shared rollup logic into `src/_mix_rollups_helpers.py`
following the existing `src/_load_aop_helpers.py` pattern.

- [x] [P4-T1] Create `src/mix_rollups.py` (and, only if needed to stay <= 500 lines, a companion `src/_mix_rollups_helpers.py`) with the pure functions `build_mix_rollup_1`, `build_mix_rollup_2`, `build_mix_rollup_3`, `build_mix_rollup_4` (scalar `float`), `build_mix_1_sku`, `build_mix_2_category`, `build_mix_3_customer`, `build_mix_4_country`, and `build_mix_0_detail`, implementing research §4.10-§4.17. Reuse `add_ratios`, `stack_pivot`, and `fill_zero_with_avg` from `src.mix_transforms`. `build_mix_rollup_4` returns `mix_3_customer["Calc Net Price Impact"].sum()`. `build_mix_4_country` subtracts that scalar as a broadcast and names its derived column `Country Mix`. `build_mix_3_customer` names its derived column `Customer Mix` (documented deviation from the M-source "Category Mix" per spec / research §6.6) and applies `fill_zero_with_avg`. `build_mix_2_category` produces `Category Mix`. Full type hints, docstrings, no I/O. Acceptance: `src/mix_rollups.py` exists; every file produced (including any helper) is <= 500 lines; the nine functions are exposed; `Customer Mix` and `Country Mix` names and the M-source deviation are documented in code.
- [x] [P4-T2] Create `tests/test_mix_rollups.py` covering the rollup chain with a fabricated `mix_base`/`rate_impacts` fixture: assert `build_mix_rollup_1..3` group correctly, `build_mix_rollup_4` returns the scalar sum, `build_mix_1_sku`/`build_mix_2_category`/`build_mix_3_customer`/`build_mix_4_country` produce the expected mix columns (`SKU Mix`, `Category Mix`, `Customer Mix`, `Country Mix`), `build_mix_3_customer`/`build_mix_4_country` apply `fill_zero_with_avg`, `build_mix_0_detail` produces the three composite key columns (`CustSkuCountry`, `CustCatCountry`, `CustCountry`), and the rollup tie-out holds (sum of detail equals corresponding rollup within `1e-9` for ratio columns and exactly for integer measures). Arrange-Act-Assert; fabricated data only. Acceptance: `tests/test_mix_rollups.py` exists, is <= 500 lines, all tests pass including the tie-out assertions, and contains no confidential data values.
- [x] [P4-T3] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; coverage >= 85% line / >= 75% branch with no regression on changed lines; no unauthorized suppressions; confidentiality check passes for `src/mix_rollups.py` (and any helper) and `tests/test_mix_rollups.py`.

---

### Phase 5 — Q1 Results By Sku

Budget: 1 production file, 1 test file. DAG layer: evaluation step 19
(`Q1 Results By Sku`, separate path reading the raw LE monthly columns).

- [x] [P5-T1] Create `src/mix_q1.py` with a pure `build_q1_results_by_sku(le_raw)` per research §4.18: select `{Customer, SKU Descripiton, SKU #, GtN Mapping, Jan, Feb, Mar}`, add `Q1 = Jan + Feb + Mar`, group and pivot `GtN Mapping` on `Q1`, `fillna(0)`, add `Net Rev = Gross Sales - Off Invoice - Non-Trade - Trade` (pre-negation subtraction), rename to `$` names, then apply `calc_ratios` from `src.mix_transforms`. Full type hints, docstrings, no I/O. Acceptance: `src/mix_q1.py` exists, is <= 500 lines, exposes `build_q1_results_by_sku`, and imports `calc_ratios` from `src.mix_transforms`.
- [x] [P5-T2] Create `tests/test_mix_q1.py` covering `build_q1_results_by_sku` with a fabricated raw-LE fixture: assert `Q1 = Jan + Feb + Mar` aggregation, the pivot of GtN measures, the pre-negation `Net Rev` subtraction, the `$` renames, and the appended ratio columns. Arrange-Act-Assert; fabricated data only. Acceptance: `tests/test_mix_q1.py` exists, is <= 500 lines, all tests pass, and contains no confidential data values.
- [x] [P5-T3] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; coverage >= 85% line / >= 75% branch with no regression on changed lines; no unauthorized suppressions; confidentiality check passes for `src/mix_q1.py` and `tests/test_mix_q1.py`.

---

### Phase 6 — Pipeline Orchestration, CLI, and End-to-End Integration

Budget: 1 production file, 1 test file. DAG layer: orchestration over all
transforms plus the `mix-pipeline` CLI.

- [x] [P6-T1] Create `src/mix_pipeline.py` with a `main(argv=None) -> int` CLI entry point following the `argparse` pattern of `src/load_aop.main`. Arguments: `--input` (required), `--output` (required), `--le-sheet` (default `"LE-8 + 4"`), `--aop-sheet` (default `"AOP1"`), `--skulu-input` (default = value of `--input`), `--skulu-sheet` (default `"SKU_LU"`). `main()` orchestrates only (no transform logic): reuse `src.normalize_le` (LE import), `src.load_aop` (AOP import), and `src.load_skulu` (SKU_LU import), then read the import tables back via `src.pandas_io.read_table` and run the transform functions in topological order (evaluation steps 1-19), persisting each of the nineteen derived tables via `src.pandas_io.write_table` with `if_exists="replace"`; persist `mix_rollup_4` as a single-row single-column table. Return `0` on success and `1` on a column/KEY/validation `ValueError` from a reused loader; print a stdout summary of tables written and row counts; configure `logging` once. Full type hints and docstrings; CLI top-level blind-except only if it matches the pre-authorized `BLE001 - CLI top-level error handling` pattern. Acceptance: `src/mix_pipeline.py` exists, is <= 500 lines, exposes `main`, contains no transform logic, and routes all I/O through `src.pandas_io`.
- [x] [P6-T2] Create `tests/test_mix_pipeline.py` as an end-to-end integration test: build a fabricated in-memory Excel workbook (`BytesIO`) supplying `AOP1`, `LE-8 + 4`, and `SKU_LU` sheets and run `mix_pipeline.main` against an in-memory or `:memory:`-backed SQLite database (no runtime temp files). Assert `main` returns `0`, all nineteen derived tables (`le_wide`, `aop_wide`, `customer_lu`, `sku_lu`, `aop_norm`, `le_norm`, `aop_vs_le`, `mix_base`, `rate_impacts`, `mix_rollup_1`, `mix_1_sku`, `mix_rollup_2`, `mix_2_category`, `mix_rollup_3`, `mix_3_customer`, `mix_rollup_4`, `mix_4_country`, `mix_0_detail`, `q1_results_by_sku`) plus the `aop` and `LE` import tables exist, and assert the key rollups tie out (sum of detail equals corresponding rollup within `1e-9` for ratio columns and exactly for integer measures). Arrange-Act-Assert; fabricated data only. Acceptance: `tests/test_mix_pipeline.py` exists, is <= 500 lines, all assertions pass, no runtime temp files are used, and no confidential data values appear.
- [x] [P6-T3] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; coverage >= 85% line / >= 75% branch with no regression on changed lines; no unauthorized suppressions; confidentiality check passes for `src/mix_pipeline.py` and `tests/test_mix_pipeline.py`.

---

### Phase 7 — Quality-Tiers Classification and README

Budget: configuration and documentation only (no new test files).

- [x] [P7-T1] Update `quality-tiers.yml` at the repository root to add the seven new modules under `projects` at tier `T2`: `src/load_skulu.py`, `src/mix_transforms.py`, `src/mix_lookups.py`, `src/mix_rate_impacts.py`, `src/mix_rollups.py`, `src/mix_q1.py`, `src/mix_pipeline.py` (and `src/_mix_rollups_helpers.py` at `T2` if that helper was created in Phase 4), with the same T2-Core rationale as the existing ETL modules. Note for review: the prior checkpoint flagged `quality-tiers.yml` as absent, but it exists at the repo root with existing entries; this task extends it rather than creating it. Acceptance: every new module path appears exactly once under `projects` with a `T2` value; no existing entry is removed or changed; the file remains valid YAML.
- [x] [P7-T2] Update `README.md` to document the `mix-decomp-transforms` pipeline and the `mix-pipeline` CLI: the single-workbook end-to-end invocation (`mix-pipeline --input <workbook.xlsx> --output <database.db>`), the optional `--le-sheet`/`--aop-sheet`/`--skulu-input`/`--skulu-sheet` arguments and their defaults, the nineteen derived SQLite tables produced, and the confidentiality note that the source workbooks and output `.db` are gitignored. Use only schema names and fabricated examples; no confidential data values. Acceptance: `README.md` documents the CLI surface, defaults, and the nineteen derived tables; contains no confidential data values.
- [x] [P7-T3] Run the full toolchain loop and persist evidence to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/`: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step fails or changes files. Acceptance: all four commands exit 0 in a single pass; the CI tier-classification expectation is satisfied (every project, including the seven new modules, has a tier); coverage >= 85% line / >= 75% branch with no regression.

---

### Phase 8 — Final QA Loop and Acceptance Verification

Budget: verification only. Full language-appropriate QA loop for Python with
coverage-mode tests and numeric coverage evidence.

- [x] [P8-T1] Run `poetry run black --check .` and persist the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/final-black.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: `EXIT_CODE: 0`; `Output Summary:` confirms all files formatted.
- [x] [P8-T2] Run `poetry run ruff check .` and persist the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/final-ruff.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: `EXIT_CODE: 0`; `Output Summary:` records zero errors and confirms no unauthorized suppressions.
- [x] [P8-T3] Run `poetry run pyright` and persist the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/final-pyright.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: `EXIT_CODE: 0`; `Output Summary:` records zero errors.
- [x] [P8-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and persist the result to `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/final-pytest-coverage.2026-05-26T20-00.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: `EXIT_CODE: 0`; `Output Summary:` records post-change numeric line-coverage % (>= 85), branch-coverage % (>= 75), and the passed test count; if any QA step changed files, restart the loop from P8-T1.
- [x] [P8-T5] Record a coverage delta/threshold verification artifact at `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/qa-gates/coverage-delta.2026-05-26T20-00.md` reporting baseline coverage (from Phase 0), post-change coverage (from P8-T4), and new/changed-code coverage for the seven new modules and their tests. Acceptance: artifact records all three numeric values; new/changed-code coverage meets the >= 85% line / >= 75% branch gate with no regression on changed lines.
- [x] [P8-T6] Verify every acceptance criterion in `user-story.md` and the Definition of Done in `spec.md` against the implemented code and tests, and record a mapping artifact at `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/other/acceptance-verification.2026-05-26T20-00.md` linking each criterion to the implementing module/test or evidence file. Confirm: all nineteen derived tables persisted; single `mix-pipeline` CLI runs end-to-end reusing the loaders; `SKU_LU` loaded with `International`->`Country` and `0`/`1`->`US`/`Canada`; six helper transforms pure and independently tested; two-level classification with exact zero tests; rollup tie-out within tolerance; `Customer Mix` and scalar `mix_rollup_4` subtraction; no confidential values anywhere; no file exceeds 500 lines; seven new `T2` entries in `quality-tiers.yml`. Acceptance: every acceptance criterion is mapped to verified evidence; any unmet criterion is reported as remediation-required rather than PASS.
