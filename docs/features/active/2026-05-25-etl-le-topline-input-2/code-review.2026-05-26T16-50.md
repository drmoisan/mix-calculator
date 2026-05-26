# Code Review — etl-le-topline-input (Issue #2)

- Artifact type: code-review
- Timestamp: 2026-05-26T16-50
- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Base: `main` @ `03eb801de63e5f39e18c59e8d96706eafde3857c`
- Head: `636c493f6dca28b7a83a1f7069e1dba881ec6e4a`
- Scope: full branch diff vs base; focused re-review of the defect fix

> `MCP_TEMPLATE_RESOLUTION_UNAVAILABLE` — authored from canonical headings.

## Executive Summary

This re-review covers the defect fix for a real-data tie-out failure on top of the
prior PASS branch. The fix adds a new pure module `src/le_totals.py` with
`fill_blank_totals` (a fillna-style fill of blank `FY`/`Q1..Q4` cells from their
monthly sums) and `total_vs_months_violations` (a per-row consistency check),
wires `fill_blank_totals` into `load_source` before the collapse step, and extends
`validate_tieouts` with a per-row `Qn == sum(its months)` check alongside the
existing `FY == sum(months)` check.

Code quality is high. The new module is a small, single-purpose, fully typed pure
transform with complete Google-style docstrings, intent comments on the loop and
multi-step blocks, and no I/O. The fill is correctly implemented as `fillna`
(only blank/NaN cells filled; populated totals untouched), and NaN months are
counted as 0 because `DataFrame.sum(axis=1)` skips NaN — both behaviors are
asserted by dedicated tests. The new per-row quarter check has an isolated
failure-path test that perturbs Q2 in both source and output so only the new check
fails. Coverage is 100% line and branch for all changed files. The toolchain
(Black, Ruff, Pyright strict, Pytest) passes cleanly with zero suppressions.

No behavior change to populated source values was introduced: the fill is
NaN-only, and the existing transform/validation paths are unchanged except for the
additive per-row quarter check.

One FAIL-level finding is procedural rather than a code defect: the test module
`tests/test_normalize_le.py` is 532 lines, exceeding the 500-line repository limit.
One Info-level note concerns the strength of the populated-totals-preserved test
assertion. Neither indicates incorrect behavior in the shipped transform.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocking | `tests/test_normalize_le.py` | whole file (532 lines) | Test file exceeds the 500-line hard limit in `.claude/rules/general-code-change.md`, which applies to test code. | Split the module along its existing section banners (e.g. extract the `load_source`/fill tests or the `normalize` tests into a sibling `tests/test_normalize_le_transform.py`), reusing `tests/le_fixtures.py`. | The 500-line limit is a hard repository policy with no exception for test files; the addition of the four blank-total tests pushed the file from a previously-passing size to 532. | `wc -l tests/test_normalize_le.py` = 532; rule text "No production code, test code, or reusable script file may exceed 500 lines." |
| Info | `tests/test_normalize_le.py` | `test_load_source_preserves_populated_fy_and_quarters` (lines 244-274) | The populated-totals-preserved test sets each total equal to its month sum (`blank_totals=False`), so it confirms pass-through for the equal case but does not prove the fill leaves a populated total that *diverges* from the month sum untouched. | Optionally add a case where a populated total differs from the month sum and assert the original value is kept, to assert the no-overwrite invariant in its strongest form. | The caller invariant is "populated totals untouched." The implementation (`Series.fillna`) is structurally NaN-only so behavior is correct, but the test does not exercise the divergent-but-populated path explicitly. Not a code defect; the implementation is sound. | `src/le_totals.py` lines 56, 62 use `.fillna(...)`; test asserts only `close(row["FY"], sum(months))`. |
| Info | `src/normalize_le.py` | line 335, `per_row_checks` dict | `validate_tieouts` reuses `QUARTER_TO_MONTHS` and prepends `"FY": MONTH_COLUMNS`, delegating both FY and quarter per-row checks to `total_vs_months_violations`. This is clean reuse; no change needed. | None. | Positive observation: the defect fix factored the per-row check into one helper applied uniformly to FY and all four quarters, avoiding duplicated comparison logic (reusability principle). | `src/normalize_le.py` lines 335-342; `src/le_totals.py` `total_vs_months_violations`. |

## Typed-Python Review Notes

- `src/le_totals.py` is fully annotated; the `pd` import is correctly under
  `TYPE_CHECKING` (the module needs pandas only for type hints, not at runtime,
  since callers pass already-constructed frames). Pyright strict reports zero
  issues across the module.
- `total_vs_months_violations` returns `list[object]` for the offending KEY
  values, which is accurate (KEY values may be arbitrary scalars); the caller
  interpolates them into an error message, so the wide type is appropriate.
- No `Any`, no suppression directives, no untyped escape hatches introduced.
  T2 untyped-escape-hatch budget (0) is satisfied.
- The fillna approach relies on `DataFrame.sum(axis=1)` skipping NaN to realize
  the "NaN months count as 0" rule; this is documented in the module docstring
  and the function docstring, and asserted by
  `test_load_source_fills_blank_totals_treating_blank_months_as_zero`.

## Conclusion

The defect fix is correct, well-typed, well-documented, and well-tested, with no
behavior change to populated source values. The only Blocking item is the
test-file size violation, which is mechanical to resolve by splitting the module.
Route the Blocking finding to remediation.
