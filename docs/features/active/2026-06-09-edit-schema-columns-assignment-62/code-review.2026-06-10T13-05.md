# Code Review: edit-schema-columns-assignment Cycle-1 (#62)

**Review Date:** 2026-06-10
**Reviewer:** feature-review agent (Claude Opus 4.8)
**Feature Folder:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/`
**Feature Folder Selection Rule:** Suffix `-62` matches the issue number in the branch name `fix/edit-schema-columns-assignment`.
**Base Branch:** `main` (merge-base `f7aea0f`)
**Head Branch:** `fix/edit-schema-columns-assignment` (head `150d42a`)
**Review Type:** Post-remediation re-review (cycle-1 R4)

---

## Executive Summary

This cycle delivers the production fix that cycle-0 missed. Cycle-0 seeded Columns-tab assignments
only from persisted aliases, which the bundled default schemas (empty aliases) never exercise, and
the Edit Schema button opened the builder with no `preview_slice`. Cycle-1 reads the selected
worksheet's real headers through the existing reader + best-header-row path and seeds them as the
Columns-tab source pool, so fuzzy prepopulation can render matching canonical rows as assigned. It
also adds a resizable scroll area on the Columns tab (AC-7) and resizable/min/max window controls
(AC-8), and preserves the no-file/no-sheet seam (AC-9).

**What changed:**
`wire_edit_schema_buttons` now takes the three per-tab `SourceSelectionPresenter`s (each carrying
`.reader`) and, before opening the builder, builds a live `PreviewSlice` from the selected
worksheet headers via the new public `read_worksheet_header_columns`. `best_header_row` was promoted
to a public function and reused. `_schema_builder_tabs.build_columns_tab` wraps the columns widget
in a resizable `QScrollArea`. A new `_schema_builder_window_setup.py` applies the window flags so
`schema_builder_dialog.py` stays under 500 lines. `_columns_tab_drag.py` adds two public read seams
(`assignment_text`, `row_assignment_text`) used to assert the rendered assignment. The cycle-0
`_seed_from_persisted_aliases` second pass remains as a fallback for alias-carrying schemas.

**Top 3 risks:**
1. The Edit path depends on the per-tab presenter being injected at the composition root; verified present at `app.py:424-430`, so production reaches the seam (not a tested-but-unwired seam).
2. AC-6 correctness depends on asserting rendered widget state rather than internal presenter state; verified the test resolves the real `ColumnsTabWidget` via `findChild` and reads `row_assignment_text`.
3. `schema_builder_dialog.py` sits at exactly 499 lines (1 below the cap); any further addition must extract a helper.

**PR readiness recommendation:** **Go** — The production fix is wired into the real control flow, AC-6 is asserted against rendered state, toolchain is green, coverage is above threshold, and no policy violations were found.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/widgets/schema_builder_dialog.py` | whole file | File is at 499 lines, 1 below the 500-line cap. | No action now; extract a helper before any future addition. | A single added line would breach the cap. | `wc -l` = 499 |
| Info | `src/gui/presenters/source_selection_presenter.py` | `read_worksheet_header_columns` | New helper is the sole production producer of the Edit-path source pool; its empty-tuple guards (blank path/sheet, empty preview) drive AC-9. | None; covered by `tests/gui/test_worksheet_header_columns.py`. | Correctness of the empty-pool seam depends on these guards. | module 100% line coverage |
| Info | `src/gui/_schema_discovery_wiring.py` | `_open_edit` getattr guard | `load_existing` is invoked via getattr to tolerate recording stubs. | None; intentional and documented. | Keeps test factories compatible without weakening production. | `test_edit_with_stub_presenter_lacking_load_existing_does_not_crash` |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The fix reuses the existing `best_header_row` scorer rather than duplicating header-detection logic; `read_worksheet_header_columns` is a thin, Qt-free helper over the injected reader and is independently unit-tested.
- The composition-root call signature was preserved: `wire_edit_schema_buttons` gained keyword presenter params with `None` defaults, so `app.py` passes the existing per-tab presenters without restructuring.
- Window-flag setup was extracted into `_schema_builder_window_setup.py`, keeping `schema_builder_dialog.py` under the cap while isolating pure Qt geometry from dialog logic.
- The cycle-0 `_seed_from_persisted_aliases` ordering is correct: it runs strictly after the live fuzzy pass and never overrides an existing `consumed_columns` entry, preserving live-match-wins and one-source-per-row.

#### Typing and API notes

- New public surface (`read_worksheet_header_columns`, `best_header_row`, `apply_schema_builder_window_flags`) is fully annotated and exported via `__all__`. Return types are precise (`tuple[str, ...]`, `PreviewSlice | None`). No `Any` introduced.

#### Error handling and logging

- No broad exception handlers added. The reader's `ValueError`-to-view policy in the presenter is unchanged. The Edit path's blank-path/sheet guard prevents calling the reader with an invalid sheet, matching the issue #50 seam. No print statements; logging unchanged.

---

## Test Quality Audit

The cycle adds targeted unit tests for each new behavior and, critically, asserts AC-6 against the
rendered widget. `test_edit_renders_matching_canonical_rows_as_assigned` constructs a real
`SchemaBuilderDialog` and real `SchemaBuilderPresenter`, emits `edit_schema_requested`, resolves the
live `ColumnsTabWidget` via `findChild`, and asserts `row_assignment_text("Customer") == "Customer"`
— the user-visible assignment label, not an internal state object. This addresses the exact gap
cycle-0 had (passing internal checks while the UI showed "(unassigned)").

### Reviewed test and QA artifacts

- `tests/gui/test_worksheet_header_columns.py` — header read, best-header-row honored, blank/empty guards (AC-5/AC-9 helper). Module 100% line coverage.
- `tests/gui/test_edit_schema_wiring.py` — AC-5 (preview slice from real headers), AC-6 (rendered assignment), AC-9 (no-file seam, no reader call), stub tolerance.
- `tests/gui/test_columns_tab_presenter.py` — AC-1/AC-2/AC-3 with live-match-wins and one-source-per-row invariants.
- `evidence/qa-gates/final-pytest-coverage.md` — executor full-suite run (1037 passed); corroborated by this audit's fresh full-suite run.

### Quality assessment prompts

- **Determinism:** Deterministic fakes for reader/service; offscreen Qt; no clock/RNG/network.
- **Isolation:** One behavior per test; fresh widgets per test via `qtbot.addWidget`.
- **Speed:** ~40s for the full 1037-test suite with coverage.
- **Diagnostics:** Equality assertions on assignment text and slice headers produce readable failure diffs.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Added-line scan; no credentials. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess in the diff. |
| Input validation at boundaries | ✅ PASS | Blank path/sheet and empty-preview guards in `read_worksheet_header_columns`. |
| Error handling remains explicit | ✅ PASS | No broad catches added; reader ValueError policy unchanged. |
| Configuration / path handling is safe | ✅ PASS | Path/sheet read from the widget selection; no filesystem writes; no real `.xlsx` in tests. |
| No confidential worksheet data committed | ✅ PASS | Scan for real AOP header tokens (GtN, Super Category, SKU Descripiton, YTD/YTG) in added `.py` lines returned NONE; tests use synthetic `Customer/SKU/Jan`. |
| No unauthorized suppressions | ✅ PASS | Added-line scan for `noqa`/`type: ignore`/`pyright: ignore` returned NONE. |

---

## Research Log

No external research was required. All findings are grounded in diff inspection, the toolchain runs
executed during this audit, and the refreshed `artifacts/python/lcov.info`.

---

## Verdict

The change is ready for normal PR flow. The cycle-1 production fix is genuinely wired into the
real Edit-Schema control flow (app.py → wiring → reader/header path → preview slice → builder →
load_existing/prepopulate), AC-6 is asserted against rendered widget state, all changed files are
within the 500-line cap, no suppressions or confidential data were introduced, and the full Python
toolchain (Black, Ruff, Pyright, Pytest with coverage) is green with no coverage regression. No
Blocker or Major findings. Recommendation: **Go**. Blocking count from this artifact: 0.
