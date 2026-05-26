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
