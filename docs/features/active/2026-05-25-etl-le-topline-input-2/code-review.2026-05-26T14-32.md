# Code Review — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Generated: 2026-05-26T14-32
- Base/head: `2d86e836f89f43df011ed7528ac8decbd82cd761..c97da58a18869584004664590180a7d5a757f3ca`
- MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: review-artifact MCP template tools and a
  repo-side template fallback are both absent; artifact built from the canonical
  headings per `feature-review-workflow` fail-closed guidance.

## Executive Summary

This is a post-remediation re-review. The feature delivers a single-file-style Python
ETL split across cohesive modules (`normalize_le.py`, `le_columns.py`, `le_key.py`)
plus a new typed I/O boundary module (`src/pandas_io.py`) and an in-memory test fixture
suite. The remediation that prompted this re-review eliminated all four prior
suppressions by refactoring the pandas boundary behind a typed `Protocol` adapter and
by assembling the SQLite read query from a constant clause plus a quoted identifier.

The four-stage toolchain (Black, Ruff, Pyright strict, Pytest) passes clean in a single
pass with zero suppressions remaining in `src/` and `tests/`. Coverage is 100% line /
100% branch repo-wide including the new boundary module. The typed-adapter approach does
not weaken typing strictness: it uses `typing.cast` to a `Protocol` view (a runtime
no-op) rather than `Any`, consistent with the `python.md` directive to isolate untyped
libraries behind small typed adapters. No runtime behavior or public API regressed —
the transform functions, the `--key-mismatch` semantics, the `0.85` fuzzy threshold,
and the `to_sql(if_exists="replace", index=False)` persistence contract are unchanged;
only the static-typing routing of the pandas member access moved into `pandas_io.py`.

No blocking findings. The code design adheres to the repository's separation-of-concerns,
typing, testing-determinism, file-size, and commenting policies.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/pandas_io.py` | 39-79 | The typed `Protocol` views (`_PandasReaders`, `_FrameWriter`) live in a `TYPE_CHECKING` block and are reached via `typing.cast`, which is a runtime no-op. This contains the unstubbed-pandas unknown member types without `Any` or a suppression. | None required. Approach is correct and aligns with `python.md` ("isolate it by wrapping untyped libraries behind small typed adapters"). | Confirms the typed-adapter refactor does not weaken strictness. | Pyright exits 0/0/0; module is 100% covered. |
| Info | `src/pandas_io.py` | 86, 116-140 | The S608 lint trigger was removed by assembling the read query from the module constant `_SELECT_ALL_FROM` plus a quoted, escaped identifier (`'"' + table_name.replace('"', '""') + '"'`) instead of an f-string literal beginning with the SQL verb adjacent to interpolation. | None required. Identifier is a trusted internal value and is quoted/escaped; SQL identifiers cannot be parameterized. | Confirms RF-1 resolution is correct, not merely silenced. | `ruff check .` exits 0 with no `# noqa`. |
| Info | `tests/le_fixtures.py` | 27, 76-91 | The test `read_table` helper is a thin documented wrapper that delegates to `src.pandas_io.read_table`, keeping the typed boundary and identifier quoting in one place. | None required. | Confirms RF-3 resolution; no duplicated suppression in tests. | `grep` for suppressions returns no matches. |
| Info | `src/le_key.py` | 127-189 | `decide_key_action` is a pure decision seam with `is_tty`/`prompt` injected, so the interactive `--key-mismatch prompt` path is fully testable without real stdin and never blocks automation (raises with guidance when non-interactive). | None required. | Supports determinism and no-temp-files policy. | 100% branch coverage on `le_key.py`. |
| Info | `src/le_columns.py` | 1-36 | Column resolution is a self-contained pure module (depends only on `re`, `difflib`, typing) with the `0.85` threshold as a named constant and position/equality passes before fuzzy match. | None required. | Separation of concerns; no import cycle with `normalize_le`. | 100% line/branch coverage. |

No Major or Blocking findings were identified.

## Typed-Python Review

- No `Any` is introduced anywhere in the changed files. The single concession to the
  unstubbed pandas/openpyxl boundary is contained in `src/pandas_io.py` via
  `typing.cast("_PandasReaders", pd)` / `typing.cast("_FrameWriter", df)`, where the
  `Protocol` declares only the exact members and signatures invoked. Callers receive
  concrete `pd.DataFrame` returns.
- All public functions across `normalize_le.py`, `le_columns.py`, `le_key.py`, and
  `pandas_io.py` carry complete parameter and return type hints and Google-style
  docstrings with `Args`/`Returns`/`Raises`/`Side effects` as applicable, satisfying the
  commenting policy.
- Pure transforms are separated from the I/O boundary; the I/O boundary is now isolated
  in a dedicated module, improving testability and keeping `reportUnknownMemberType`
  contained at a single seam rather than scattered at call sites.

## Regression Assessment

`typing.cast` is a runtime no-op, so the move of the pandas member access into
`pandas_io.py` changes static typing only, not behavior. The persistence call remains
`to_sql(table_name, con, if_exists="replace", index=False)` (via `write_table`), the
Excel read remains `read_excel(..., header=2, engine="openpyxl")` (via
`read_excel_sheet`), and the SQLite read remains `read_sql(SELECT * FROM "<table>", con)`
(via `read_table`). The 72-test suite — including the in-memory SQLite round-trip,
replace-if-exists re-run, and end-to-end `main` tests — passes, confirming no behavioral
or API regression.
