# Code Review: edit-schema-columns-assignment (Issue #62)

**Review Date:** 2026-06-09
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62`
**Feature Folder Selection Rule:** Folder suffix `-62` matches the canonical issue number and the branch `fix/edit-schema-columns-assignment`.
**Base Branch:** `main` (merge-base `f7aea0f00475594e254adbd2d17535628713d35c`)
**Head Branch:** `fix/edit-schema-columns-assignment` (`db1c9f07e86045b3f0bd0327418d876228c16b09`)
**Review Type:** Initial review

---

## Executive Summary

This change fixes a Columns-tab rendering bug in the schema builder (issue #62, `minor-audit`). When a schema is opened for editing via `SchemaBuilderPresenter.load_existing`, the edit-from-button path supplies no live `preview_slice`, so the source pool is empty and the existing fuzzy-match pass in `ColumnsTabPresenter.prepopulate()` leaves every canonical row unassigned even though the loaded rows carry persisted aliases. The fix adds a second pass, `_seed_from_persisted_aliases()`, that fills any still-unassigned row from its first persisted alias.

The diff is small and well-contained: one production file (`_columns_tab_presenter.py`) and two test files, plus feature-folder docs and evidence. The implementation respects the existing ordering (live fuzzy matches win), preserves the one-source-per-row invariant, and deliberately does not write a phantom entry back into `source_columns`. The full Python toolchain is clean on the changed files and coverage thresholds are met with no regression.

**What changed:**
`prepopulate()` now calls `_seed_from_persisted_aliases()` after the fuzzy-match loop. The new helper iterates the declared column rows, skips any already in `consumed_columns` (preserving live matches), and seeds `consumed_columns[canonical] = aliases[0]` for unassigned rows that carry at least one persisted alias. Four tests were added (AC-1..AC-4), including a `load_existing`-to-`save` round-trip.

**Top 3 risks:**
1. Low — the fix relies on `aliases[0]` as the canonical persisted assignment; if a column legitimately carries multiple ordered aliases with the first not being the rendered assignment, the seeded value could differ from user expectation. The behavior is documented and tested for the single-alias case, which is the bug's scope.
2. Low — production wiring depends on `DragTabBinder.set_columns` continuing to call `prepopulate()`; verified present at `_schema_builder_drag_tabs.py:123`.
3. Low — coverage was inspected from a pre-existing artifact rather than regenerated in this review; the executor's full-suite evidence (1027 pass) and the targeted re-run (28 pass) corroborate it.

**PR readiness recommendation:** **Go** — toolchain clean, all four acceptance criteria satisfied, production seam verified wired, no blockers.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/presenters/_columns_tab_presenter.py` | `prepopulate` / `_seed_from_persisted_aliases` (108, 111-154) | New seam is wired into production via `DragTabBinder.set_columns -> prepopulate()` and reached on the edit path through `load_existing -> _render_state -> view.set_columns`. | None. | Confirms the fix is not a tested-but-unwired seam. | `_schema_builder_drag_tabs.py:123`; `schema_builder_presenter.py:215,314` |
| Info | `src/gui/presenters/_columns_tab_presenter.py` | `_seed_from_persisted_aliases` docstring | The "no source-pool reflection" decision is documented inline, explaining why the seeded alias is not added back to `source_columns`. | None. | Good rationale capture for a non-obvious choice. | Diff inspection |
| Nit | `src/gui/presenters/_columns_tab_presenter.py` | `_seed_from_persisted_aliases` (seeds `aliases[0]`) | Only the first persisted alias is seeded; multi-alias rows are not surfaced. | Acceptable for this bug's scope; note if multi-alias edit rendering becomes a requirement. | Matches AC-1/AC-3 which specify a single persisted source per row. | issue.md AC-1, AC-3 |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The fix is the minimal correct change: a second pass appended after the existing fuzzy loop, rather than restructuring `prepopulate`.
- Ordering is explicit and defensive: rows already in `consumed_columns` are skipped, so live fuzzy matches are never overridden. This directly satisfies AC-3 and is covered by `test_live_fuzzy_match_wins_over_persisted_alias`.
- The one-source-per-row invariant is preserved by seeding at most one alias per row and only for rows the live pass left unassigned.
- No Qt import and no I/O were added; the change stays pure presenter/state logic, consistent with the issue's constraints.

#### Typing and API notes

- `_seed_from_persisted_aliases(self) -> None` is fully annotated. The loop unpacks the typed `columns` tuple `(canonical, _role, _required, _in_output, aliases)`. No `Any` introduced. No new public API surface was added (the method is `_`-prefixed).

#### Error handling and logging

- No new exception handling or logging was introduced, which is appropriate: the helper performs a bounded dict mutation with no failure modes. The guard `if aliases:` correctly leaves alias-free rows unassigned (AC-2).

---

## Test Quality Audit

The four added tests map one-to-one to the acceptance criteria and exercise the seam through both the presenter-level entry (`prepopulate`) and the higher-level `load_existing -> save` round-trip. Coverage and regression evidence is present in the feature folder and was independently corroborated.

### Reviewed test and QA artifacts

- `tests/gui/test_columns_tab_presenter.py` — adds AC-1 (empty-pool seeding), AC-2 (alias-free row unassigned), AC-3 (live-match-wins). Behavioral assertions on `consumed_columns` and `view.assignments`.
- `tests/gui/test_schema_builder_presenter_core.py` — adds AC-4 (edit-then-save preserves aliases) via `load_existing("tmpl")` then `save()`, asserting the saved Customer column retains `("cust_col",)`.
- `evidence/qa-gates/coverage-comparison.md` — repo-wide 98.27% line / 93.87% branch post-change; modified file 93.33% line / 85.29% branch; changed-line coverage 100%.
- `evidence/regression-testing/fail-before-ac1.2026-06-10T02-12.md` — documents the pre-fix failing state for the AC-1 scenario, confirming the test reproduces the bug before the fix.
- `artifacts/python/lcov.info` — independently parsed: `_columns_tab_presenter.py` 83/86 lines (96.5%), 29/34 branches (85.3%); uncovered lines 263/285/286 are pre-existing helpers.

### Quality assessment prompts

- **Determinism:** Pure in-memory inputs (literal tuples), no clock/RNG/network/filesystem. Deterministic.
- **Isolation:** Each test constructs its own fakes and state; one AC per test.
- **Speed:** Targeted run 28 passed in 0.63s.
- **Diagnostics:** Assertions compare full dicts/tuples, yielding readable failure diffs.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff contains no credentials or tokens. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess use in the change. |
| Input validation at boundaries | ✅ PASS | The `if aliases:` guard handles the empty-alias case; loaded rows come from the persisted schema, not user free-text. |
| Error handling remains explicit | ✅ PASS | No broad catches; bounded dict mutation with no failure modes. |
| Configuration / path handling is safe | N/A | No path or config handling in this change. |

---

## Research Log

No external research was required. All findings are grounded in the branch diff, the four-stage Python toolchain output, the lcov coverage artifact, and the feature-folder evidence.

---

## Verdict

The change is ready for normal PR flow. It is a small, correct, well-tested bug fix with a clean toolchain, no coverage regression, all changed files under the 500-line cap, and a verified production call site through `DragTabBinder.set_columns` and `SchemaBuilderPresenter.load_existing`. There are no Blocker or Major findings; the only notes are informational and a single nit about single-alias seeding that is within the bug's scope. This conclusion is consistent with the Findings Table and the Go recommendation above.
