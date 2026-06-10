# Code Review: edit-schema-columns-assignment (#62, Cycle 1 re-review R4)

**Review Date:** 2026-06-10
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62`
**Feature Folder Selection Rule:** Folder suffix `-62` matches the canonical issue number and the branch name `fix/edit-schema-columns-assignment`.
**Base Branch:** `main` (merge-base `f7aea0f`)
**Head Branch:** `fix/edit-schema-columns-assignment` (head `150d42a`)
**Review Type:** Post-remediation re-review (cycle 1)

---

## Executive Summary

Cycle 0 delivered alias-seeding (AC-1..AC-4) that passed local audit and CI but did not fix the user-observable defect: the bundled default schemas carry empty aliases and the "Edit Schema" button opened the schema builder with no source-column pool, so every canonical column rendered "(unassigned)". Cycle 1 fixes the real production behavior and adds two adjacent UI requirements requested by the user.

The implementation is well-scoped and reuses existing seams. The header read is delegated to a new module-level `read_worksheet_header_columns` that reuses the schema-discovery `best_header_row` path (no duplicated header logic), honoring the detected header row. The Edit wiring builds a live `preview_slice` and passes it through `open_schema_builder(..., preview_slice=...)`; the binder retains the slice and `prepopulate()` fuzzy-matches canonical columns to the real headers. The window-flag setup is extracted to a small new module to keep `schema_builder_dialog.py` under the 500-line cap, and the Columns tab is wrapped in a resizable `QScrollArea`.

**What changed:**
- `_schema_discovery_wiring.py`: `wire_edit_schema_buttons` now accepts per-tab presenters, builds `_build_edit_preview_slice` from the selected worksheet headers, and passes the slice into the shared open path before `load_existing`.
- `source_selection_presenter.py`: new `read_worksheet_header_columns` reusing `best_header_row`, with the issue #50 no-file/no-sheet guard.
- `_columns_tab_presenter.py`: `_seed_from_persisted_aliases` (cycle-0 fallback retained, live-match-wins).
- `_schema_builder_tabs.py`: Columns tab wrapped in `QScrollArea(setWidgetResizable(True))`.
- `_schema_builder_window_setup.py` (new) + `schema_builder_dialog.py`: resizable window with min/max/close flags.
- `_columns_tab_drag.py`: `assignment_text`/`row_assignment_text` test seams.

**Top 3 risks:**
1. The Edit path depends on the composition root (`app.py`) passing the reader-carrying presenters into `wire_edit_schema_buttons`; verified present, so the seam is wired (not tested-only).
2. The AC-6 render assertion depends on the fuzzy threshold matching exact-name headers; verified by an end-to-end test through the real binder.
3. The seeded preview slice carries unmasked real headers; this is the worksheet header row (column names), not sample data values, and is consistent with the existing discovery flow.

**PR readiness recommendation:** **Go** — The production call-site wiring is verified end-to-end, the toolchain is clean, coverage does not regress, and no file-size or confidentiality issues were found.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/_schema_discovery_wiring.py` | `_build_edit_preview_slice` / `wire_edit_schema_buttons` | Edit path builds a live `preview_slice` from real headers and passes it into the shared open path; production composition root in `app.py` supplies the reader-carrying presenters. | None. | Confirms the cycle-0 "tested-but-unwired" gap is closed at the production call site. | `app.py:330-343,424-431`; `_schema_discovery_wiring.py:107-113,264-336`; test `test_edit_renders_matching_canonical_rows_as_assigned` |
| Info | `src/gui/presenters/source_selection_presenter.py` | `read_worksheet_header_columns` | Header read reuses `best_header_row` (no duplicated header logic) and honors the detected header row; blank path/sheet returns `()` with no reader call. | None. | Satisfies AC-5 and preserves the issue #50 no-file/no-sheet seam (AC-9). | `source_selection_presenter.py:104-156`; test `test_worksheet_header_columns.py` |
| Info | `src/gui/widgets/_schema_builder_tabs.py` | `build_columns_tab` | Columns tab wrapped in `QScrollArea` with `setWidgetResizable(True)`; the bundle still exposes the real `ColumnsTabWidget` so binder wiring is unchanged. | None. | Satisfies AC-7 without breaking existing binder/test seams. | `_schema_builder_tabs.py:191-203` |
| Info | `src/gui/widgets/_schema_builder_window_setup.py` | `apply_schema_builder_window_flags` | New module sets `Qt.Window | Minimize | Maximize | Close` hints and a default size; keeps the dialog file under the cap. | None. | Satisfies AC-8; respects the 500-line cap design constraint. | `_schema_builder_window_setup.py:36-61`; `schema_builder_dialog.py:88-91` |
| Info | `src/gui/presenters/_columns_tab_presenter.py` | `_seed_from_persisted_aliases` | Cycle-0 alias-seeding retained as a fallback; runs strictly after the live fuzzy pass (live-match-wins) and seeds at most one alias per row. | None. | Preserves AC-1..AC-4 and the one-source-per-row invariant (AC-3). | `_columns_tab_presenter.py:105-156` |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The header read is factored as a single reusable function (`read_worksheet_header_columns`) shared by both discovery and the Edit path, avoiding the divergence between the build and edit buttons that caused the cycle-0 defect.
- Window-flag setup is isolated in its own module, keeping `schema_builder_dialog.py` at 499 lines (under the cap) while remaining cohesive.
- The Edit wiring uses the established getattr seam pattern (`getattr(retained, "load_existing", None)`), keeping recording test stubs compatible.

#### Typing and API notes

- New public function returns `tuple[str, ...]`; the slice builder returns `PreviewSlice | None`. No `Any`. `apply_schema_builder_window_flags` accepts a `QDialog` (extensible). Pyright reports 0 errors on `src/gui`.

#### Error handling and logging

- No broad catches added. Blank/empty inputs return early (empty tuple or `None` slice) rather than raising, which is the AC-9 graceful-degradation contract. The existing module logger is retained; no `print`.

---

## Test Quality Audit

The verification evidence is strong for a GUI change. The AC-6 test exercises the real dialog, presenter, and binder rather than fakes, asserting the rendered assignment label per canonical row — directly addressing the cycle-0 failure mode where fake-based unit tests passed but production did not render.

### Reviewed test and QA artifacts

- `tests/gui/test_edit_schema_wiring.py` — AC-5 (preview-slice seeded from real headers), AC-6 (end-to-end render assignment through the real binder), AC-9 (no reader call / `None` slice on blank selection; placeholder short-circuit; stub-presenter tolerance).
- `tests/gui/test_worksheet_header_columns.py` (new) — header read positive/negative/edge with synthetic data.
- `tests/gui/test_schema_builder_dialog.py` — AC-8 window flags.
- `tests/gui/test_columns_tab_widgets.py`, `tests/gui/test_columns_tab_presenter.py` — AC-7 scroll-area wrap and retained alias-seeding behavior.
- `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/qa-gates/final-pytest-coverage.md` — repo-wide and changed-file coverage; reviewer independently re-ran the full suite (1037 passed) and changed-module coverage.

### Quality assessment prompts

- **Determinism:** Offscreen Qt; synthetic fake reader/service; no wall-clock/RNG/network.
- **Isolation:** One AC per test; separate tests for reader-seeding, render-assignment, and no-reader-call.
- **Speed:** Changed-scope subset 65 tests in 1.37s; full suite 43.64s.
- **Diagnostics:** Assertions read the user-facing `row_assignment_text` and `reader.preview_calls`, so a failure localizes to the render/seam.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | No credentials/secrets in changed files. |
| No unsafe subprocess or command construction | PASS | No subprocess/shell usage in changed GUI code. |
| Input validation at boundaries | PASS | `read_worksheet_header_columns` guards blank path/sheet and empty preview before indexing. |
| Error handling remains explicit | PASS | Early returns for degenerate inputs; getattr guard tolerates absent `load_existing`; no broad catches added. |
| Configuration / path handling is safe | PASS | Paths come from the widget's current selection; no path concatenation or traversal introduced. |
| No confidential worksheet data committed | PASS | Branch-changed source/test files use synthetic tokens ("Acme", "Customer", "Sales", "HEADER"); AOP-specific header tokens appear only in pre-existing schema/fixture files predating the merge-base. |

---

## Research Log

No external research was required. All findings are grounded in diff inspection, the composition-root trace in `app.py`, the binder/`open_schema_builder` seam, and reviewer-run toolchain output.

---

## Verdict

The cycle-1 change closes the real production defect at the verified call site and delivers the two adjacent UI requirements (scrollable Columns tab, resizable window with min/max/close). The toolchain is clean, coverage does not regress, all changed files are within the 500-line cap, and no confidentiality or evidence-location violations were found. The change is ready for normal PR flow. blocking_count = 0 for this artifact.
