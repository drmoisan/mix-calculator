# load-aop-sheet (Issue #7)

- Date captured: 2026-05-26
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/load-aop-sheet/ (Issue #7)

- Issue: #7
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/7
- Last Updated: 2026-05-26
- Work Mode: full-feature

## Problem / Why

The repository contains the `normalize-le` ETL (`src/normalize_le.py`) over the
`LE-8 + 4` sheet. A sibling ETL is needed for the `AOP1` sheet: load it into a
pandas DataFrame, establish the business KEY, validate per-row totals, and
persist to SQLite. The shared ETL helpers currently carry `le_*` names that
imply LE ownership even though the logic is domain-agnostic; a second consumer
makes the misleading naming a maintenance liability and risks duplicated logic.

## Proposed Behavior

Add `src/load_aop.py` exposing both a CLI (`load-aop`) and an importable API
(`load_aop`, `persist_aop`). It resolves the documented `AOP1` schema
position-independently (position pass then fuzzy >= 0.85), establishes the KEY
via the shared reconcile policy, optionally applies a caller-supplied
transform, validates per-row total identities, and writes to a SQLite table
with lookup indexes.

Refactor the shared leaf modules to neutral names so both ETLs depend on a
clean diamond:

- `src/le_columns.py` -> `src/etl_columns.py`
- `src/le_key.py` -> `src/etl_key.py`
- `src/le_totals.py` -> `src/etl_totals.py`
- `src/pandas_io.py` unchanged.

Generalize `fill_blank_totals` to accept a `dict[str, list[str]]` mapping of
total column -> constituent months (replacing the FY-hardcoded signature), and
update `normalize_le` to call it with `{"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS}`
with no LE behavior change.

## Acceptance Criteria (early draft)

- [x] `src/load_aop.py` exposes `load_aop`, `persist_aop`, and `main`; file under 500 lines (AOP helpers extracted to `src/_load_aop_helpers.py` if needed).
- [x] Shared leaves renamed to `etl_columns`, `etl_key`, `etl_totals`; `normalize_le` and LE tests import the new names; LE suite stays green.
- [x] `fill_blank_totals` accepts a `dict[str, list[str]]` totals->months mapping; LE per-row tie-outs still pass.
- [x] `load_aop` reuses `coerce_sku`, `rebuild_key`, `resolve_key`, `resolve_columns`, `normalize_name`, `fill_blank_totals`, `total_vs_months_violations`, and the `pandas_io` read/write boundary (no re-implementation).
- [x] Position-independent resolution: exact, reordered, fuzzy >= 0.85, missing-required halt, extras warn-and-continue.
- [x] Per-row validation for `YTD`, `Q1..Q4`, `YTG` against their months (tol 1e-6); row-count >= 1; duplicate KEYs warn (not fail).
- [x] `Super Category`/`PPG` sentinels (`0`, `"0"`, `"#N/A"`, NaN) cleaned to `None`; AOP does not apply the LE `Super Category <- PPG` quirk and does not collapse rows.
- [x] CLI: `--output` required (missing exits non-zero), `--source-sheet`/`--table-name`/`--key-mismatch`/`--if-exists`/`--snake-case` defaults per spec; `main` returns 0 success / 1 on resolution/KEY/validation `ValueError`.
- [x] SQLite persist routes through `write_table`, adds quoted lookup indexes, and `--if-exists replace` round-trips with no row duplication.
- [x] Poetry console-script `load-aop = "src.load_aop:main"` registered; module tier-classified (T2-Core).
- [x] Full toolchain green: Black, Ruff, Pyright (strict), Pytest with line >= 85% / branch >= 75%; no new third-party dependency.

## Constraints & Risks

- No access to the source workbook; tests use in-memory `io.BytesIO` openpyxl
  workbooks and `sqlite3.connect(":memory:")` round-trips (no temp files).
- Pyright strict: route unknown-typed pandas members through `src/pandas_io.py`
  rather than suppressing.
- Rename must be atomic across `src/` and `tests/` to avoid import breakage.
- Avoid circular imports: both ETLs import only from the neutral leaf modules.

## Test Conditions to Consider

- [x] Unit coverage: resolution branches, validation pass/fail, sentinel cleaning, KEY branches, transform-after-validation, `--snake-case`.
- [x] Integration scenarios: SQLite persist + replace-if-exists round-trip via in-memory connection.
- [x] CLI/API examples: missing `--output` non-zero; success zero; importable `load_aop`/`persist_aop`.
- [x] Property tests (T2: >= 1 per pure function) where pure functions warrant.

## Next Step

- [x] Promote to GitHub issue (feature request template)
- [x] Create `docs/features/active/load-aop-sheet/` folder from the template