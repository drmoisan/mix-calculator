# Code Review — etl-le-topline-input (Issue #2)

- Artifact type: code-review
- Timestamp: 2026-05-26T17-05
- Feature: 2026-05-25-etl-le-topline-input-2
- Base branch (resolved): `main` @ `03eb801de63e5f39e18c59e8d96706eafde3857c`
- Head SHA: `ac098a9454cefd50c6d39a3cd3784d4317700c6e`
- Scope: full branch diff `feature/etl-le-topline-input-2` vs `main`

> `MCP_TEMPLATE_RESOLUTION_UNAVAILABLE`: the MCP `code-review-template` asset could
> not be resolved in this environment; the artifact is authored with the required
> canonical sections (`## Executive Summary`, `## Findings Table`).

## Executive Summary

This re-review follows remediation of the single Blocking file-size finding from the
prior review. The `fill_blank_totals` test cluster was extracted verbatim into
`tests/test_normalize_le_totals.py` (121 lines), bringing `tests/test_normalize_le.py`
to 436 lines. The split is mechanical: assertions are unchanged, test count is
unchanged (77), and coverage is unchanged (100% line / 100% branch). The new file has
a clear module docstring describing the split and what lives where.

The branch's typed-Python quality holds: Black, Ruff, and Pyright (strict) all pass
with zero findings, run by the reviewer. The design maintains a clean separation
between pure transforms (`src/le_columns.py`, `src/le_key.py`, `src/le_totals.py`, the
`normalize`/`compute_ytg` functions) and I/O boundaries (`load_source`/`write_sqlite`
in `src/normalize_le.py`, the typed pandas adapter in `src/pandas_io.py`). The as-built
`Super Category <- PPG` quirk and the `SKU Descripiton` typo are encoded as explicit,
test-asserted invariants. No suppressions are present.

No blocker- or major-severity findings. Two informational observations are recorded
below; neither requires change and neither blocks merge.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `tests/test_normalize_le_totals.py` | lines 1-21 | New module from the file-size split. Module docstring correctly documents the split and cross-references the sibling test modules. Imports the three shared fixtures it uses (`build_workbook`, `close`, `make_row`) and `load_source`; no unused imports (Ruff clean). | None. Accept as-is. | The split is the intended remediation; the new file is cohesive (only blank-total `load_source` cases) and self-documenting. | `tests/test_normalize_le_totals.py`; Ruff exit 0; 3 tests collected. |
| Info | `tests/test_normalize_le.py` | whole file | Reduced from 532 to 436 lines; the three moved tests are absent here and present only in the totals module. No assertions altered in the remaining 28 tests. | None. Accept as-is. | Confirms the remediation is a move, not a rewrite; preserves the prior validated test behavior. | `rg -c "fill_blank\|fills_blank_totals\|preserves_populated" tests/test_normalize_le.py` → none; `wc -l` → 436; 77 tests pass. |
| Info | `src/le_totals.py` | lines 30-95 | Pure-transform module for blank-total fill and FY/quarter consistency checks. Google-style docstrings, intent comments above the fillna loop, fail-fast typing. `fillna`-style fill (not overwrite) matches the spec's "populated totals left unchanged". | None. Accept as-is. | Good separation of the defect-fix logic from the I/O boundary; 100% line/branch covered. | `src/le_totals.py`; coverage 14 stmts / 2 branch at 100%. |

## Detailed Observations

### Test organization (post-split)

The suite now mirrors module structure cleanly: `test_le_columns.py` /
`test_le_key.py` cover the resolver and KEY modules; `test_normalize_le.py` covers the
pure transforms; `test_normalize_le_io.py` covers I/O, SQLite persistence, and the CLI;
`test_normalize_le_totals.py` covers the blank-total fill path through `load_source`.
The split improved cohesion without changing behavior. The largest test file
(`test_normalize_le.py`, 436) now has comfortable headroom under the 500-line limit.

### Typed pandas boundary

`src/pandas_io.py` encapsulates the pandas read/write boundary behind typed helpers,
which is how the branch achieves a Pyright-strict-clean, zero-suppression state for
code that interacts with an untyped third-party surface. This is consistent with the
repo rule preferring small typed adapters over `Any` or `# type: ignore`.

### Confidentiality

All test fixtures use fabricated customer names and abstract PPG codes; no real
financial figures appear; the confidential workbook inputs and `.db` output are
isolated under the gitignored, untracked `artifacts/` tree. See the policy audit
Confidentiality section for the verification commands and results.

## Verdict

Code-review verdict: **PASS** — no blocker or major findings. The remediation is
sound and the branch is ready from a code-quality standpoint.
