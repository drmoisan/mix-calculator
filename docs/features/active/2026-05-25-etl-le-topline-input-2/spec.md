# etl-le-topline-input — Spec

- **Issue:** #2
- **Parent (optional):** n/a
- **Owner:** Dan Moisan
- **Last Updated:** 2026-05-26T00-00
- **Status:** Draft
- **Version:** 0.1.0

## Overview

A single-file Python CLI that normalizes an Excel "LE" (Latest Estimate) topline
planning workbook into one row per business key, reproducing an as-built in-workbook
Excel formula chain exactly — including a known quirk that must be preserved rather
than corrected.

- Target users/personas and primary use cases: FP&A analysts who run the script
  monthly against the LE planning workbook to produce a normalized table persisted
  to a SQLite database for downstream analysis, replacing a fragile chain of
  `XLOOKUP`/`SUMIF`/key-concatenation formulas with an auditable, repeatable,
  version-controllable transform.
- Success metrics or expected impact: deterministic, fail-fast normalization whose
  per-column source/output tie-outs match within `1e-6`; the manual formula chain is
  no longer required to produce the normalized output.

## Behavior

End-to-end, the tool loads the source sheet, resolves the source columns to the
expected schema by position then fuzzy match, establishes the business key, collapses
rows by key, derives the `YTG` measure, validates tie-outs, persists the result to
SQLite, and prints a tie-out summary.

- Column resolution (position-independent): extraction does not require the source
  columns to be in their documented positions. Each expected column is resolved as
  follows:
  - Position pass: for each expected column, bind the actual column at the same index
    when its name equals the expected name after normalization (case-folded, with
    spaces and punctuation removed).
  - Fuzzy pass: for each still-unbound expected column, match it against the remaining
    unbound actual columns by normalized equality first, then by a
    `difflib.SequenceMatcher` similarity score on normalized names with a threshold of
    `>= 0.85`.
  - Missing: if any required expected column remains unmatched after the fuzzy pass,
    the run halts with a clear error naming the unmatched expected column(s).
  - Extras: if every required expected column is matched but unmatched actual columns
    remain, a warning naming the extra column(s) is logged via the Python stdlib
    `logging` module and the run continues.
  - After resolution the working frame is selected and renamed to the canonical
    expected names; all downstream logic uses canonical names regardless of source
    order. `KEY` is optional in the source and is resolved by name only (no fuzzy
    match), then handled per KEY handling below.
- KEY handling: `KEY` is established from one of three branches.
  - Absent: when the source has no `KEY` column, create it as
    `Customer + coerce_sku(SKU #) + Type`.
  - Present and matching: when a `KEY` column is present and every value equals that
    rebuilt pattern, trust and keep the existing column.
  - Present and diverging: when a `KEY` column is present but one or more values do not
    match the rebuilt pattern, resolve per `--key-mismatch`:
    - `trust`: keep the existing `KEY` values; log a warning.
    - `overwrite`: replace `KEY` with the rebuilt pattern; log a warning.
    - `prompt` (default): when stdin is an interactive TTY, ask the user to choose
      trust or overwrite; when stdin is not interactive (automation/CI), do not block —
      fail fast with a non-zero exit instructing the caller to pass
      `--key-mismatch trust|overwrite`.
- Main user flow (happy path): a workbook whose columns resolve to the documented
  source schema is loaded (Excel row 3 as header, data from row 4); rows with blank
  `Customer` are dropped; columns are resolved and renamed to canonical names; blank
  `FY`/`Q1..Q4` totals are filled from their monthly components (`FY <- sum(Jan..Dec)`,
  `Qn <- sum(its months)`; populated totals untouched, NaN months count as 0); `KEY`
  is established per KEY handling; all rows sharing a `KEY` collapse into one row (text
  from the first matching row, numeric columns summed); the `YTD/YTG` column is dropped
  and a derived `YTG = sum(May..Dec)` is added after `Q4`; all transformations occur in
  a single in-memory pandas DataFrame (no intermediate spreadsheet output); the
  26-column normalized DataFrame is persisted to the SQLite database at `--output`, into
  the table named per `--table-name`, via `to_sql(..., if_exists="replace", index=False)`;
  a validation/tie-out summary is printed to stdout; the process exits zero.
- Alternate/edge flows:
  - Reordered or slightly renamed columns: a workbook whose columns are shuffled or
    contain a minor typo/variant still resolves via the position and fuzzy passes and
    proceeds normally.
  - Extra source columns: when all required columns are matched but extra actual
    columns remain, the extras are logged as a warning and the run continues.
  - KEY branches: a source with no `KEY` column has `KEY` created; a present-and-matching
    `KEY` is trusted; a present-and-diverging `KEY` is resolved per `--key-mismatch`.
  - Replace-existing-table: if a table of the same name already exists in the
    destination SQLite database, `to_sql(if_exists="replace", ...)` drops and rewrites
    it before persisting the new rows; re-running against an existing table produces no
    row duplication.
  - Singleton key passes through unchanged; a key appearing 3+ times sums all matching
    rows; NaN month cells are treated as 0; first-appearance order is preserved with no
    alphabetical or KEY sorting.
- Error handling and recovery behavior:
  - Missing `--output`: the CLI does not provide a default output path; invocation
    without `--output` exits non-zero.
  - Unmatched required column: if a required expected column cannot be bound after the
    position and fuzzy passes, the run halts with a clear error naming the unmatched
    expected column(s) and exits non-zero.
  - Diverging `KEY` under `--key-mismatch prompt` with a non-interactive stdin: the run
    fails fast with a non-zero exit and guidance to pass `--key-mismatch trust|overwrite`;
    it does not block waiting on input.
  - Tie-out failure (output-row-count != unique keys, any per-column source/output
    tie-out outside `1e-6`, or `FY != sum(months)` on any row) raises and exits
    non-zero.
  - Errors are surfaced fail-fast via `ValueError` (or a dedicated exception subclass)
    rather than silently ignored; warnings (extra columns, trust/overwrite resolution)
    are emitted via `logging` to stderr; `main` maps the failure to a non-zero exit code.

## Inputs / Outputs

- Inputs (CLI flags, files, env vars):
  - Positional `<input.xlsx>` — path to the source Excel workbook.
  - `--output <path.db>` — REQUIRED; destination path to a SQLite database file
    (e.g. `.db`/`.sqlite`). There is no default; a missing `--output` exits non-zero.
  - `--source-sheet <name>` — source worksheet name.
  - `--table-name <name>` — name of the SQLite table to persist.
  - `--key-mismatch {prompt,trust,overwrite}` — how to resolve a present `KEY` column
    whose values diverge from the rebuilt pattern (default `prompt`).
- Outputs (artifacts, logs, telemetry):
  - SQLite: a table named per `--table-name` in the database at `--output`, containing
    the 26 target columns in exact order, one row per unique KEY.
  - stdout: tie-out summary (source rows, unique keys, output rows, per-month/FY/
    quarter tie-outs, and first/middle/last output rows for spot-checking).
  - stderr: `logging`-based warnings for extra source columns and for `trust`/`overwrite`
    KEY resolution, in addition to the stdout tie-out summary.
  - Exit code: zero on success; non-zero on missing `--output`, an unmatched required
    column, a non-interactive `--key-mismatch prompt` with a diverging `KEY`, or a
    tie-out failure.
- Config keys and defaults:
  - `--source-sheet` default `"LE-8 + 4"`.
  - `--table-name` default `LE`.
  - `--key-mismatch` default `prompt` (alternatives `trust`, `overwrite`).
  - `--output` is REQUIRED and has no default; it must point at a SQLite database file.
- Versioning or backward-compatibility constraints: the source and target schemas are
  fixed 26-column contracts in exact A..Z order; the header typo `SKU Descripiton` is
  preserved verbatim in both schemas.

## API / CLI Surface

Invocation (Poetry console-script entry point `normalize-le`, declared under
`[tool.poetry.scripts]`):

```
poetry run normalize-le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE] \
  [--key-mismatch {prompt,trust,overwrite}]
```

Public functions (per the research module layout):

- `coerce_sku(val) -> str` — Excel-compatible SKU coercion: whole-number SKUs render as
  integer strings (no decimals/separators); non-numeric codes preserved verbatim.
- `rebuild_key(customer, sku, type_) -> str` — concatenates `Customer + coerce_sku(SKU #)
  + Type` with no separator.
- `resolve_columns(actual, expected) -> mapping/extras` — pure resolver: binds each
  expected column to an actual column by the position pass (normalized name equality at
  the same index) then the fuzzy pass (normalized equality, then
  `difflib.SequenceMatcher` similarity `>= 0.85` on normalized names); raises naming the
  unmatched required expected column(s) when any cannot be bound; returns the resolved
  mapping and the list of extra unmatched actual columns (logged as a warning by the
  caller).
- `resolve_key(df, policy, *, interactive) -> df` — establishes `KEY` on the
  canonical-named frame: creates it from the rebuilt pattern when absent; trusts it when
  present and every value matches the rebuilt pattern; otherwise resolves a divergence
  per `policy` (`trust`/`overwrite` log a warning; `prompt` asks when `interactive` is
  true and fails fast with a non-zero-exit error when it is not). `KEY` is resolved by
  name only — no fuzzy matching is applied to `KEY`.
- `load_source(path, sheet_name, ...) -> pd.DataFrame` — I/O boundary; reads with
  `header=2`, drops blank-`Customer` rows, calls `resolve_columns` and selects/renames
  the frame to the canonical expected names so all downstream logic uses canonical names.
- `normalize(df) -> pd.DataFrame` — pure transform: collapse by KEY, build target
  schema.
- `compute_ytg(df) -> pd.Series` — derived `YTG = sum(May..Dec)` on the output row.
- `validate_tieouts(source_df, output_df) -> None` — enforces row-count, per-column
  tie-outs within `1e-6`, `FY == sum(months)`, and `Qn == sum(its months)` per row;
  raises on failure.
- `fill_blank_totals(df, ...) -> pd.DataFrame` — fills only blank (`NaN`) `FY`/quarter
  cells with the sum of their constituent months; populated totals are left unchanged.
- `write_sqlite(df, dest, table_name) -> None` — I/O boundary; persists the normalized
  DataFrame to the SQLite database at `dest` via
  `df.to_sql(table_name, conn, if_exists="replace", index=False)`.
- `main(argv: list[str] | None = None) -> int` — CLI entry point returning an exit code.

- Example invocations with expected outputs (concise):
  - `poetry run normalize-le book.xlsx --output le.db` — persists table `LE` to
    `le.db`, prints tie-out summary, exits 0.
  - `poetry run normalize-le book.xlsx` (no `--output`) — exits non-zero (output is
    required).
  - `poetry run normalize-le bad.xlsx --output le.db` (a required column cannot be
    resolved) — names the unmatched expected column(s) and exits non-zero.
  - `poetry run normalize-le book.xlsx --output le.db --key-mismatch overwrite` (a
    present `KEY` diverges) — replaces `KEY` with the rebuilt pattern, logs a warning to
    stderr, and exits 0.
- Contracts and validation rules: `--output` is required and must be a SQLite database
  path. Column resolution is position-independent (position pass, then fuzzy pass with a
  `>= 0.85` threshold); a required column that cannot be bound halts the run. `KEY` is
  resolved by name only and handled per `--key-mismatch`. The literal column headers
  (including the space in `SKU Descripiton` and the `#` in `SKU #`) and the table name
  are preserved as-is; pandas `to_sql` quotes column names so they round-trip without
  modification. Tie-outs are validated as described above.

## Data & State

This feature introduces a pure data transform that reads an Excel workbook and
persists the normalized result to a SQLite database with no persistent state beyond
the written table.

- Source schema — sheet `LE-8 + 4`, two leading non-data rows, Excel row 3 is the
  header, data from row 4. The header order below is the canonical reference for
  matching; extraction does not require columns to be in these exact positions (see the
  Column resolution flow in Behavior). `KEY` is optional in the source; every other
  listed column is required.

  | Col | Header | Type | Notes |
  |-----|--------|------|-------|
  | A | `KEY` | text | Optional; Excel `=C&E&F`. Created when absent; trusted when its values match the rebuilt pattern; otherwise resolved per `--key-mismatch`. Resolved by name only (no fuzzy). |
  | B | `YTD/YTG` | text | `"YTD"` or `"YTG"`; not part of the key. |
  | C | `Customer` | text | |
  | D | `SKU Descripiton` | text | Typo intentional; preserve verbatim. |
  | E | `SKU #` | mixed | Usually integer; sometimes a string code. |
  | F | `Type` | text | e.g. `Gross Sales`, `Off Invoice`, `PPD`, `Lbs`. |
  | G | `GtN Mapping` | text | Roll-up label. |
  | H–S | `Jan`..`Dec` | numeric | 12 monthly value columns. |
  | T | `FY` | numeric | SUM(H:S) per row. |
  | U | `Q1` | numeric | SUM(Jan-Mar). |
  | V | `Q2` | numeric | SUM(Apr-Jun). |
  | W | `Q3` | numeric | SUM(Jul-Sep). |
  | X | `Q4` | numeric | SUM(Oct-Dec). |
  | Y | `Super Category` | text | |
  | Z | `PPG` | text | |

- Target schema — SQLite table (default name `LE`), 26 columns A..Z in exact order:

  ```
  KEY, Customer, SKU Descripiton, SKU #, Type, GtN Mapping,
  Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
  FY, Q1, Q2, Q3, Q4, YTG, Super Category, PPG
  ```

  `YTD/YTG` is dropped; derived `YTG` is added after `Q4`, before `Super Category`.

- Persistence invariant: the normalized DataFrame is persisted with
  `to_sql(table_name, conn, if_exists="replace", index=False)`. The row index is not
  persisted; an existing table of the same name is dropped and rewritten; the 26 target
  columns are persisted in exact order, one row per unique KEY.

- Data transformations and invariants:
  - Column-resolution + canonical-rename invariant: source columns are bound to expected
    columns by the position pass then the fuzzy pass (`difflib` similarity `>= 0.85` on
    normalized names); the working frame is then selected and renamed to the canonical
    expected names, so every downstream transform operates on canonical names regardless
    of source column order. A required column that cannot be bound halts the run; extra
    unmatched actual columns are logged and dropped from the working frame.
  - KEY optional/derived invariant: `KEY` is not a trusted source column. It is created
    from `Customer + coerce_sku(SKU #) + Type` when absent, trusted when present and all
    values match that rebuilt pattern, and otherwise resolved per `--key-mismatch`
    (`trust`/`overwrite`/`prompt`, with the non-interactive `prompt` path failing fast).
  - Collapse-by-KEY: text columns taken from the first matching source row per KEY;
    `Jan..Dec`, `FY`, `Q1..Q4` summed across all rows sharing a KEY (blanks treated as 0,
    `groupby(sort=False)` with default `min_count=0`).
  - Super Category <- PPG quirk: both `Super Category` and `PPG` output columns are
    populated from the source `PPG` column and are identical per row. This is an
    invariant to preserve, not a defect to correct.
  - Float64 no-rounding invariant: numeric values preserve float64 precision; no rounding
    is applied; tie-outs use a `1e-6` tolerance.
  - First-appearance ordering invariant: one row per unique KEY in first-appearance order;
    no alphabetical or KEY sorting.
- Caching or persistence details: the only persisted artifact is the SQLite table at
  `--output`; an existing table of the same name is replaced on each run.
- Migration or backfill requirements (if any): none.

## Constraints & Risks

- Limits and acceptable trade-offs:
  - The source workbook is unavailable during development; the script is built to the
    documented schema contract and validated with synthetic in-memory fixtures.
  - Temp files are prohibited in tests; the Excel read fixture uses in-memory
    `io.BytesIO` for `pd.read_excel`, and the SQLite persist round-trip uses an
    in-memory or test-scoped database via `sqlite3.connect(":memory:")` so no temp
    files are created.
  - openpyxl may return the `KEY` formula string, a cached value, or `None`; the script
    does not blindly trust a loaded `KEY` — it creates `KEY` when absent, trusts it only
    when its values match the rebuilt pattern, and otherwise resolves per `--key-mismatch`.
  - Fuzzy mis-mapping risk: a similarity threshold that is too low could bind two
    genuinely different columns. The threshold is fixed at `>= 0.85` on normalized names,
    and the position and normalized-equality passes run first so well-formed inputs never
    reach the similarity step. Mitigation: tests assert that a typo/variant resolves and
    that genuinely distinct columns are not bound.
  - Non-blocking prompt: the interactive `--key-mismatch prompt` path must never block
    automation. It prompts only when stdin is an interactive TTY and otherwise fails fast
    with a non-zero exit and guidance to pass `--key-mismatch trust|overwrite`.
- Security/privacy considerations: local file I/O only (Excel read, SQLite write); no
  network or external process access. Source data is planning data handled entirely
  in-process.
- Operational/rollout risks and mitigations:
  - New runtime dependencies `pandas` and `openpyxl` (and transitive `numpy`) are
    introduced; `openpyxl` remains the Excel read engine used by pandas. `sqlite3`,
    `difflib` (fuzzy column matching), and `logging` (warnings) are in the Python
    standard library, so the SQLite sink, fuzzy matching, and warning logs add no new
    third-party dependency. pandas/openpyxl/numpy are unchanged by this revision.
    `hypothesis` is added as a dev dependency for T2 property tests.
  - Risk: divergence from the as-built workbook if the Super Category/PPG quirk or the
    `SKU Descripiton` typo is "corrected." Mitigation: both are encoded as explicit
    invariants and asserted by tests.

## Implementation Strategy

- Implementation scope: add `src/normalize_le.py` (pure transform plus thin I/O
  boundaries and a CLI entry point); keep the file under 500 lines, extracting helpers
  into `src/_normalize_le_helpers.py` if needed. Add `tests/test_normalize_le.py`.
- New classes/functions/commands to add: `coerce_sku`, `rebuild_key`, `resolve_columns`,
  `resolve_key`, `load_source`, `normalize`, `compute_ytg`, `validate_tieouts`,
  `write_sqlite`, `print_summary`, `main` (per the research layout).
- Dependency changes and rationale: add `pandas >=2.2,<3.0` and `openpyxl >=3.1,<4.0` as
  runtime dependencies (pandas for the transform, openpyxl as the Excel read engine used
  by pandas); add `hypothesis >=6.100,<7.0` as a dev dependency (T2 requires >=1 property
  test per pure function). numpy is pulled transitively by pandas and is not pinned
  explicitly unless CI surfaces a conflict. `sqlite3` is in the Python standard library
  and adds no new dependency for the SQLite sink.
- Logging/telemetry additions and locations: behavior is fail-fast via raised
  `ValueError`/exception with a clear message plus a non-zero exit code from `main`. The
  Python stdlib `logging` module emits warnings to stderr for extra source columns and
  for `trust`/`overwrite` KEY resolution. The tie-out summary is printed to stdout by
  `print_summary`.
- Rollout plan: classified T2 — Core. The module is a pure transform with no `datetime`,
  `time`, or `random` usage, so no Clock interface or seeded RNG is required. No feature
  flag is needed; the script is invoked directly.

## Definition of Done

- [x] Acceptance criteria documented and mapped to tests or demos
  - CLI/defaults/required-`--output`/`--key-mismatch` → CLI tests for custom flags
    (including `--key-mismatch` default and alternatives); missing-`--output` non-zero
    exit test.
  - `header=2`, blank-`Customer` drop → load tests.
  - Column resolution (position-independent) → `resolve_columns` unit tests:
    exact-by-position; reordered columns resolved by name; a typo/variant resolved by
    fuzzy `>= 0.85`; canonical rename after resolution.
  - Missing required column → `resolve_columns` halt test asserting a clear error naming
    the unmatched expected column(s) and a non-zero exit.
  - Extra actual columns → `resolve_columns` warn-and-continue test asserting a logged
    warning naming the extras and a normal run.
  - `coerce_sku`/KEY rebuild → `coerce_sku` unit + property tests; `rebuild_key` tests.
  - KEY handling → `resolve_key` tests: absent → created; present-and-matching →
    trusted; present-and-diverging → `trust`/`overwrite`/`prompt` resolution
    (each logging a warning where applicable); non-interactive `prompt` → fail fast with
    a non-zero exit.
  - Target column order / one-row-per-KEY / first-appearance → `normalize` unit + property
    tests.
  - First-row text + summed numerics (blanks as 0) → `normalize` aggregation tests.
  - `YTG = sum(May..Dec)` on output → `compute_ytg` unit + property tests.
  - Super Category/PPG quirk → quirk-invariant test asserting both equal source `PPG`.
  - Tie-out validation (row-count, `1e-6`, `FY == sum(months)`) → `validate_tieouts` pass
    and failure tests; non-zero exit assertion.
  - stdout summary → `print_summary`/`main` test with `capsys`.
  - SQLite persist + replace-if-exists → `sqlite3.connect(":memory:")` round-trip
    integration test asserting columns, order, and row count; re-run replaces table with
    no row duplication.
- [x] Behavior matches acceptance criteria in all documented environments
- [x] Tests updated/added (unit/integration as applicable)
- [x] Edge cases and error handling covered by tests
- [x] Docs updated (README, docs/features/active/... links)
- [x] Telemetry/logging added or updated (if applicable) — the tie-out summary uses `print` by design; the stdlib `logging` module emits stderr warnings for extra source columns and `trust`/`overwrite` KEY resolution
- [x] Toolchain pass completed (format → lint → type-check → test)
