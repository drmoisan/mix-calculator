# 2026-05-26-load-aop-sheet — Spec

- **Issue:** #7
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-26T14-03
- **Status:** Draft
- **Version:** 0.1

## Overview

The repository contains the `normalize-le` ETL (`src/normalize_le.py`) over the
`LE-8 + 4` sheet. A sibling ETL is needed for the `AOP1` sheet: load it into a
pandas DataFrame, establish the business KEY, validate per-row totals, and
persist to SQLite. The shared ETL helpers currently carry `le_*` names that
imply LE ownership even though the logic is domain-agnostic; a second consumer
makes the misleading naming a maintenance liability and risks duplicated logic.


## Behavior

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


## Inputs / Outputs

### Inputs

- Source workbook: an `.xlsx` file containing an `AOP1` sheet. The reader path
  accepts a file path or any object `read_excel_sheet` supports (including an
  in-memory `io.BytesIO` workbook for tests).
- Sheet layout (`AOP1`): two leading non-data rows; Excel row 3 is the header
  (read with `header=2`); data rows occupy rows 4..~1956. A trailing `#N/A`
  spill region is removed by the blank-`Customer` filter.
- CLI flags (see API / CLI Surface for full detail): positional `<input.xlsx>`,
  `--output` (required), `--source-sheet`, `--table-name`, `--key-mismatch`,
  `--if-exists`, `--snake-case`.
- API parameters: `source`, `sheet`, `transform`, `key_mismatch`, `is_tty`,
  `prompt` (see API / CLI Surface).
- No environment variables are read.

### Outputs

- An importable `pandas.DataFrame` with canonical column names (original headers
  preserved verbatim, including the intentional `SKU Descripiton` typo, unless
  `--snake-case` is requested).
- A SQLite database file at `--output` containing the target table (default
  `aop`) plus quoted lookup indexes on `KEY`, `Customer`, `SKU #`, and `Type`.
- A human-readable summary on stdout (row count, unique KEYs, customers, SKU #s,
  sorted Types, YTD total, validation status).
- A persistence confirmation line on stdout:
  `Persisted <n> rows to <db_path> (table='<table>')`.
- Warnings routed to `logging` at WARNING level: extra (unexpected) columns,
  trust/overwrite KEY resolution, and duplicate KEYs.

### Config keys and defaults

| Flag | Default | Notes |
|---|---|---|
| `<input.xlsx>` (positional) | required | source workbook path |
| `--output` | required (missing exits non-zero) | SQLite DB path |
| `--source-sheet` | `"AOP1"` | sheet name to read |
| `--table-name` | `"aop"` | target table name |
| `--key-mismatch` | `"prompt"` | one of `prompt`, `trust`, `overwrite` |
| `--if-exists` | `"replace"` | one of `replace`, `append`, `fail` |
| `--snake-case` | off | rename columns before writing when set |

### Versioning / backward-compatibility constraints

- The shared leaf modules are renamed (`le_columns`/`le_key`/`le_totals` ->
  `etl_columns`/`etl_key`/`etl_totals`). The rename must be atomic across `src/`
  and `tests/`; `normalize_le` and the LE test suite must import the new names
  and remain green with no LE behavior change.
- `fill_blank_totals` gains a generalized signature accepting a
  `dict[str, list[str]]` mapping; the LE caller is updated in the same change so
  LE per-row tie-outs continue to pass.
- No new third-party dependencies are introduced.

## API / CLI Surface

### CLI

```
poetry run load-aop <input.xlsx> --output <path.db> \
    [--source-sheet "AOP1"] [--table-name aop] \
    [--key-mismatch {prompt,trust,overwrite}] \
    [--if-exists {replace,append,fail}] [--snake-case]
```

- `main(argv: list[str] | None = None) -> int` returns `0` on success and `1`
  when a column-resolution, KEY-resolution, or validation `ValueError` is
  raised.
- `--output` is required; invoking without it exits non-zero.
- `main` calls `logging.basicConfig(level=logging.WARNING)` exactly once;
  warnings go to logging and the summary goes to stdout via `print`.
- Poetry console-script registration: `load-aop = "src.load_aop:main"` added
  alongside the existing `normalize-le`.

Example invocation and expected stdout:

```
poetry run load-aop data/aop.xlsx --output build/aop.db

Loaded sheet 'AOP1':
  Rows:           1953
  Unique KEYs:    1953
  Customers:      42
  SKU #s:         310
  Types:          ['Base', 'Promo']
  YTD total:      1234567.89
  Validation:     OK
Persisted 1953 rows to build/aop.db (table='aop')
```

### Importable API

```python
load_aop(
    source,
    *,
    sheet="AOP1",
    transform: Callable[[pd.DataFrame], pd.DataFrame] | None = None,
    key_mismatch="prompt",
    is_tty=sys.stdin.isatty,
    prompt=input,
) -> pd.DataFrame
```

- The optional `transform` is applied AFTER validation and BEFORE return.
- `is_tty` and `prompt` are injected to keep KEY-reconcile prompting testable
  without real TTY/stdin.

```python
persist_aop(df, db_path, table="aop", if_exists="replace")
```

### Contracts and validation rules

- Column resolution is position-independent: a position pass first, then fuzzy
  matching on normalized names at threshold `>= 0.85`.
- The optional `KEY` column is located by name only
  (`normalize_name(...) == "key"`), never by fuzzy match, and is excluded from
  the required-column set.
- All non-KEY columns in `EXPECTED_COLUMNS` are required; a missing required
  column halts with a `ValueError`.
- Extra (unexpected) columns are logged as a warning and processing continues.
- KEY is never blindly trusted; it is created/trusted/resolved according to
  `--key-mismatch` via `resolve_key`.
- Per-row total identities are validated with tolerance `1e-6` (see Data &
  State).

## Data & State

### Data flow

1. Read the sheet via `read_excel_sheet(source, sheet_name=sheet, header=2)`.
2. Locate the optional `KEY` column by `normalize_name(...) == "key"` (name
   only) and exclude it from the required set.
3. Resolve remaining required columns with
   `resolve_columns(actual_without_key, EXPECTED_COLUMNS)`; select and rename to
   canonical names. Log any extras as a warning and continue.
4. Drop rows where `Customer` is NaN/blank (removes the trailing `#N/A` spill).
5. Fill blank totals via
   `fill_blank_totals(frame, {"YTD": MONTHS, **QUARTER_TO_MONTHS, "YTG": YTG_MONTHS})`
   — only blank/NaN total cells are filled from the sum of their months.
6. Establish the KEY via
   `resolve_key(frame, key_mismatch, has_key_column=..., is_tty=..., prompt=...)`.
   The AOP KEY `=B&D&F` (Customer & SKU # & Type) is structurally identical to
   the LE key, so `resolve_key` applies unchanged.
7. Coerce numeric columns (`Jan..Dec`, `YTD`, `Q1..Q4`, `YTG`) with
   `pd.to_numeric(..., errors="coerce").fillna(0.0)` BEFORE validation.
8. Clean `Super Category` and `PPG` sentinels (numeric `0`, `"0"`, `"#N/A"`,
   NaN) to `None` via a local helper
   `clean_label_sentinels(frame, ["Super Category", "PPG"])`.
9. Validate (see invariants). On failure, raise a `ValueError` listing all
   failures.
10. Apply the caller-supplied `transform` (if any), then return the DataFrame.
11. On the CLI path, persist via `persist_aop` and print the summary.

### Source schema (sheet AOP1)

Header order below matches the reference workbook only; extraction is
position-independent.

| Col | Name | Type / notes |
|---|---|---|
| A | KEY | text, optional; Excel `=B&D&F`; resolved by name only |
| B | Customer | text |
| C | SKU Descripiton | text; typo intentional, preserved verbatim |
| D | SKU # | mixed int or string code |
| E | Customer Master | text |
| F | Type | text |
| G..R | Jan..Dec | 12 numeric months |
| S | YTD | numeric grand total = SUM(Jan..Dec) |
| T..W | Q1..Q4 | Q1=SUM(Jan..Mar); Q2=SUM(Apr..Jun); Q3=SUM(Jul..Sep); Q4=SUM(Oct..Dec) |
| X | YTG | = SUM(May..Dec) (8+4 convention; present as a source column unlike LE) |
| Y | Super Category | text; may be `0`/`"0"`/`"#N/A"`/NaN |
| Z | PPG | text; same sentinel caveat as Super Category |

KEY is optional; all other columns are required.

### Differences from LE

- AOP has a `Customer Master` column and a source `YTG` column.
- AOP has no YTD/YTG half-marker and no `GtN Mapping`.
- AOP's grand-total column is `YTD` (LE's is `FY`).
- AOP does NOT collapse rows by KEY and does NOT apply the LE
  `Super Category <- PPG` quirk.

### Invariants (validation, tolerance 1e-6)

Validation runs after coercion, before transform, and before persist. It raises
a single `ValueError` listing all failures:

1. At least 1 data row remains after dropping blanks.
2. Per-row identities via `total_vs_months_violations`:
   `YTD == sum(Jan..Dec)`; `Q1..Q4` against their constituent months;
   `YTG == sum(May..Dec)`.
3. Duplicate KEYs WARN only (do not fail), via `logging`.

### Persistence details

- Writes route through `write_table`.
- Quoted lookup indexes are added for `KEY`, `Customer`, `"SKU #"`, and `Type`;
  index names are made safe by replacing space with `_` and `#` with `num`, and
  lowercasing.
- `if_exists` is passed through (`replace`/`append`/`fail`).
- `--snake-case` renames columns before writing to: `sku_num`,
  `sku_description`, `customer_master`, `super_category`, `ppg`, `ytd`, `ytg`,
  `q1..q4`, `jan..dec`, plus `key`, `customer`, `type`. The default preserves
  original headers verbatim (typo included).

### Module constants (AOP-specific)

- `MONTHS = Jan..Dec`
- `YTG_MONTHS = MONTHS[4:]`
- `QUARTER_COLUMNS = Q1..Q4`
- `QUARTER_TO_MONTHS = {q: MONTHS[i*3:i*3+3]}`
- `NUMERIC_COLS = [*MONTHS, "YTD", *QUARTER_COLUMNS, "YTG"]`
- `SOURCE_COLUMNS = [KEY, Customer, "SKU Descripiton", "SKU #", "Customer Master", Type, *MONTHS, YTD, *QUARTER_COLUMNS, YTG, "Super Category", PPG]`
- `EXPECTED_COLUMNS = [c for c in SOURCE_COLUMNS if c != "KEY"]`
- `TARGET_COLUMNS = SOURCE_COLUMNS`

### Migration or backfill requirements

None. The feature adds a new ETL path and a SQLite output; it does not migrate
existing data. The shared-module rename is a code refactor with no data impact.

## Constraints & Risks

- No access to the source workbook; tests use in-memory `io.BytesIO` openpyxl
  workbooks and `sqlite3.connect(":memory:")` round-trips (no temp files).
- Pyright strict: route unknown-typed pandas members through `src/pandas_io.py`
  rather than suppressing.
- Rename must be atomic across `src/` and `tests/` to avoid import breakage.
- Avoid circular imports: both ETLs import only from the neutral leaf modules.


## Implementation Strategy

### Implementation scope

- Add `src/load_aop.py` (Python 3.12+) exposing the CLI and importable API.
  Keep the file under the 500-line limit; if exceeded, extract AOP-specific
  helpers into `src/_load_aop_helpers.py`.
- Reuse the neutral leaf modules without duplication:
  - `src.pandas_io`: `read_excel_sheet`, `write_table`.
  - `src.etl_key`: `coerce_sku`, `rebuild_key`, `decide_key_action`,
    `resolve_key`.
  - `src.etl_columns`: `resolve_columns`, `normalize_name`.
  - `src.etl_totals`: `fill_blank_totals`, `total_vs_months_violations`.
- Refactor the shared leaf modules to neutral names and update `normalize_le.py`
  and LE test imports, with no LE behavior change:
  - `src/le_columns.py` -> `src/etl_columns.py`
  - `src/le_key.py` -> `src/etl_key.py`
  - `src/le_totals.py` -> `src/etl_totals.py`
  - `src/pandas_io.py` stays as-is.
- Generalize `fill_blank_totals` to accept a mapping
  `totals_to_months: dict[str, list[str]]` (total column -> constituent months),
  filling only blank/NaN total cells from the sum of their months. Update
  `normalize_le.load_source` to call it with
  `{"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS}`. AOP calls it with
  `{"YTD": MONTHS, **QUARTER_TO_MONTHS, "YTG": YTG_MONTHS}`.
- Register the Poetry console-script `load-aop = "src.load_aop:main"` alongside
  the existing `normalize-le`.
- Classify the module in `quality-tiers.yml` at repo root as T2-Core
  (consistent with `normalize_le`). The pure-transform core is the rationale for
  T2.

### New classes/functions/commands

- `src/load_aop.py`: `load_aop(...)`, `persist_aop(...)`, `main(argv)`, the local
  helper `clean_label_sentinels(frame, columns)`, and the AOP module constants
  listed under Data & State.
- Generalized `fill_blank_totals(df, totals_to_months)` in `src/etl_totals.py`.

### Dependency changes

- None. Required packages (`pandas`, `openpyxl`) are already present; `numpy` is
  transitive and `sqlite3` is stdlib. No new third-party dependency is added.

### Logging/telemetry additions and locations

- `logging.basicConfig(level=logging.WARNING)` is configured exactly once in
  `main`.
- WARNING-level logging is emitted for: extra/unexpected columns,
  trust/overwrite KEY resolution, and duplicate KEYs.
- The run summary and the persistence confirmation line are written to stdout
  via `print`, not logging.

### Rollout plan

- No feature flags or staged deploys. The change is additive (new ETL path) plus
  an atomic in-repo rename. The fallback path is that the existing
  `normalize-le` ETL is unaffected, which is verified by keeping the LE suite
  green.

### Testing approach

- Add `tests/test_load_aop.py` (transform/validation) and
  `tests/test_load_aop_io.py` (I/O + CLI), using in-memory fixtures only
  (`io.BytesIO` openpyxl workbooks and `sqlite3.connect(":memory:")`); no temp
  files. Reuse `tests/le_fixtures.py` patterns (in-memory connection that
  survives close, injected `is_tty`/`prompt`).
- Cover: position-independent resolution (exact, reordered, fuzzy `>= 0.85`,
  missing-required halt, extras warn-and-continue); KEY branches (assert AOP
  wiring); per-row validation pass/fail; duplicate-KEY warning; sentinel
  cleaning; `--snake-case`; SQLite persist + replace-if-exists round-trip; CLI
  exit codes (missing `--output` non-zero, success zero); a transform callable
  applied after validation; hypothesis property tests where pure functions
  warrant (T2: `>= 1` per pure function).
- Toolchain in order until a clean single pass: `poetry run black .` ->
  `poetry run ruff check .` -> `poetry run pyright` (strict) ->
  `poetry run pytest --cov --cov-branch --cov-report=term-missing`; line
  `>= 85%`, branch `>= 75%`. Route unknown-typed pandas members through
  `src/pandas_io.py` rather than suppressing.

## Definition of Done

- [x] `src/load_aop.py` exposes `load_aop`, `persist_aop`, and `main`; file under 500 lines (AOP helpers extracted to `src/_load_aop_helpers.py` if needed).
- [x] Shared leaves renamed to `etl_columns`, `etl_key`, `etl_totals`; `normalize_le` and LE tests import the new names; LE suite stays green.
- [x] `fill_blank_totals` accepts a `dict[str, list[str]]` totals->months mapping; LE per-row tie-outs still pass; AOP calls it with `{"YTD": MONTHS, **QUARTER_TO_MONTHS, "YTG": YTG_MONTHS}`.
- [x] `load_aop` reuses `coerce_sku`, `rebuild_key`, `decide_key_action`, `resolve_key`, `resolve_columns`, `normalize_name`, `fill_blank_totals`, `total_vs_months_violations`, and the `pandas_io` read/write boundary (no re-implementation).
- [x] Position-independent resolution: exact, reordered, fuzzy >= 0.85, missing-required halt, extras warn-and-continue; optional KEY located by name only.
- [x] Per-row validation for `YTD`, `Q1..Q4`, `YTG` against their months (tol 1e-6); row-count >= 1; duplicate KEYs warn (not fail); failures raised as a single `ValueError` listing all failures.
- [x] Numeric columns coerced via `pd.to_numeric(..., errors="coerce").fillna(0.0)` before validation; `Super Category`/`PPG` sentinels (`0`, `"0"`, `"#N/A"`, NaN) cleaned to `None`; AOP does not apply the LE `Super Category <- PPG` quirk and does not collapse rows.
- [x] CLI: `--output` required (missing exits non-zero); `--source-sheet`/`--table-name`/`--key-mismatch`/`--if-exists`/`--snake-case` defaults per spec; `main` returns 0 success / 1 on resolution/KEY/validation `ValueError`; `logging.basicConfig(level=logging.WARNING)` configured once; summary printed to stdout.
- [x] SQLite persist routes through `write_table`, adds quoted lowercase lookup indexes for KEY/Customer/`SKU #`/Type (space->`_`, `#`->`num`), passes `if_exists` through, and `--if-exists replace` round-trips with no row duplication; `--snake-case` renames columns before writing.
- [x] Poetry console-script `load-aop = "src.load_aop:main"` registered; module tier-classified T2-Core in `quality-tiers.yml`.
- [x] Tests added (`tests/test_load_aop.py`, `tests/test_load_aop_io.py`) using in-memory fixtures only (no temp files); edge cases and error handling covered.
- [x] Full toolchain green in a single pass: Black, Ruff, Pyright (strict), Pytest with line >= 85% / branch >= 75%; no new third-party dependency.

## Seeded Test Conditions (from potential)
- [x] Unit coverage: resolution branches, validation pass/fail, sentinel cleaning, KEY branches, transform-after-validation, `--snake-case`.
- [x] Integration scenarios: SQLite persist + replace-if-exists round-trip via in-memory connection.
- [x] CLI/API examples: missing `--output` non-zero; success zero; importable `load_aop`/`persist_aop`.
- [x] Property tests (T2: >= 1 per pure function) where pure functions warrant.
