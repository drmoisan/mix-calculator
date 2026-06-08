# loader-header-row-detection (Spec)

- **Issue:** #55
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-06
- **Status:** Final
- **Version:** 1.0

## Context
- The GUI LE/AOP import fails with a column-resolution error when the source
  sheet's header is not on Excel row 3 (zero-based index 2). The protected
  loaders hardcode `read_excel_sheet(..., header=2)`, so a sheet whose header is
  on a different row is read with a data row as the header.
- Observed environment: `poetry run mix-pipeline-gui`, importing an LE source.
- Impact: import cannot complete for any LE/AOP sheet whose header is not on row
  index 2 (deterministic).
- First observed: 2026-06-06 on main. The hardcoded `header=2` predates the
  schema-builder work; the bug is pre-existing.

## Repro & Evidence
- Steps: launch the GUI, select an LE workbook/sheet whose header is on Excel
  row 1 (index 0), click Import (LE).
- Expected vs actual: expected the columns to resolve and the import to proceed;
  actual is `ValueError: Source schema mismatch: could not resolve required
  column(s): [...]. Actual columns: ['Able Sales Company33105Gross Sales',
  'Able Sales Company', ...]` — the "actual columns" are data values (pandas
  `.1`/`.2` dedup suffixes on repeated numbers), proving a data row was read as
  the header.
- Determinism: always, when the header is not on index 2.
- Probe (artifacts/*.xlsx, 2026-06-06): `LE-8 + 4`/`AOP1`/`GS YTD April + YTG 5.8`
  -> header at index 2; flat `LE84Data` -> header at index 0.

## Scope & Non-Goals
- In scope: replace the hardcoded `header=2` in `src/normalize_le.load_source`
  and `src/load_aop.load_aop` with header-row detection; a shared detection
  helper; widen `read_excel_sheet`'s `header` parameter to accept `None` for the
  probe read.
- Out of scope: the schema-driven reader path (`SchemaLoader` receives a
  pre-read frame; it does not call `read_excel_sheet`); the GUI `pipeline_service`
  (it delegates to the loaders and benefits automatically); `load_skulu`
  (already `header=0`, correct); the pre-existing `header_row:0` vs `header=2`
  documentation divergence in the bundled schemas.

## Root Cause Analysis
- Confirmed root cause: `src/normalize_le.py:142` and `src/load_aop.py:184` call
  `read_excel_sheet(..., header=2)` unconditionally. A sheet whose header is not
  on index 2 yields a data row as the column header, so `resolve_columns` fails.
- Affected components: `src/normalize_le.py`, `src/load_aop.py`,
  `src/pandas_io.py` (header param type), and the GUI import path that calls
  them.

## Proposed Fix

### Design summary (what changes where):
- Add `src/_header_detection.py` with a deterministic `detect_header_row` helper.
- `normalize_le.load_source` and `load_aop.load_aop` detect the header row, then
  read with the detected index instead of `header=2`.
- `read_excel_sheet`'s `header` parameter is widened to `int | None` so the
  detection helper can take a `header=None` probe read.

### Boundaries and invariants to preserve:
- Loader parity: for the standard sheets and existing fixtures (header at index
  2), detection MUST select index 2 so outputs are byte-identical to today.
- No change to the pure transform functions or to `load_skulu`.
- Detection is deterministic (no wall-clock, no randomness).

### Dependencies or blocked work:
- None. Branches off main (PR #51 / issues #50, #54 already merged).

### Implementation strategy (what changes, not sequencing):

#### Files/modules to change:
- New `src/_header_detection.py` — `detect_header_row(source, sheet_name,
  expected_tokens, *, max_rows=5, min_match)`.
- `src/pandas_io.py` — widen `read_excel_sheet` `header: int` to `int | None`
  (and the Protocol).
- `src/normalize_le.py` — detect then read (replace the line-142 hardcode).
- `src/load_aop.py` — detect then read (replace the line-184 hardcode).

#### Functions/classes/CLI commands impacted:
- `normalize_le.load_source`, `load_aop.load_aop`, `pandas_io.read_excel_sheet`.
- New `_header_detection.detect_header_row`.
- CLI: unchanged surface; both loaders gain robustness transparently.

#### Data flow and validation changes:
- Two-read approach: probe read with `header=None`, score each of the first
  `max_rows` rows by the count of normalized (`etl_columns.normalize_name`)
  expected tokens present, select the topmost row with the highest score that
  meets `min_match`, then read the final frame with that header index. BytesIO
  sources are rewound between reads.
- Scoring rejects data rows: numeric cells normalize to non-token strings, so a
  genuine data row scores below `min_match`.

#### Error handling and logging updates:
- No qualifying header row within `max_rows` raises a clear `ValueError` naming
  the sheet and the expected columns (no silent fallback to `header=2`).

#### Rollback/feature-flag considerations:
- None; behavior for header-at-index-2 sheets is unchanged.

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:
- `detect_header_row(source, sheet_name, expected_tokens: frozenset[str], *,
  max_rows: int = 5, min_match: int) -> int` returns the zero-based header index.
- LE expected tokens = normalized `EXPECTED_COLUMNS` (25); AOP = normalized
  `EXPECTED_COLUMNS` (24). `min_match` set to a high fraction of the token count
  (LE 20 of 25, AOP 17 of 24) to reject data rows while tolerating a few label
  diffs; the planner finalizes the exact thresholds with the fixtures in view.

#### Required configuration keys and defaults:
- None.

#### Backward-compatibility expectations:
- Header-at-index-2 sheets unchanged. `read_excel_sheet(header=2)` callers
  (parity tests) unaffected by the widened type.

#### Performance constraints:
- One extra bounded read of the top `max_rows` rows per import; negligible.

## Assumptions, Constraints, Dependencies
- Assumptions: a valid LE/AOP source has a header row containing (almost) all
  expected canonical column labels within the first `max_rows` rows.
- Constraints: 500-line file cap (all edited files well under); Pyright-clean;
  no new dependencies; coverage >= 85% line / >= 75% branch on changed lines.
- External dependencies: pandas/openpyxl (already present).

## Data / API / Config Impact
- User-facing: LE/AOP import now works for sheets with the header on any of the
  first few rows; clearer error when no header is found.
- Migration: none.
- Logging: optionally log the detected header index at debug.
- Compatibility: CLI flags/config unchanged.

## Test Strategy
- New `tests/test_header_detection.py`: detect header at index 0; at index 2;
  with 3 leading rows (index 3); no-match raises ValueError; a data row with a
  few coincidental tokens does NOT cross the threshold.
- LE/AOP fixtures (`tests/le_fixtures.py`, `tests/aop_fixtures.py`): add a
  flat-workbook builder (header at index 0) without breaking the existing
  header-at-index-2 builders.
- `tests/test_normalize_le.py` / `tests/test_load_aop.py`: add a flat-sheet
  `load_source`/`load_aop` test that resolves columns and matches the
  header-at-index-2 output for equivalent data; confirm existing tests still pass
  (parity).
- Toolchain: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch`),
  coverage >= 85% line / >= 75% branch, no regression on changed lines.

## Acceptance Criteria
- [x] AC-1: Importing an LE sheet whose header is on Excel row 1 (index 0)
      resolves columns and completes without the "Source schema mismatch" error.
- [x] AC-2: The standard `LE-8 + 4` and `AOP1` sheets (header at index 2) still
      load correctly; detection selects index 2 and loader output is unchanged
      (parity preserved; existing LE/AOP loader tests pass).
- [x] AC-3: Header detection is shared between the LE and AOP loaders via a
      single helper.
- [x] AC-4: A sheet with no resolvable header row within the scan window raises
      a clear `ValueError` naming the sheet and the expected columns (no silent
      fallback).
- [x] AC-5: Detection is deterministic and rejects a data row that coincidentally
      contains a few expected tokens (threshold guard).
- [x] AC-6: `read_excel_sheet` accepts `header=None` for the probe read; existing
      `header=2` callers are unaffected.
- [x] AC-7: All changed/added files remain <= 500 lines.
- [x] AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Outcome (implemented 2026-06-07)
- Added `src/_header_detection.detect_header_row` (two-read probe with
  `header=None`, normalized-token scoring via `etl_columns.normalize_name`,
  topmost-highest-score selection with a `min_match` floor, BytesIO rewind,
  deterministic). Both `normalize_le.load_source` and `load_aop.load_aop` wire it
  in, replacing the hardcoded `header=2`.
- Finalized thresholds: LE `min_match=20` of 25 expected tokens; AOP
  `min_match=17` of 24 expected tokens. The AOP token count is 24 (verified
  against `src._load_aop_helpers.EXPECTED_COLUMNS`).
- `read_excel_sheet` (and its `_PandasReaders` Protocol) widened to
  `header: int | None`.
- Tests added: `tests/test_header_detection.py` (6 unit tests), and flat-sheet
  parity tests in new sibling modules `tests/test_normalize_le_header.py` and
  `tests/test_load_aop_header.py` (placed there to keep the 446- and 494-line
  pre-existing test files under the 500-line cap).
- Final toolchain: Black clean, Ruff 0 errors, Pyright 0 errors, Pytest 976
  passed (was 966); total line coverage 98%, branch ~93.9%; all four changed
  modules at 97-100% with 0 missed changed statements. No deviations from scope.

## Risks & Mitigations
- Risk: detection false-positive on a data row. Mitigation: high `min_match`
  threshold; topmost-highest selection; explicit edge-case test.
- Risk: parity regression for header-at-index-2 sheets. Mitigation: detection
  provably selects index 2 for existing fixtures; run the full LE/AOP suites.
- Risk: BytesIO not rewound between probe and final read. Mitigation: helper
  rewinds; test by importing twice from one buffer.

## Rollout & Follow-up
- Rollout: standard PR to main with green CI.
- Follow-up (not in scope): reconcile the bundled schemas' `header_row:0` with
  the detected header for the schema-driven path.
- Links: issue #55; research artifacts/research/loader-header-row-detection-55.md.
