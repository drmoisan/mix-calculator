# le-loader-required-vs-output-columns (Spec)

- **Issue:** #57
- **Parent (optional):** #55 (rides in PR #56)
- **Owner:** drmoisan
- **Last Updated:** 2026-06-07
- **Status:** Final
- **Version:** 1.0

## Context
- After header-row detection (#55) resolves the header, importing an LE sheet
  that lacks the intermediate `YTD/YTG` discriminator still fails:
  `ValueError: Source schema mismatch: could not resolve required column(s):
  ['YTD/YTG']`.
- The protected LE loader requires every source column except `KEY`
  (`EXPECTED_COLUMNS = SOURCE_COLUMNS - {KEY}` in `src/_normalize_le_columns.py`),
  including columns that are not part of and never read for the final output.
- Observed: `poetry run mix-pipeline-gui`, Import LE of a flat sheet
  (LE84Data-style: header at row 0, has `YTG`, no `YTD/YTG`, no `KEY`).
- Impact: LE sheets without the `YTD/YTG` discriminator cannot be imported.

## Repro & Evidence
- Steps: Import an LE sheet whose columns are
  `[Customer, SKU Descripiton, SKU #, Type, GtN Mapping, Jan..Dec, FY, Q1..Q4,
  YTG, Super Category, PPG]` (no `YTD/YTG`).
- Actual: `resolve_columns` raises, missing `['YTD/YTG']`.
- Root cause (verified):
  - `YTD/YTG` is in `EXPECTED_COLUMNS` (`_normalize_le_columns.py:90`) but
    `normalize()` (`normalize_le.py:223-265`) never reads it; output is
    `TARGET_COLUMNS`, which excludes it. It is required only to be dropped.
  - Source `Super Category` is required but ignored: `normalize()` sets the
    output `Super Category` from `PPG`
    (`output["Super Category"] = first_rows["PPG"]`, `normalize_le.py:261`);
    the source `Super Category` value is never read.
  - Grep of `src/` confirms `YTD/YTG` and source `Super Category` are not read
    anywhere in `normalize_le.py` executable logic.

## Scope & Non-Goals
- In scope: make the protected LE loader require only the must-have source
  columns and treat `YTD/YTG` and source `Super Category` as optional-by-name
  (carried if present, tolerated if absent), mirroring the pattern AOP already
  uses for `KEY`/`YTG`.
- Out of scope: `load_aop` (already excludes `KEY`/`YTG` and has no
  required-only-to-drop column — confirmed; source `Super Category` IS used in
  AOP); the schema-driven loader (`#54` already handled it via `in_output`);
  header detection (`#55`).

## Root Cause Analysis
- `EXPECTED_COLUMNS` conflates "must be present in source" with "needed for
  output." `YTD/YTG` (dropped) and source `Super Category` (overwritten by PPG)
  are required despite never being read.

## Proposed Fix

### Design summary (mirror the AOP `load_aop` / `_by_name_optional_columns` pattern):
- In `src/_normalize_le_columns.py`:
  - Add `REQUIRED_COLUMNS = TEXT_COLUMNS + [*MONTH_COLUMNS, "FY", *QUARTER_COLUMNS,
    "PPG"]` (23 must-have source columns).
  - Add `OPTIONAL_BY_NAME = ["YTD/YTG", "Super Category"]`.
  - Redefine `EXPECTED_COLUMNS = REQUIRED_COLUMNS` (required-only, matching the
    AOP module convention).
  - Rewrite `resolve_le_columns` to locate each `OPTIONAL_BY_NAME` column by
    normalized name (no fuzzy match, no raise on absence) exactly as `KEY` is
    located; exclude located optionals from the `resolvable` list passed to
    `resolve_columns`; require only `REQUIRED_COLUMNS`; append located optionals
    to `selection` only when found.
- In `src/normalize_le.py`:
  - Update `load_source` to build `columns_to_keep` from `REQUIRED_COLUMNS` plus
    the located optional/`KEY` columns from `selection` (instead of iterating the
    full former `EXPECTED_COLUMNS`), mirroring `load_aop.py:240-246`.
- `normalize()` and `validate_tieouts()` need NO change: they reference only
  `TEXT_COLUMNS`, `SUM_COLUMNS`, `PPG`, and `KEY`; output `Super Category` is
  created from `PPG` regardless of source presence; `TARGET_COLUMNS` still
  excludes `YTD/YTG`.

### Boundaries and invariants to preserve:
- Parity: the standard `LE-8 + 4` source (which HAS `YTD/YTG` and `Super
  Category`) yields byte-identical output — the optionals are located, carried,
  and `YTD/YTG` dropped at emit as today; output `Super Category` = `PPG`.
- A genuine must-have column absent still raises a clear error naming it.
- No change to `load_aop`, the schema loader, or the CLI surface.

### Files/modules to change:
- `src/_normalize_le_columns.py` (constants + `resolve_le_columns`).
- `src/normalize_le.py` (`load_source` selection block only).
- Tests: new/extended unit tests for `resolve_le_columns` optional handling;
  extend `tests/test_normalize_le.py` / `tests/test_normalize_le_header.py`;
  update `tests/test_etl_columns.py` where it passes `EXPECTED_COLUMNS` to
  `resolve_columns` (now 23 columns).

## Test Strategy
- `YTD/YTG` absent -> load_source succeeds; frame lacks `YTD/YTG`.
- Source `Super Category` absent -> load_source succeeds; normalize() output
  `Super Category == PPG`.
- Both absent -> all 26 `TARGET_COLUMNS` produced correctly.
- Both present (parity) -> output identical to current behavior.
- A must-have column absent (e.g. `PPG`, `Customer`, a month) -> raises naming it.
- LE84Data-style flat sheet (header row 0, no `YTD/YTG`, no `KEY`) -> imports to
  `TARGET_COLUMNS`.
- Toolchain: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch`),
  coverage >= 85% line / >= 75% branch, no regression on changed lines.

## Acceptance Criteria
- [x] AC-1: An LE sheet without a `YTD/YTG` column imports successfully (no
      "could not resolve required column(s): ['YTD/YTG']" error).
- [x] AC-2: An LE sheet without a source `Super Category` column imports
      successfully; output `Super Category` is still derived from `PPG`.
- [x] AC-3: The protected LE loader requires only the 23 must-have source columns
      (`Customer`, `SKU Descripiton`, `SKU #`, `Type`, `GtN Mapping`, `Jan`..`Dec`,
      `FY`, `Q1`..`Q4`, `PPG`); `YTD/YTG` and source `Super Category` are optional
      (located by name, carried if present, tolerated if absent).
- [x] AC-4: The standard `LE-8 + 4` source (with `YTD/YTG` + `Super Category`
      present) produces byte-identical output to today (parity; existing LE loader
      tests pass).
- [x] AC-5: A source missing a genuine must-have column raises a clear
      column-resolution error naming the missing column.
- [x] AC-6: A flat LE sheet (header row 0, no `YTD/YTG`, no `KEY`) imports to the
      full `TARGET_COLUMNS` set.
- [x] AC-7: `load_aop` is unchanged; AOP imports unaffected.
- [x] AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage
      >= 85% line / >= 75% branch and no regression on changed lines; all files
      <= 500 lines.

## Risks & Mitigations
- Risk: parity regression for the standard source. Mitigation: optionals are
  located and carried exactly as before; run the full LE loader suite.
- Risk: changing `EXPECTED_COLUMNS` meaning breaks importers/tests. Mitigation:
  update `tests/test_etl_columns.py` usages; grep all `EXPECTED_COLUMNS` importers.
- Risk: a must-have column accidentally made optional. Mitigation: explicit
  REQUIRED_COLUMNS list reviewed against `normalize()`/`validate_tieouts` readers.

## Rollout & Follow-up
- Rides in PR #56 on branch `fix/loader-header-row-detection` so non-standard LE
  import works end-to-end (header detection + must-have columns).
- Links: issue #57; research artifacts/research/le-loader-required-vs-output-columns-57.md.
