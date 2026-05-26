---
name: pandas-pyright-stubs
description: Under this repo's strict Pyright, pandas/openpyxl code needs pandas-stubs and narrow boundary ignores
metadata:
  type: project
---

This repo runs Pyright in `typeCheckingMode = "strict"` with `reportMissingTypeArgument = "error"` (see `pyproject.toml` `[tool.pyright]`). Neither `pandas` nor `openpyxl` installs a `py.typed` marker, so without type stubs every pandas call resolves to `Unknown` and strict mode emits dozens of `reportMissingTypeStubs` / `reportUnknownMemberType` errors.

**Why:** Adding `pandas` for `src/normalize_le.py` (issue #2) produced 61 strict-Pyright errors until `pandas-stubs` was added as a dev dependency, which reduced it to a handful at genuine untyped-library boundaries.

**How to apply:** When introducing pandas (or pandas-using modules) here:
- Add `pandas-stubs` to `[tool.poetry.group.dev.dependencies]`.
- For the residual `reportUnknownMemberType` at `pd.read_excel` (openpyxl `Workbook`/`Book` in the overload) and `pd.to_sql`/`pd.read_sql` (sqlite connection in the overload), assign the result to an explicitly-typed variable and add a narrow `# pyright: ignore[reportUnknownMemberType]` scoped to that single boundary call with an inline justification. Do not narrow the global strictness.
- numpy scalars (`np.integer`/`np.floating`) carry `Unknown` type params; normalize them to Python scalars early via `.item()` before further use.
- In tests, prefer a typed `close()`/`as_float()` helper over `pytest.approx` (pytest's `approx` is untyped and trips strict mode).

Related: the repo's hard 500-line file limit (`.claude/rules/general-code-change.md`) has no docstring exemption; mandatory Google-style docstrings inflate line counts fast, so a single fully-documented pandas module plus its tests can need splitting (the file budget allows up to 3 production + 3 test files). Shared test fixtures can live in a `tests/le_fixtures.py`-style helper module imported via `from tests.<module> import ...` (resolves through pytest rootdir on sys.path; Pyright resolves it too).
