# Code Review — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Base branch (resolved): `main` @ `2d86e836f89f43df011ed7528ac8decbd82cd761`
- Head: `feature/etl-le-topline-input-2` @ `74743671ae26e42e74e039fa5f33e90d2e4b3294`
- Review timestamp: 2026-05-25T21-11
- Languages with changed code files: Python (only)

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: the `code-review-template` MCP asset is not
> available; this artifact is constructed directly with the required `## Executive
> Summary`, `## Findings Table`, and the standard findings table header.

## Executive Summary

The change adds a single-file Python ETL CLI (`src/normalize_le.py`) with three test
modules. The code is well-structured: pure transforms are cleanly separated from the two
I/O boundaries (`load_source`, `write_sqlite`) and the CLI glue, matching the spec's
module layout. Typing is complete and Pyright-clean, docstrings and intent comments meet
the repository commenting policy, and the test suite covers positive, negative, edge, and
property-based scenarios with 100% line and branch coverage.

The auditor independently re-ran Black, Ruff, Pyright, and Pytest; all passed in a single
clean pass. This is a typed-Python review (Python files changed).

No blocker or major findings. A small number of minor and informational observations are
recorded below; none require remediation before merge.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | src/normalize_le.py | L498 | Module is 498 lines, 2 below the 500-line hard limit. | Monitor; extract helpers into `src/_normalize_le_helpers.py` if the module grows. | The spec anticipated this extraction path; the margin is small. | `general-code-change.md` file-size limit; `wc -l` = 498. |
| Minor | src/normalize_le.py | L230, L388 | Two `# pyright: ignore[reportUnknownMemberType]` at pandas `read_excel`/`to_sql` boundaries. | Keep as-is; suppressions are scoped single-line with explanatory comments. | pandas-stubs resolves the unstubbed openpyxl overload / connection union as partially unknown; refactoring would not remove the unknown member without weakening typing. | `src/normalize_le.py:226-232`, `383-390`. |
| Minor | tests/le_fixtures.py | L83 | `# noqa: S608 - trusted test table name` on an f-string `SELECT`. | Acceptable in test code; table name derives from test constants, not user input. | Mirrors the test-only rationale of authorized S108/S105 patterns in `python-suppressions.md`. | `tests/le_fixtures.py:83`. |
| Info | src/normalize_le.py | L489 | CLI errors print to stdout via `print(f"ERROR: {error}")` then return 1. | Consider `print(..., file=sys.stderr)` so errors are separable from tie-out summary on stdout. | The spec text mentions surfacing the message "to stderr"; current behavior prints to stdout. Functionally correct (non-zero exit and message emitted) and asserted by tests via `capsys.out`; cosmetic stream choice only. | `src/normalize_le.py:488-490`; `tests/test_normalize_le_io.py:238-243` asserts `captured.out`. |
| Info | src/normalize_le.py | L131-138 | `coerce_sku` branch ordering (int before float, with `bool` guarded first). | None; ordering is documented and tested. | Branch ordering is load-bearing (bool is an int subclass) and carries a decision-logic comment. | `src/normalize_le.py:124-141`; `test_coerce_sku_branches`. |
| Info | tests/le_fixtures.py | L93-108 | `PersistentConnection` overrides `close` to a no-op for in-memory round-trips. | None; documented and torn down via `real_close`. | Necessary because `write_sqlite` closes its connection in `finally`; the seam avoids temp files per policy. | `tests/le_fixtures.py:93-127`. |

## Detailed Notes

### Design and separation of concerns
- Pure transforms (`coerce_sku`, `rebuild_key`, `validate_schema`, `normalize`,
  `compute_ytg`, `validate_tieouts`) contain no I/O and are individually unit-tested.
- I/O is isolated to `load_source` (openpyxl read) and `write_sqlite` (SQLite write),
  each documented with a Side-effects section. This matches the spec's stated boundaries.
- The `Super Category <- PPG` quirk and the `SKU Descripiton` typo are encoded as
  explicit invariants and asserted by `test_normalize_le_super_category_ppg_quirk` and
  the `TEXT_COLUMNS`/`SOURCE_COLUMNS` constants, satisfying the anti-requirements.

### Typing
- Full annotations throughout; `pd.Series[float]` return on `compute_ytg`. Pyright strict
  reports 0 diagnostics. The two boundary `pyright: ignore` directives are the minimum
  needed and are scoped to single statements.

### Error handling
- Fail-fast `ValueError` for schema and tie-out failures, mapped to exit code 1 in
  `main`; missing `--output` produces a non-zero argparse `SystemExit`. The broad
  surface is confined to the CLI entry point and re-surfaces the message — consistent
  with the policy's allowance for boundary handlers.

### Tests
- AAA structure, descriptive names, parametrized boundary matrix, and Hypothesis
  property tests for the pure functions. In-memory `io.BytesIO` and
  `sqlite3.connect(":memory:")` keep tests free of temp files and external services.
- Negative paths (row-count mismatch, column perturbation, FY mismatch, schema mismatch,
  missing `--output`) and the zero-output `print_summary` branch are all exercised,
  which is why branch coverage reaches 100%.

## Verdict

No blocking or major findings. Recommend proceeding to PR readiness on code-quality
grounds. Minor/info items are optional follow-ups, not merge gates.
