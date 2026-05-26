# Feature Audit — etl-le-topline-input (Issue #2)

- Artifact type: feature-audit
- Timestamp: 2026-05-26T16-50
- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature

> `MCP_TEMPLATE_RESOLUTION_UNAVAILABLE` — authored from canonical headings.

## Scope and Baseline

- Base branch (resolved): `main` @ `03eb801de63e5f39e18c59e8d96706eafde3857c`
  (git-computed merge-base, confirmed by PR-context artifacts; the caller-supplied
  `2d86e83` is an ancestor and yields the same changed-file set).
- Head: `feature/etl-le-topline-input-2` @ `636c493f6dca28b7a83a1f7069e1dba881ec6e4a`.
- Acceptance-criteria sources (full-feature): `user-story.md` `## Acceptance
  Criteria`, `spec.md` `## Definition of Done`. The caller also cites `issue.md`
  `## Acceptance Criteria`; it is included here because it carries the only
  unchecked item relevant to the defect fix.
- Change under review: defect fix adding blank `FY`/`Q1..Q4` fill before collapse
  (`src/le_totals.py` `fill_blank_totals`), wired into `load_source`, plus per-row
  `Qn == sum(its months)` validation in `validate_tieouts`, with tests.

## Acceptance Criteria Inventory

`issue.md` `## Acceptance Criteria` — 14 items. 13 were already checked at the
prior PASS; one item remained unchecked and is the focus of this re-audit:

- Item (previously `[ ]`): "Blank `FY`/`Q1..Q4` cells in the source are filled
  from their monthly components before collapsing (`FY <- sum(Jan..Dec)`,
  `Qn <- sum(its months)`); populated totals are left unchanged and NaN months
  count as 0."

`user-story.md` `## Acceptance Criteria` — 13 items, all previously `[x]`. The
validation item references `FY == sum(months)` (the pre-fix text); it does not
enumerate the blank-fill or the Qn check as a separate criterion.

`spec.md` `## Definition of Done` — 6 checklist items plus a mapping list, all
previously `[x]`.

## Acceptance Criteria Evaluation

| # | Source | Criterion (abbrev.) | Verdict | Evidence |
|---|---|---|---|---|
| 1 | issue/user-story | CLI defaults; `--output` required; SQLite-only sink | PASS | `src/normalize_le.py` `_build_parser`/`main`; `tests/test_normalize_le_io.py` CLI tests. Unchanged this revision. |
| 2 | issue/user-story | `header=2`; drop blank `Customer` | PASS | `load_source` lines 177, 210-213; blank-customer drop test. |
| 3 | issue/user-story | Position-then-fuzzy column resolution + canonical rename | PASS | `src/le_columns.py` `resolve_columns`; `tests/test_le_columns.py` (15 tests). |
| 4 | issue/user-story | Unmatched required column halts with naming error | PASS | `resolve_columns` raises naming unmatched columns; column tests. |
| 5 | issue/user-story | Extra columns warn-and-continue | PASS | `load_source` line 195-196; column tests. |
| 6 | issue/user-story | `coerce_sku` integer rendering + non-numeric preserved | PASS | `src/le_key.py` `coerce_sku`; `tests/test_le_key.py`. |
| 7 | issue/user-story | KEY create/trust/resolve per `--key-mismatch` | PASS | `src/le_key.py` `resolve_key`/`decide_key_action`; key tests. |
| 8 | issue/user-story | 26 columns in exact order; one row per KEY; first-appearance; YTG after Q4 | PASS | `normalize` `TARGET_COLUMNS`; normalize tests. |
| 9 | issue/user-story | First-row text; `Jan..Dec`/`FY`/`Q1..Q4` summed (blanks as 0) | PASS | `normalize` groupby-sum; aggregation tests. |
| 10 | issue/user-story | `YTG = sum(May..Dec)` on output | PASS | `compute_ytg`; `test_compute_ytg_sums_may_through_dec`. |
| 11 | issue/user-story | Super Category and PPG both from source PPG (quirk) | PASS | `normalize` lines 286-287; quirk test. |
| 12 | **issue** | **Blank `FY`/`Q1..Q4` filled from months before collapse; populated untouched; NaN months as 0** | **PASS** | `src/le_totals.py` `fill_blank_totals` (fillna-only); `load_source` line 218 calls it before `resolve_key`/collapse; tests `test_load_source_fills_blank_fy_and_quarters_from_months`, `..._treating_blank_months_as_zero`, `..._preserves_populated_fy_and_quarters`. This is the criterion satisfied by the defect fix. |
| 13 | issue/user-story | Validation: row-count, per-column tie-out `1e-6`, `FY == sum(months)`, `Qn == sum(its months)`; non-zero exit | PASS | `validate_tieouts` (row-count, per-column, FY + Qn per-row via `total_vs_months_violations`); `main` maps `ValueError` to exit 1. Failure-path tests incl. `test_validate_tieouts_quarter_mismatch_raises` and `..._fy_mismatch_raises`. The Qn per-row check is the additive part of the defect fix. |
| 14 | issue/user-story | stdout prints source/unique/output rows, tie-outs, first/middle/last | PASS | `print_summary`; `capsys` tests. |
| 15 | issue/user-story | Persist via `to_sql(..., if_exists="replace", index=False)`; replace table; 26 cols; one row/KEY | PASS | `write_sqlite` -> `src/pandas_io.py` `write_table`; round-trip + replace-no-duplication integration tests. |
| DoD | spec.md | Definition of Done checklist (6 items) | PASS | Toolchain pass (Black/Ruff/Pyright/Pytest exit 0), tests added/updated incl. edge cases, docs/links updated; logging via stdlib `logging` for warnings, `print` for summary by design. |

All evaluated criteria are PASS. The defect fix newly satisfies issue.md item 12
(blank-total fill) and reinforces item 13 (per-row Qn validation). No criterion is
PARTIAL, FAIL, or UNVERIFIED.

Note: feature-audit PASS reflects acceptance-criteria coverage. The branch carries
one policy-level FAIL (the 532-line `tests/test_normalize_le.py`) recorded in the
policy audit; that is a code-quality/policy finding, not an unmet acceptance
criterion, and is routed to remediation separately.

## Summary

The feature satisfies all acceptance criteria across `issue.md`, `user-story.md`,
and `spec.md` for the full-feature work mode. The defect fix correctly closes the
previously-open blank-total-fill criterion: blank `FY`/`Q1..Q4` cells are filled
from their monthly components before collapse, populated totals are left unchanged
(fillna semantics), NaN months count as 0, and a per-row `Qn == sum(its months)`
check now guards the output alongside the existing `FY` check. Behavior, typing,
documentation, and test coverage (100% line/branch) all verify.

PR readiness is gated only by the non-AC policy finding (test-file size) tracked in
the policy audit and remediation inputs.

## Acceptance Criteria Check-off

The previously-unchecked `issue.md` criterion (item 12, blank-total fill) is
verified PASS and is checked off in `issue.md` by this audit. All other criteria
were already `[x]` and remain so.

### Acceptance Criteria Status
- Source: `issue.md` (`## Acceptance Criteria`), `user-story.md`
  (`## Acceptance Criteria`), `spec.md` (`## Definition of Done`)
- Total AC items (issue.md): 14
- Checked off (delivered) after this audit: 14
- Remaining (unchecked): 0
- Items remaining: none
