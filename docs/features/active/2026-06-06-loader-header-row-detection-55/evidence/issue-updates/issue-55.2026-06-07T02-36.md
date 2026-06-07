# Issue #55 Update Mirror

Timestamp: 2026-06-07T02-36
PostedAs: unknown

POSTING BLOCKED: The executor does not post to GitHub; the orchestrator handles
git and review per the execution directive. This mirror records the intended
outcome text; the local `issue.md` and `spec.md` have been updated in place with
the same outcome and the AC checklist (AC-1..AC-8) checked off.

## Intended update text

Issue #55 (loader header-row detection) implemented on branch
`fix/loader-header-row-detection`.

- Added `src/_header_detection.detect_header_row`: two-read probe (`header=None`),
  normalized-token scoring via `etl_columns.normalize_name`, topmost-highest-score
  selection with a `min_match` floor, BytesIO rewind, deterministic. ValueError
  naming the sheet and expected columns when no row qualifies.
- Wired into `normalize_le.load_source` (LE `min_match=20` of 25 tokens) and
  `load_aop.load_aop` (AOP `min_match=17` of 24 tokens), replacing the hardcoded
  `header=2`.
- Widened `read_excel_sheet`/`_PandasReaders.read_excel` `header` to `int | None`.
- Tests: `tests/test_header_detection.py` (6), plus flat-sheet parity tests in
  new sibling modules `tests/test_normalize_le_header.py` and
  `tests/test_load_aop_header.py`.
- Parity preserved: 53 pre-existing LE/AOP loader tests pass; standard sheets
  still detect header index 2 with unchanged output.
- Final toolchain: Black clean, Ruff 0, Pyright 0, Pytest 976 passed; line 98%,
  branch ~93.9%; 0 missed changed statements. AC-1..AC-8 all PASS.
- No deviations from scope.
