# `2026-05-26-load-aop-sheet` — User Story

- Issue: #7
- Owner: drmoisan
- Status: Draft
- Last Updated: 2026-05-26T14-03

## Story Statement

- As a data analyst working with the planning workbook, I want to load the
  `AOP1` sheet into a validated pandas DataFrame and a SQLite table by running a
  single command, so that I can query AOP figures with confidence that per-row
  totals tie out.
- As a maintainer of the ETL codebase, I want the shared column/key/totals
  helpers to carry neutral `etl_*` names reused by both the LE and AOP loaders,
  so that a second consumer does not duplicate logic or imply LE ownership of
  domain-agnostic code.
- As a downstream developer, I want an importable `load_aop`/`persist_aop` API
  with an injectable post-validation `transform`, so that I can integrate AOP
  loading into other Python workflows without shelling out to the CLI.

## Problem / Why

The repository contains the `normalize-le` ETL (`src/normalize_le.py`) over the
`LE-8 + 4` sheet. A sibling ETL is needed for the `AOP1` sheet: load it into a
pandas DataFrame, establish the business KEY, validate per-row totals, and
persist to SQLite. The shared ETL helpers currently carry `le_*` names that
imply LE ownership even though the logic is domain-agnostic; a second consumer
makes the misleading naming a maintenance liability and risks duplicated logic.


## Personas & Scenarios

- Persona: Planning data analyst
  - Who they are: an analyst responsible for the AOP planning workbook who
    needs the `AOP1` sheet in a queryable form.
  - What they care about: that loaded figures are correct — specifically that
    `YTD`, `Q1..Q4`, and `YTG` tie out to their constituent months — and that
    the business KEY (`Customer & SKU # & Type`) is consistent.
  - Constraints: works from `.xlsx` exports whose column order may shift between
    versions and which include two leading non-data rows and a trailing `#N/A`
    spill region.
  - Goals and frustrations: wants a single command that loads, validates, and
    persists; is frustrated when a silently mismatched total or a blindly
    trusted KEY corrupts downstream analysis.
  - Context and motivations: already uses the sibling `normalize-le` ETL and
    expects the AOP loader to behave consistently.

- Scenario: Loading and persisting the AOP1 sheet
  - Who is acting: the planning data analyst.
  - Trigger: a refreshed `AOP1` workbook export needs to be loaded for analysis.
  - Steps: the analyst runs
    `poetry run load-aop data/aop.xlsx --output build/aop.db`. The loader reads
    the sheet with `header=2`, resolves columns position-independently (position
    pass then fuzzy `>= 0.85`), locates the optional KEY by name, drops
    blank-`Customer` rows, fills blank totals, establishes the KEY under the
    default `prompt` policy, coerces numeric columns, cleans `Super Category`
    and `PPG` sentinels, and validates per-row total identities.
  - Obstacles/decisions: if a required column is missing, the run halts with a
    `ValueError` and exit code 1; extra columns are logged as a warning and
    processing continues; duplicate KEYs are logged as a warning but do not
    fail; if the KEY column is absent or mismatched, the `--key-mismatch` policy
    decides whether to create, trust, or overwrite it (never blindly trusting
    the loaded value).
  - Outcome: a summary is printed to stdout (rows, unique KEYs, customers,
    SKU #s, sorted Types, YTD total, `Validation: OK`), the table is written to
    SQLite with quoted lookup indexes, and a persistence confirmation line is
    printed.

- Scenario: Reusing the loader programmatically with a transform
  - Who is acting: a downstream developer.
  - Trigger: a Python workflow needs validated AOP data with an extra derived
    column.
  - Steps: the developer calls
    `load_aop(source, transform=add_margin)` and then
    `persist_aop(df, "out.db")`. Validation runs first; the `transform` is
    applied only after validation passes and before the DataFrame is returned.
  - Obstacles/decisions: injected `is_tty`/`prompt` allow KEY reconciliation to
    be driven without a real terminal in tests and automation.
  - Outcome: the developer receives a validated DataFrame with the transform
    applied, and the SQLite round-trip (including `if_exists="replace"`)
    produces no row duplication.


## Acceptance Criteria

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


## Non-Goals

The following are explicitly excluded from this feature:

- Re-implementing the shared helpers (`coerce_sku`, `rebuild_key`,
  `decide_key_action`, `resolve_key`, `resolve_columns`, `normalize_name`,
  `fill_blank_totals`, `total_vs_months_violations`, `read_excel_sheet`,
  `write_table`); they are reused, not duplicated.
- Treating rows 1-2 as data; they are non-data leading rows.
- Blindly trusting a loaded KEY; KEY is always created/trusted/resolved per
  `--key-mismatch`.
- Applying the LE `Super Category <- PPG` quirk.
- Collapsing rows by KEY (AOP preserves rows).
- Renaming columns by default; original headers (including the intentional
  `SKU Descripiton` typo) are preserved unless `--snake-case` is set.
- Raising on duplicate KEYs; duplicates are a warning only.
- Dropping `YTD`, `Q1..Q4`, or `YTG`.
- Adding any new third-party dependency.
- Changing LE behavior as part of the shared-module rename or the
  `fill_blank_totals` generalization.
