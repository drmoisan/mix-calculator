# etl-le-topline-input — Plan

- **Issue:** #2
- **Parent (optional):** n/a
- **Owner:** Dan Moisan
- **Last Updated:** 2026-05-25T20-21
- **Status:** Ready for execution
- **Version:** 0.1.0
- **Work Mode:** full-feature
- **Module Tier:** T2 (Core)

## Required References

- General Code Change Policy: `.claude/rules/general-code-change.md`
- General Unit Test Policy: `.claude/rules/general-unit-test.md`
- Quality Tiers: `.claude/rules/quality-tiers.md`
- Python Code Standards: `.claude/rules/python.md`
- Python Suppression Policy: `.claude/rules/python-suppressions.md`
- Commenting/Docstring Policy: `.claude/rules/self-explanatory-code-commenting.md`
- Tonality Policy: `.claude/rules/tonality.md`

**All work must comply with these policies; do not duplicate their content here.**

## Authoritative Inputs

- `docs/features/active/2026-05-25-etl-le-topline-input-2/issue.md` (AUTHORITATIVE — requirements, source/target schema, acceptance criteria, anti-requirements)
- `docs/features/active/2026-05-25-etl-le-topline-input-2/spec.md` (behavior, API/CLI surface, invariants, DoD)
- `docs/features/active/2026-05-25-etl-le-topline-input-2/user-story.md` (acceptance criteria mirror, non-goals)
- `artifacts/research/2026-05-25T00-00-normalize-le-research.md` (research; its Q3 Excel-Table/openpyxl-write section and CSV branch are SUPERSEDED by the SQLite sink — all other findings remain valid)

## Evidence Location Invariant

All evidence artifacts produced by this plan MUST be written under
`docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/`
per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing to
`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other
non-canonical evidence path is a policy violation and is rejected by the
`enforce-evidence-locations.ps1` PreToolUse hook. (Note: coverage tooling output
`artifacts/python/lcov.info` is a toolchain build artifact configured in
`pyproject.toml`, not an evidence artifact; evidence summaries that cite coverage
numbers are written under the canonical `evidence/` subtree.)

## Settled Implementation Decisions (do not re-litigate)

- Deliverable: `src/normalize_le.py`; CLI invoked as `python -m src.normalize_le`.
- Add `normalize-le = "src.normalize_le:main"` under `[tool.poetry.scripts]`.
- Runtime deps: `pandas = ">=2.2,<3.0"`, `openpyxl = ">=3.1,<4.0"`. Dev dep: `hypothesis = ">=6.100,<7.0"`. numpy is transitive via pandas. `sqlite3` is stdlib (no new dependency).
- Tests in `tests/test_normalize_le.py`, importing `from src.normalize_le import ...`.
- NO temp files: Excel I/O round-trips through `io.BytesIO`; SQLite round-trips through `sqlite3.connect(":memory:")` in tests. The test module provides an in-memory source-workbook builder helper.
- No Clock/RNG injection (pure transform; no datetime/time/random usage).

---

## Implementation Plan (Atomic Tasks)

### Phase 0 — Compliance & Baseline Capture

- [x] [P0-T1] Read repo policy files in required order and record a policy-read evidence artifact
  - Files to read, in order: `CLAUDE.md` (if present), `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/baseline/phase0-instructions-read.md` exists and contains `Timestamp:`, `Policy Order:`, and the explicit list of files read.

- [x] [P0-T2] Capture baseline Black formatting state on the branch before any change
  - Command: `poetry run black --check .`
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/baseline/baseline-black.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (pass/fail and count of files that would be reformatted).

- [x] [P0-T3] Capture baseline Ruff lint state on the branch before any change
  - Command: `poetry run ruff check .`
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/baseline/baseline-ruff.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count or "All checks passed").

- [x] [P0-T4] Capture baseline Pyright type-check state on the branch before any change
  - Command: `poetry run pyright`
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/baseline/baseline-pyright.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).

- [x] [P0-T5] Capture baseline Pytest + coverage state on the branch before any change
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/baseline/baseline-pytest.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric baseline line-coverage % and branch-coverage % and the passed/failed test counts.

### Phase 1 — Dependencies & Project Configuration

- [x] [P1-T1] Add `pandas = ">=2.2,<3.0"` and `openpyxl = ">=3.1,<4.0"` under `[tool.poetry.dependencies]` in `pyproject.toml`
  - Acceptance: `pyproject.toml` `[tool.poetry.dependencies]` lists both pinned ranges exactly; no other dependency lines removed.

- [x] [P1-T2] Add `hypothesis = ">=6.100,<7.0"` under `[tool.poetry.group.dev.dependencies]` in `pyproject.toml`
  - Acceptance: `pyproject.toml` `[tool.poetry.group.dev.dependencies]` lists `hypothesis` with the pinned range exactly.

- [x] [P1-T3] Add `[tool.poetry.scripts]` entry `normalize-le = "src.normalize_le:main"` in `pyproject.toml`
  - Acceptance: `pyproject.toml` contains a `[tool.poetry.scripts]` table with exactly that entry.

- [x] [P1-T4] Regenerate the Poetry lock file with the VIRTUAL_ENV quirk prefix
  - Command: `env -u VIRTUAL_ENV poetry lock`
  - Reason: `VIRTUAL_ENV` points at the global Python; the unprefixed command resolves against the wrong interpreter.
  - Acceptance: `poetry.lock` is regenerated and includes `pandas`, `openpyxl`, transitive `numpy`, and `hypothesis`; command `EXIT_CODE` is 0.

- [x] [P1-T5] Install dependencies into the project `.venv` with the VIRTUAL_ENV quirk prefix
  - Command: `env -u VIRTUAL_ENV poetry install`
  - Reason: unprefixed install writes to the global environment instead of `.venv`.
  - Acceptance: `env -u VIRTUAL_ENV poetry run python -c "import pandas, openpyxl, hypothesis"` exits 0.

### Phase 2 — Scalar Coercion & Key Rebuild (pure functions)

- [x] [P2-T1] Implement `coerce_sku(val: object) -> str` in `src/normalize_le.py`
  - Rules: NaN -> `""`; `int`/`np.integer` -> `str(int(v))`; integer-valued `float` -> `str(int(v))`; other `float` -> `str(v)`; else `str(v)`. Full type annotations; Google-style docstring.
  - Acceptance: function exists with the documented branch behavior and is Pyright-strict clean.

- [x] [P2-T2] Implement `rebuild_key(customer: str, sku: str, type_: str) -> str` in `src/normalize_le.py`
  - Rule: concatenate `customer + coerce_sku-rendered sku + type_` with no separator; never trust a loaded/cached `KEY` value.
  - Acceptance: function exists, calls/uses `coerce_sku` for the SKU segment, full type hints, docstring present.

- [x] [P2-T3] Add unit tests for `coerce_sku` covering int, np.integer, integer-valued float, non-integer float, NaN, and non-numeric string code in `tests/test_normalize_le.py`
  - Acceptance: parametrized tests assert `coerce_sku(5) == "5"`, `coerce_sku(np.int64(5)) == "5"`, `coerce_sku(5.0) == "5"`, `coerce_sku(5.5) == "5.5"`, `coerce_sku(np.nan) == ""`, `coerce_sku("RGFBOWLCB") == "RGFBOWLCB"`; all pass.

- [x] [P2-T4] Add a hypothesis property test for `coerce_sku` in `tests/test_normalize_le.py`
  - Property: for any integer drawn from `st.integers()`, `coerce_sku(int_value)` equals `str(int_value)` and contains no `"."`.
  - Acceptance: property test runs under hypothesis and passes; satisfies the T2 ">=1 property test per pure function" obligation for `coerce_sku`.

- [x] [P2-T5] Add unit + property tests for `rebuild_key` in `tests/test_normalize_le.py`
  - Unit: assert known triples concatenate without separators and use coerced SKU (e.g. whole-number SKU renders integer, non-numeric SKU preserved verbatim).
  - Property: for arbitrary text customer/type and integer SKU, the rebuilt key equals `customer + str(int_sku) + type_`.
  - Acceptance: both tests pass; satisfies the T2 property-test obligation for `rebuild_key`.

### Phase 3 — Source Schema Validation & Load (I/O boundary)

- [x] [P3-T1] Implement the source-column contract constant and `validate_schema(columns: list[str]) -> None` in `src/normalize_le.py`
  - Rule: confirm the 26 source columns A..Z in exact order (`KEY, YTD/YTG, Customer, SKU Descripiton, SKU #, Type, GtN Mapping, Jan..Dec, FY, Q1..Q4, Super Category, PPG`); raise `ValueError` naming missing AND extra columns on mismatch (preserve the `SKU Descripiton` typo verbatim).
  - Acceptance: function raises a `ValueError` whose message names offending columns on mismatch and returns `None` on an exact match.

- [x] [P3-T2] Implement `load_source(path: str, sheet_name: str) -> pd.DataFrame` in `src/normalize_le.py`
  - Rule: `pd.read_excel(path, sheet_name=sheet_name, header=2, engine="openpyxl")`; call `validate_schema` on the loaded columns; drop rows with blank `Customer`; rebuild `KEY` via `rebuild_key`/`coerce_sku` (never trust the loaded value).
  - Acceptance: function is fully type-annotated (`pd.DataFrame` return), reads via openpyxl with `header=2`, and is documented as an I/O boundary.

- [x] [P3-T3] Add an in-memory source-workbook builder helper to `tests/test_normalize_le.py`
  - Rule: helper accepts row dictionaries and returns an `io.BytesIO` `.xlsx` whose sheet has two leading non-data rows then the 26-column header on Excel row 3, written with openpyxl/pandas; NO temp files.
  - Acceptance: helper returns a `BytesIO` that `pd.read_excel(..., header=2, engine="openpyxl")` loads with the 26 expected columns.

- [x] [P3-T4] Add schema-validation unit tests (missing column, extra column, out-of-order column) in `tests/test_normalize_le.py`
  - Acceptance: each case asserts `validate_schema` raises `ValueError` and the message names the specific offending column(s); the exact-match case asserts no raise.

- [x] [P3-T5] Add `load_source` tests for `header=2` parsing, blank-`Customer` drop, and KEY rebuild in `tests/test_normalize_le.py`
  - Cases: a workbook with trailing blank-`Customer` rows yields a frame without those rows; the rebuilt `KEY` ignores any loaded `KEY` cell value and equals `Customer + coerce_sku(SKU #) + Type`.
  - Acceptance: tests use the in-memory builder (no temp files) and pass.

### Phase 4 — Normalize Transform & YTG Derivation (pure functions)

- [x] [P4-T1] Implement `compute_ytg(df: pd.DataFrame) -> pd.Series` in `src/normalize_le.py`
  - Rule: `YTG = sum(May..Dec)` computed on the output rows; full type annotations (`pd.Series`); docstring.
  - Acceptance: function returns a `pd.Series` equal to the row-wise sum of the `May..Dec` columns.

- [x] [P4-T2] Implement `normalize(df: pd.DataFrame) -> pd.DataFrame` in `src/normalize_le.py`
  - Rules: text cols (`Customer, SKU Descripiton, SKU #, Type, GtN Mapping`) from first row per KEY via `drop_duplicates(subset="KEY", keep="first")`; sum cols (`Jan..Dec, FY, Q1..Q4`) via `groupby("KEY", sort=False).sum()` (default `min_count=0`, 0-fills NaN); derived `YTG` via `compute_ytg`; BOTH `Super Category` and `PPG` output columns populated from source `PPG` (as-built quirk); output exactly the 26 target columns in order (`KEY, Customer, SKU Descripiton, SKU #, Type, GtN Mapping, Jan..Dec, FY, Q1..Q4, YTG, Super Category, PPG`); one row per unique KEY in first-appearance order; no rounding (float64 preserved); `YTD/YTG` absent.
  - Acceptance: function returns a frame with the 26 target columns in exact order and one row per unique KEY in first-appearance order; Pyright-strict clean.

- [x] [P4-T3] Add `compute_ytg` unit + property tests in `tests/test_normalize_le.py`
  - Unit: known May..Dec values sum to the expected YTG; Jan..Apr excluded.
  - Property: for arbitrary finite float month vectors, `compute_ytg` equals the sum of months 5..12 within `1e-9`.
  - Acceptance: both tests pass; satisfies the T2 property-test obligation for `compute_ytg`.

- [x] [P4-T4] Add `normalize` aggregation unit tests for singleton KEY, a 2-row YTD+YTG pair, and 3+ rows per KEY in `tests/test_normalize_le.py`
  - Cases: singleton KEY passes through unchanged; 2-row pair sums month/FY/quarter columns; 3+ rows sum all matching rows; NaN month cells treated as 0; text columns taken from the first matching row.
  - Acceptance: each case asserts the summed numeric values and first-row text values; all pass.

- [x] [P4-T5] Add `normalize` invariant tests for column order, first-appearance order, the Super Category/PPG quirk, and no-sort behavior in `tests/test_normalize_le.py`
  - Cases: output columns equal the 26 target list in order; rows appear in first-appearance order (assert a deliberately non-alphabetical input keeps its order); `Super Category` and `PPG` both equal source `PPG` and are identical per row; `YTD/YTG` absent; non-numeric SKU codes preserved verbatim in `KEY` and `SKU #`.
  - Acceptance: all assertions pass.

- [x] [P4-T6] Add a hypothesis property test for `normalize` in `tests/test_normalize_le.py`
  - Property: for an arbitrary set of KEYs each with 1..N source rows of arbitrary finite month values, the output row count equals the number of unique KEYs and each output month column equals the per-KEY source sum within `1e-6`.
  - Acceptance: property test passes; satisfies the T2 property-test obligation for `normalize`.

### Phase 5 — Tie-out Validation (pure function)

- [x] [P5-T1] Implement `validate_tieouts(source_df: pd.DataFrame, output_df: pd.DataFrame, tol: float = 1e-6) -> None` in `src/normalize_le.py`
  - Rules: output-row-count == number of unique KEYs; per-column source/output tie-outs for months + `FY` + `Q1..Q4` within `tol`; `FY == sum(months)` per output row; raise `ValueError` on any failure (mapped to non-zero exit by `main`).
  - Acceptance: function returns `None` on a faithful transform and raises `ValueError` with a descriptive message on each failure mode.

- [x] [P5-T2] Add `validate_tieouts` pass-path and failure-path unit tests in `tests/test_normalize_le.py`
  - Cases: pass case (faithful source/output) raises nothing; row-count mismatch raises; a column total perturbed beyond `1e-6` raises; an `FY != sum(months)` row raises.
  - Acceptance: each failure case asserts `ValueError`; pass case asserts no raise.

- [x] [P5-T3] Add a hypothesis property test for `validate_tieouts` in `tests/test_normalize_le.py`
  - Property: for arbitrary finite source frames, the output produced by `normalize(load-equivalent)` always passes `validate_tieouts` (round-trip consistency between `normalize` and `validate_tieouts`).
  - Acceptance: property test passes; satisfies the T2 property-test obligation for `validate_tieouts`.

### Phase 6 — SQLite Persistence (I/O boundary)

- [x] [P6-T1] Implement `write_sqlite(df: pd.DataFrame, db_path: str, table_name: str) -> None` in `src/normalize_le.py`
  - Rule: `con = sqlite3.connect(db_path); df.to_sql(table_name, con, if_exists="replace", index=False); con.close()`. Drop-and-replace existing table; do not persist the index. If Ruff `S608` flags the table-name argument, document the safe handling: `table_name` originates from a CLI argument and `to_sql` quotes the identifier; apply a narrow `# noqa: S608` with an explicit justification comment only after attempting resolution per `.claude/rules/python-suppressions.md`, otherwise no suppression.
  - Acceptance: function is fully type-annotated, documented as an I/O boundary, and uses `if_exists="replace", index=False`.

- [x] [P6-T2] Add an in-memory SQLite round-trip integration test in `tests/test_normalize_le.py`
  - Rule: persist a normalized frame via `write_sqlite` into a `sqlite3.connect(":memory:")` connection (inject/share the in-memory connection so no file is created), read the table back, and assert the 26 columns in exact order and the expected row count (one per unique KEY); NO temp files.
  - Acceptance: read-back asserts column names/order and row count; test passes without creating files.

- [x] [P6-T3] Add a replace-if-exists (re-run) integration test in `tests/test_normalize_le.py`
  - Rule: write the same frame twice into the same in-memory table; assert the row count after the second write equals the unique-KEY count (no duplication) and that an existing table is dropped-and-rewritten.
  - Acceptance: test asserts no row duplication on re-run and passes.

### Phase 7 — CLI Entry Point & stdout Summary

- [x] [P7-T1] Implement `print_summary(...) -> None` in `src/normalize_le.py`
  - Rule: print source rows, unique keys, output rows, per-month/FY/quarter tie-outs, and first/middle/last output rows to stdout for spot-checking. Use `print` for the CLI summary surface (CLI tool output, not library logging).
  - Acceptance: function emits the documented summary lines to stdout; full type hints; docstring.

- [x] [P7-T2] Implement `main(argv: list[str] | None = None) -> int` in `src/normalize_le.py`
  - Rule: argparse with positional `<input.xlsx>`; `--output` REQUIRED (argparse `required=True`); `--source-sheet` default `"LE-8 + 4"`; `--table-name` default `"LE"`; NO `--output-sheet`, NO CSV branch, NO Excel output. Orchestrate `load_source -> normalize -> validate_tieouts -> write_sqlite -> print_summary`. Return 0 on success; map schema/tie-out `ValueError` to a non-zero return/exit; missing `--output` is handled by argparse `required=True`.
  - Acceptance: function returns 0 on success and a non-zero code on schema/tie-out failure; fully type-annotated; no Excel/CSV output path exists.

- [x] [P7-T3] Add a module entry guard so `python -m src.normalize_le` invokes `main` in `src/normalize_le.py`
  - Rule: `if __name__ == "__main__": raise SystemExit(main())`.
  - Acceptance: `python -m src.normalize_le` dispatches to `main` and propagates its exit code.

- [x] [P7-T4] Add a `main` end-to-end success test using in-memory fixtures in `tests/test_normalize_le.py`
  - Rule: build an in-memory `.xlsx` (BytesIO) and a shareable in-memory SQLite connection; invoke `main` with `--output`/`--table-name`; assert return code 0, the persisted table is readable with the 26 columns and expected row count, and `capsys` captures the stdout summary lines (source rows, unique keys, output rows, tie-outs, first/middle/last rows).
  - Acceptance: test asserts exit 0, persisted schema/row-count, and presence of summary lines; no temp files.

- [x] [P7-T5] Add a `main` missing-`--output` non-zero-exit test in `tests/test_normalize_le.py`
  - Rule: invoke `main` (or the parser) without `--output`; assert a non-zero exit (argparse `SystemExit` with non-zero code).
  - Acceptance: test asserts a non-zero exit when `--output` is absent.

- [x] [P7-T6] Add a `main` schema-mismatch non-zero-exit test in `tests/test_normalize_le.py`
  - Rule: build an in-memory `.xlsx` with a missing/extra/out-of-order column; invoke `main` with valid `--output`; assert a non-zero return/exit and that the message names the offending column(s).
  - Acceptance: test asserts non-zero exit and descriptive column-naming message.

- [x] [P7-T7] Add a `main` custom `--source-sheet` and `--table-name` test in `tests/test_normalize_le.py`
  - Rule: build the in-memory workbook on a non-default sheet name; invoke `main` with custom `--source-sheet` and `--table-name`; assert exit 0 and the persisted table uses the custom name with the 26 columns.
  - Acceptance: test asserts exit 0 and the custom table name is present with correct schema.

### Phase 8 — Final QA Loop, Coverage Delta, and Acceptance Mapping

- [x] [P8-T1] Run Black formatting on the full repository and record the final-QA artifact
  - Command: `poetry run black .`
  - Rerun behavior: if Black reformats any file, restart the loop from this task before proceeding.
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/final-black.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; final state shows no files reformatted.

- [x] [P8-T2] Run Ruff lint on the full repository and record the final-QA artifact
  - Command: `poetry run ruff check .`
  - Rerun behavior: if Ruff applies fixes that change files, restart from P8-T1.
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/final-ruff.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; `EXIT_CODE` is 0 with 0 errors (any suppression matches `.claude/rules/python-suppressions.md` with the required comment format).

- [x] [P8-T3] Run Pyright (strict) on the repository and record the final-QA artifact
  - Command: `poetry run pyright`
  - Rerun behavior: if any fix changes files, restart from P8-T1.
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/final-pyright.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; 0 errors (no narrowed strictness; no unjustified `# type: ignore`).

- [x] [P8-T4] Run Pytest with branch coverage and record the final-QA artifact
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Rerun behavior: if a failure or file change occurs, restart from P8-T1.
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/final-pytest.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including numeric post-change line-coverage % and branch-coverage %; all tests pass; line coverage >= 85% and branch coverage >= 75%.

- [x] [P8-T5] Record a coverage-delta verification artifact comparing baseline to post-change coverage
  - Rule: compare baseline coverage (from P0-T5) to post-change coverage (from P8-T4); report baseline line/branch %, post-change line/branch %, and `src/normalize_le.py` new-code line/branch %; confirm no regression on changed lines and that thresholds (>= 85% line, >= 75% branch) hold.
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/coverage-delta.md` exists with baseline coverage, post-change coverage, and new/changed-code coverage as numeric values (no placeholders); if any threshold or no-regression check fails, the outcome is remediation-required, not PASS.

- [x] [P8-T6] Record an acceptance-criteria mapping artifact tying each issue #2 acceptance criterion to its verifying test(s)
  - Rule: map every acceptance criterion in `issue.md` `## Acceptance Criteria` and every `## Test Conditions` item to the specific test function(s) in `tests/test_normalize_le.py` that verify it (CLI/defaults/required-`--output`; `header=2`/blank-Customer drop/schema validation; `coerce_sku`/KEY rebuild; target column order/one-row-per-KEY/first-appearance; first-row text + summed numerics with blanks as 0; `YTG = sum(May..Dec)`; Super Category/PPG quirk; tie-out validation pass+fail; stdout summary; SQLite persist + replace-if-exists; non-numeric SKU preserved; NaN months as 0; trailing blank rows dropped).
  - Acceptance: `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/acceptance-mapping.md` exists with each criterion mapped to at least one named test; any unmapped criterion makes the outcome remediation-required.

## Test Plan

- Unit: `coerce_sku` (int, np.integer, integer-valued float, non-integer float, NaN, string code); `rebuild_key`; `validate_schema` (missing/extra/out-of-order); `normalize` (singleton, 2-row pair, 3+ rows, NaN-as-0, first-row text, column order, first-appearance order, Super Category/PPG quirk, non-numeric SKU preserved); `compute_ytg`; `validate_tieouts` (pass + 3 failure paths); `load_source` (header=2, blank-Customer drop, KEY rebuild); `print_summary`/`main` stdout via `capsys`.
- Property (hypothesis, T2 >=1 per pure function): `coerce_sku`, `rebuild_key`, `compute_ytg`, `normalize`, `validate_tieouts`.
- Integration: in-memory SQLite round-trip (columns/order/row count read back); replace-if-exists re-run (no duplication); `main` end-to-end success; missing-`--output` non-zero exit; schema-mismatch non-zero exit; custom `--source-sheet`/`--table-name`.
- Coverage evidence:
  - Baseline artifacts: `evidence/baseline/baseline-{black,ruff,pyright,pytest}.md` (Phase 0).
  - Final-QA artifacts: `evidence/qa-gates/final-{black,ruff,pyright,pytest}.md` (Phase 8).
  - Comparison artifact: `evidence/qa-gates/coverage-delta.md` (Phase 8).
  - Acceptance mapping: `evidence/qa-gates/acceptance-mapping.md` (Phase 8).
  - All paths are relative to `docs/features/active/2026-05-25-etl-le-topline-input-2/`.

## Open Questions / Notes

- No `quality-tiers.yml` exists at repo root and the existing `src.calculator` project has no tier entry, so the manifest schema is unestablished. This plan classifies `src/normalize_le.py` as T2 in the header and does not fabricate a repo-wide tier manifest, which is outside the declared touched-file scope (`src/normalize_le.py`, `pyproject.toml`/`poetry.lock`, `tests/test_normalize_le.py`). If repo policy later requires a `quality-tiers.yml` entry, add it as a follow-up.
- Research artifact Q3 (Excel Table via openpyxl) and the CSV branch are SUPERSEDED by the SQLite sink; all other research findings remain valid.
- Per-batch budget respected: production file `src/normalize_le.py` plus `pyproject.toml`/`poetry.lock`, and test file `tests/test_normalize_le.py` — within the 3 production + 3 test file limit.
