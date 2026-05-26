# mix-calculator

A mix calculator.

## LE normalization (`normalize_le`)

`src/normalize_le.py` replicates the as-built Excel "LE-8 + 4" normalization
pipeline. It reads the source sheet into a pandas DataFrame, validates the schema,
rebuilds the `KEY` column, collapses each `(Customer, SKU #, Type)` key's YTD/YTG
rows into a single full-year row, derives the `YTG` (`sum(May..Dec)`) column, and
persists the result to a SQLite database.

```sh
python -m src.normalize_le <input.xlsx> --output <path.db> \
  [--source-sheet "LE-8 + 4"] [--table-name LE]
```

- `--output` is required and must point at a SQLite database file; SQLite is the
  only output sink. An existing table of the same name is dropped and rewritten.
- `--source-sheet` defaults to `"LE-8 + 4"`; `--table-name` defaults to `LE`.
- A validation/tie-out summary is printed to stdout; the command exits non-zero on
  any schema or tie-out failure.

See [docs/features/active/2026-05-25-etl-le-topline-input-2/](docs/features/active/2026-05-25-etl-le-topline-input-2/)
for the full specification and acceptance criteria (issue #2).

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
