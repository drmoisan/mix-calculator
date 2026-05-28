# mix-calculator

A mix calculator.

## LE normalization (`normalize_le`)

`src/normalize_le.py` replicates the as-built Excel "LE-8 + 4" normalization
pipeline. It reads the source sheet into a pandas DataFrame, validates the schema,
rebuilds the `KEY` column, collapses each `(Customer, SKU #, Type)` key's YTD/YTG
rows into a single full-year row, derives the `YTG` (`sum(May..Dec)`) column, and
persists the result to a SQLite database.

```sh
poetry run normalize-le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE]
```

- `--output` is required and must point at a SQLite database file; SQLite is the
  only output sink. An existing table of the same name is dropped and rewritten.
- `--source-sheet` defaults to `"LE-8 + 4"`; `--table-name` defaults to `LE`.
- A validation/tie-out summary is printed to stdout; the command exits non-zero on
  any schema or tie-out failure.

See [docs/features/active/2026-05-25-etl-le-topline-input-2/](docs/features/active/2026-05-25-etl-le-topline-input-2/)
for the full specification and acceptance criteria (issue #2).

## AOP load (`load_aop`)

`src/load_aop.py` is a sibling ETL over the `AOP1` sheet. It reads the sheet into
a pandas DataFrame, resolves the schema position-independently (position pass then
fuzzy match ≥ 0.85), reconciles the `(Customer, SKU #, Type)` `KEY` via the shared
policy, validates the per-row total identities (`YTD`, `Q1`..`Q4`, `YTG` against
their constituent months), optionally applies a caller-supplied transform, and
persists the result to a SQLite table with lookup indexes. Unlike `normalize_le`,
it does not collapse rows by `KEY`.

```sh
poetry run load-aop <input.xlsx> --output <path.db> \
  [--source-sheet "AOP1"] [--table-name aop] \
  [--key-mismatch {prompt,trust,overwrite}] \
  [--if-exists {replace,append,fail}] [--snake-case]
```

- `--output` is required and must point at a SQLite database file. `--source-sheet`
  defaults to `"AOP1"`; `--table-name` defaults to `aop`.
- `--key-mismatch` (default `prompt`) selects how a present `KEY` column that
  diverges from the rebuilt pattern is resolved; `--if-exists` (default `replace`)
  is passed through to the SQLite write boundary.
- `--snake-case` renames columns to snake_case before writing; by default the
  original headers (including the intentional `SKU Descripiton` typo) are preserved.
- A load summary is printed to stdout; the command exits non-zero on any
  column-resolution, `KEY`-resolution, or validation failure.

An importable API is also available:

```python
from src.load_aop import load_aop, persist_aop

df = load_aop("path/to/workbook.xlsx", sheet="AOP1")
persist_aop(df, db_path="aop.db", table="aop", if_exists="replace")
```

Both ETLs share domain-agnostic leaf modules — `src/etl_columns.py`,
`src/etl_key.py`, `src/etl_totals.py`, and `src/pandas_io.py` — so column
resolution, `KEY` reconciliation, blank-total filling, total/months validation,
and the pandas read/write boundary are defined once.

See [docs/features/active/2026-05-26-load-aop-sheet-7/](docs/features/active/2026-05-26-load-aop-sheet-7/)
for the full specification and acceptance criteria (issue #7).

## Mix decomposition pipeline (`mix-pipeline`)

`src/mix_pipeline.py` runs the LE-versus-AOP gross-to-net mix and rate
decomposition end-to-end. It reuses the `normalize_le`, `load_aop`, and
`load_skulu` loaders to import the `LE`, `aop`, and `sku_lu` tables, then runs a
chain of pure pandas transforms (`src/mix_transforms.py`, `src/mix_lookups.py`,
`src/mix_rate_impacts.py`, `src/mix_rollups.py`, `src/mix_q1.py`) in topological
order and persists every derived table into the same SQLite database. The
orchestrator performs all I/O through `src/pandas_io.py`; the transform modules
are pure.

```sh
poetry run python -m src.mix_pipeline --input <workbook.xlsx> --output <database.db> \
  [--le-sheet "LE-8 + 4"] [--aop-sheet "AOP1"] \
  [--skulu-input <workbook.xlsx>] [--skulu-sheet "SKU_LU"]
```

- `--input` and `--output` are required. `--input` supplies the `AOP1` and
  `LE-8 + 4` sheets; the decomp workbook also contains `SKU_LU`, so a single
  `--input` can run the whole pipeline end-to-end.
- `--le-sheet` defaults to `"LE-8 + 4"`; `--aop-sheet` defaults to `"AOP1"`.
- `--skulu-input` defaults to the value of `--input`; `--skulu-sheet` defaults to
  `"SKU_LU"`. The `SKU_LU` load renames `International` to `Country` and maps the
  `0`/`1` codes to `US`/`Canada`.
- A summary of the tables written and their row counts is printed to stdout; the
  command exits `0` on success and `1` on a loader column/`KEY`/validation
  failure.

The pipeline writes the two import tables (`aop`, `LE`) plus twenty-three derived
tables: `le_wide`, `aop_wide`, `customer_lu`, `sku_lu`, `aop_norm`, `le_norm`,
`aop_vs_le`, `mix_base`, `rate_impacts`, `mix_rollup_1`, `mix_1_sku`,
`mix_rollup_2`, `mix_2_category`, `mix_rollup_3`, `mix_3_customer`,
`mix_rollup_4` (a single-row scalar table), `mix_4_country`, `mix_0_detail`,
`mix_2_sku_bottomsup`, `mix_3_category_bottomsup`, `mix_4_customer_bottomsup`,
`q1_results_by_sku`, and `nrr_summary` (the appended final summary table).

The three `*_bottomsup` tables (issue #18) decompose the gross-to-net mix shift
at the SKU, category, and customer grains.

`nrr_summary` (issue #15) replicates the workbook's `NRR_Summary` tab as a tidy
long table built purely from the frames above (`aop_vs_le`, `rate_impacts`, and
the four `mix_*` levels). It has one row per source-tab label, in source order,
with columns `section` (one of `attribute_summary`, `net_revenue_realization`,
`net_pricing_breakdown`, `mix_breakdown`, `reconciliation`), `metric` (the row
label), `aop`, `le`, `value` (the `Abs` change or `NR $`), `pct` (the `%` change
or `%NR`), and `check`. The final `Check` row carries `"CHECK"` in its `check`
column when the realization-derived Price/Mix and the pricing-plus-mix build-up
reconcile (for both `NR $` and `%NR`), and `"ERROR"` otherwise. Example shape
(fabricated values):

| section | metric | aop | le | value | pct | check |
| --- | --- | --- | --- | --- | --- | --- |
| attribute_summary | Net-Revenue $ | 100.0 | 130.0 | 30.0 | 0.30 | |
| net_revenue_realization | Price/Mix | | | 10.0 | 0.10 | |
| reconciliation | Check | | | | | CHECK |

Confidentiality: the source workbooks (for example
`artifacts/LE v AOP Gross to Net Decomp.xlsx`, `artifacts/Input Files.xlsx`) and
the output `.db` are gitignored and must remain untracked. `SKU Description` and
`Category` values from `SKU_LU` are confidential and never appear in tests,
fixtures, or docs; only fabricated examples (for example `SKU-001`, `Widget A`,
`Category X`) are used. The `US`/`Canada` country values are not secret.

See [docs/features/active/2026-05-26-mix-decomp-transforms-9/](docs/features/active/2026-05-26-mix-decomp-transforms-9/)
for the full specification and acceptance criteria (issue #9).

## Mix Pipeline GUI (`mix-pipeline-gui`)

`src/gui/` provides a PySide6 desktop GUI for the mix-decomposition pipeline.
It uses an MVP (Model-View-Presenter) passive-view structure: presenters hold
the GUI logic (no Qt imports), widgets are thin views, and services
(`PipelineService`, `WorkbookReader`, `DbService`, `ExporterRegistry`) are
constructor-injected at the composition root. The existing `mix-pipeline` CLI is
unchanged; the GUI calls the same loaders and transform chain through a service
seam.

```sh
poetry run mix-pipeline-gui
```

The main window hosts a per-input file/sheet selector for LE, AOP, and SKU_LU
with the default sheet names pre-filled:

- LE default sheet: `"LE-8 + 4"`
- AOP default sheet: `"AOP1"`
- SKU_LU default sheet: `"SKU_LU"`

Workflow:

1. Select an Excel workbook and pick a worksheet tab for each input. Selecting a
   file populates the tab dropdown. An optional "render tab" checkbox shows a
   bounded preview (200 rows) of the chosen tab.
2. Import one selected input or all selected inputs.
3. Run the pipeline. The run executes off the UI thread via a `QObject` worker
   on a `QThread`; the status bar reflects the running state.
4. Save the working tables to a SQLite `.db` file. Save uses `if_exists="replace"`
   table semantics, matching the CLI output sink.
5. Open an existing `.db` to repopulate the working tables.
6. Export selected tables via the Export dialog (per-table checklist plus an
   Export-All control). Excel writes one worksheet per selected table; CSV writes
   one CSV file per selected table into a destination directory. The format set
   is extensible by registering a new exporter — no presenter change required.

Headless testing uses the offscreen Qt platform plugin:

```sh
QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui
```

The repository's `tests/gui/conftest.py` pins `QT_QPA_PLATFORM=offscreen` for
the whole session so widget and worker tests run without a display server.

Example values throughout the GUI tests and docs are fabricated only (for
example `Acme Foods`, `SKU-001`, `Widget A`, `Category X`); no confidential
`SKU Description` or `Category` values appear.

See [docs/features/active/2026-05-27-mix-pipeline-gui-19/](docs/features/active/2026-05-27-mix-pipeline-gui-19/)
for the full specification and acceptance criteria (issue #19).

## Development

This project uses [Poetry](https://python-poetry.org/) with an in-project
virtualenv (`./.venv`).

```sh
poetry install
```

### Quality-control toolchain

Run in order; restart from the top if any step modifies files:

```sh
poetry run black .                                  # 1. format
poetry run ruff check .                             # 2. lint
poetry run pyright                                  # 3. type-check
poetry run pytest --cov=src --cov-report=term-missing  # 4. test
```

Coverage policy: repository line coverage ≥ 80%, new modules/methods ≥ 90%.
