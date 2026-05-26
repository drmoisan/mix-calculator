# Code Review — load-aop-sheet (Issue #7)

- Timestamp: 2026-05-26T14-40
- Reviewer: feature-review agent
- Base: `origin/main` @ `c586ac073c0c9b6e21b0f82beee55801a741cb5f`
- Head: `5329c9f48d9652b0b25b6d389860c8500e359ebc`

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: the `code-review-template` MCP asset is not
> exposed in this environment. This artifact uses the required canonical
> headings and findings-table header directly.

## Executive Summary

The change adds a sibling AOP ETL (`src/load_aop.py` plus the extracted pure
helpers in `src/_load_aop_helpers.py`) and performs an atomic rename of the
shared leaf modules from `le_*` to neutral `etl_*` names, generalizing
`fill_blank_totals` to a `dict[str, list[str]]` totals->months mapping. The
implementation reuses the shared leaf helpers and the `src/pandas_io.py`
read/write boundary without re-implementation, isolates I/O at the boundaries,
and keeps pure transform/validation logic free of disk, network, and DB access.

Code quality is high and consistent with repository policy. The four-stage
toolchain (Black, Ruff, Pyright strict, Pytest) passes in a single clean pass on
independent re-run, with 100% line and branch coverage across all changed
modules. Docstrings and intent comments meet the self-explanatory-code policy.
No suppressions were introduced. The atomic rename leaves no lingering `le_*`
module imports. No blocking or major findings were identified. Two minor,
non-blocking observations are recorded for awareness only; neither requires
remediation.

Go/no-go: the change is ready for PR from a code-quality standpoint.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | `src/_load_aop_helpers.py` | L37 | `MONTHS` is built with `list[str](...".split())`, calling a subscripted generic as a constructor. It is valid and Pyright-clean but an uncommon idiom; a plain annotated assignment (`MONTHS: list[str] = "...".split()`) is more conventional. | Optional: replace with a plain annotated assignment for readability. | Subscripted-generic call adds no type-safety over an annotation and may read as unusual to maintainers; no functional impact. | Pyright passes (exit 0); the construct is valid Python. Style observation only. |
| Minor | `src/load_aop.py` | L312-L317 | The CLI summary (`print_summary`) is computed from the canonical-named frame `df` while the snake_cased frame is what is persisted. This is intentional and documented in the inline comment, but the divergence between the persisted column names and the summarized frame is a subtle behavior worth a test assertion that the summary path is unaffected by `--snake-case`. | Optional: add/confirm a CLI test asserting the summary output is identical with and without `--snake-case`. | Reduces the chance a future change to summary computation accidentally couples to column casing. | `tests/test_load_aop_io.py` covers `--snake-case` rename on the persisted table; summary-vs-casing independence is implied by current coverage but not explicitly asserted. |

## Detailed Observations (non-blocking)

### Design and separation of concerns

- I/O is correctly isolated: `load_aop` reads only via
  `src.pandas_io.read_excel_sheet` and `persist_aop` writes only via
  `src.pandas_io.write_table`. Validation, coercion, and sentinel cleaning are
  pure and live in `src/_load_aop_helpers.py` with no I/O.
- The 500-line file-size constraint is respected by extracting AOP constants and
  pure helpers into `_load_aop_helpers.py`, as the spec's Implementation Strategy
  anticipated. The re-export `__all__` in `src/load_aop.py` keeps the public
  import surface stable for callers and tests.
- Reuse without duplication is confirmed: `resolve_columns`, `normalize_name`,
  `resolve_key`, `fill_blank_totals`, and `total_vs_months_violations` are
  imported from the neutral leaves; no shared helper is re-implemented.

### Error handling

- `load_aop` raises `ValueError` for resolution, KEY, and validation failures;
  `validate_aop` aggregates all per-row failures into a single `ValueError`
  message, satisfying the fail-fast-with-context policy.
- `main` confines the broad-to-specific catch to a single `except ValueError`,
  mapping to exit code 1 with the descriptive message printed; this is a CLI
  boundary handler, not a blind catch-all.

### Typing and suppressions

- The change is Pyright-strict clean with zero suppressions. The spec constraint
  to route unknown-typed pandas members through `src/pandas_io.py` rather than
  suppressing is honored.

### Naming and rename atomicity

- The shared-leaf rename to `etl_columns`/`etl_key`/`etl_totals` is atomic: a
  repository search found no remaining `le_columns`/`le_key`/`le_totals` imports
  in `src/` or `tests/`. `normalize_le.py` imports the new names and its
  `fill_blank_totals` call site uses the generalized mapping signature
  (`{"FY": MONTH_COLUMNS, **QUARTER_TO_MONTHS}`).

### Tests

- 110 tests pass. Test files use in-memory fixtures (`io.BytesIO`,
  `sqlite3.connect(":memory:")`); no temp files, consistent with the unit-test
  policy. Property-based tests are present (hypothesis plugin loaded). Coverage is
  100% line and branch on all changed modules.
