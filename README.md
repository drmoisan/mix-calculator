# mix-calculator

A mix calculator.

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
