# Feature Audit: gui-render-import-ux (Issue #27)

**Audit Date:** 2026-05-29
**Feature Folder:** `docs/features/active/2026-05-28-gui-render-import-ux-27`
**Base Branch:** `main`
**Head Branch:** `mix-calculator-wt-2026-05-28-23-17`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `8ea722e8a8c904732910c669fe0e79c95a10f68c`)
- **Head branch/commit:** `mix-calculator-wt-2026-05-28-23-17` (commit `5b4266c238c0a1a7a797a067c2dce524b178a706`)
- **Merge base:** `8ea722e8a8c904732910c669fe0e79c95a10f68c`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-05-28-gui-render-import-ux-27/evidence/` (`baseline/`, `qa-gates/`)
  - Additional evidence: reviewer-regenerated `artifacts/python/lcov.info`; independent toolchain re-run
- **Feature folder used:** `docs/features/active/2026-05-28-gui-render-import-ux-27`
- **Requirements source:** `spec.md` and `user-story.md` (full-feature mode); `issue.md` mirrors the 14 spec criteria.
- **Work mode resolution note:** `issue.md` carries `- Work Mode: full-feature`, so the authoritative AC sources are `spec.md` and `user-story.md` per the work-mode contract.
- **Scope note:** Audit scope is the full branch diff vs base `main`. Only Python files are changed. PR context was confirmed fresh (generated 2026-05-29 04:39 UTC against the current head SHA).

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `spec.md` — primary source (Acceptance Criteria AC1–AC14)
- `user-story.md` — primary source (Given/When/Then scenarios 1.1–4.3)

### Acceptance criteria (from spec.md)

1. AC1: Checking any one Render-tab checkbox (LE, AOP, or SKU_LU) unchecks the other two, leaving exactly one checked.
2. AC2: Programmatically unchecking the two displaced checkboxes during an exclusivity switch does not invoke `on_clear_preview` and does not clear the preview produced by the newly-checked widget.
3. AC3: The user can uncheck the currently-active Render-tab checkbox, leaving all three unchecked (zero-checked state) and clearing the shared preview.
4. AC4: Per-input import is dispatched through the injected `RunnerProtocol` (verified deterministically with `SynchronousRunner`), not called directly on the presenter from the signal handler.
5. AC5: Import-all is dispatched through the injected `RunnerProtocol` (verified deterministically with `SynchronousRunner`).
6. AC6: A successful import disables its keyed import button; a failed import (loader `ValueError`) leaves the keyed import button enabled and routes the message to `show_error`.
7. AC7: A successful import invalidates the derived-table set so a downstream Run rebuilds.
8. AC8: The view reflects a busy state while an import is in flight and returns to idle on completion (success or error).
9. AC9: A successful import-one displays a factual completion message in the status bar via `show_result` (for example `"Imported LE."`).
10. AC10: A successful import-all displays a factual completion message in the status bar via `show_result` (for example `"Imported all 3 sources."`).
11. AC11: Each per-input Import button renders inside its `SourceInputWidget`, and `SourceInputWidget` exposes the button via an `import_btn` attribute.
12. AC12: Import All remains in the global control row, and the three per-input Import buttons are absent from the global control row.
13. AC13: `MainWindow.import_le_btn`, `import_aop_btn`, and `import_skulu_btn` resolve to the widget-owned buttons so `MainWindowPipelineView.set_import_button_enabled` and existing tests work unchanged.
14. AC14: The toolchain passes (format -> lint -> type-check -> test) with line coverage >= 85% and branch coverage >= 75%, no regression on changed lines.

### From user-story.md

- Story 1 (1.1 check unchecks others; 1.2 switching does not clear new preview; 1.3 zero-checked reachable) maps to AC1–AC3.
- Story 2 (2.1 per-input dispatch; 2.2 import-all dispatch; 2.3 failed import surfaces error and allows retry; 2.4 busy state; 2.5 derived tables invalidated) maps to AC4–AC8.
- Story 3 (3.1 import-one message; 3.2 import-all message; 3.3 error path unchanged) maps to AC9, AC10, AC6.
- Story 4 (4.1 button inside widget; 4.2 Import All in control row; 4.3 enable/disable contract preserved) maps to AC11–AC13.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC1 single-selection | PASS | `_render_exclusivity.wire_render_exclusivity` unchecks others on check-to-True; tests `test_build_application_checking_aop_after_le_unchecks_le_and_skulu`, `test_build_application_checking_each_box_in_turn_leaves_only_that_box`, `test_wire_render_exclusivity_unit_unchecks_others_on_check`. | `pytest tests/gui/test_app_wiring_render.py` | Wired in `app.py` via `wire_render_checkboxes`. |
| 2 | AC2 no spurious clear on displacement | PASS | `blockSignals` guards span the displaced `setChecked(False)` so no `toggled(False)` fires; test `test_build_application_displaced_uncheck_does_not_clear_new_preview` asserts the preview survives. | `pytest tests/gui/test_app_wiring_render.py` | Preview-clear wired before exclusivity. |
| 3 | AC3 zero-checked reachable + clear | PASS | Exclusivity is a no-op on `toggled(False)`; preview-clear closure fires on uncheck; test `test_build_application_uncheck_active_box_clears_preview_zero_checked` asserts all unchecked and preview cleared. | `pytest tests/gui/test_app_wiring_render.py` | |
| 4 | AC4 import-one through runner | PASS | `_import_dispatch_wiring._handle_import_one` builds the task and calls `runner.run`; test `test_import_one_dispatches_through_runner_not_synchronous_path` with `_RecordingRunner` proves no synchronous import ran. | `pytest tests/gui/test_app_wiring_dispatch.py` | |
| 5 | AC5 import-all through runner | PASS | `_handle_import_all` dispatches via `runner.run`; test `test_import_all_dispatches_through_runner_not_synchronous_path`. | `pytest tests/gui/test_app_wiring_dispatch.py` | |
| 6 | AC6 success disables / failure keeps enabled + show_error | PASS | `handle_import_one_success` calls `set_import_button_enabled(name, False)`; error path re-enables and routes to `show_error`. Tests `test_import_le_disables_button_on_success`, `test_le_failure_leaves_button_enabled`, `test_le_failure_routes_message_to_status_bar`. | `pytest tests/gui/integration/test_behavioral_import_buttons.py` | |
| 7 | AC7 derived-table invalidation | PASS | `record_one_import_result`/`record_all_import_result` set `self._derived_tables = {}`. Covered by presenter unit tests at 100%; behavioral imports re-enable Run via `can_run`. | `pytest tests/gui/test_pipeline_presenter.py` | |
| 8 | AC8 busy in flight / idle on completion | PASS | `set_busy(True)` at dispatch (wiring) and in `run_import_*_sync`; `set_busy(False)` in all four callbacks. Test `test_import_one_clears_busy_after_completion` and `test_import_all_failure_clears_busy_and_leaves_buttons_enabled`. | `pytest tests/gui/integration/test_behavioral_import_buttons.py` | Deterministic via `SynchronousRunner`; production responsiveness rests on the unchanged threaded path. |
| 9 | AC9 import-one completion message | PASS | `handle_import_one_success` emits `view.show_result(f"Imported {name}.")`; test `test_import_one_success_shows_completion_message` asserts status `"Imported LE."`. | `pytest tests/gui/integration/test_behavioral_import_buttons.py` | |
| 10 | AC10 import-all completion message | PASS | `handle_import_all_success` emits `"Imported all 3 sources."`; test `test_import_all_success_shows_completion_message`. | `pytest tests/gui/integration/test_behavioral_import_buttons.py` | |
| 11 | AC11 button inside widget + `import_btn` | PASS | `SourceInputWidget.__init__` constructs the optional Import button and adds it to the layout; `import_btn` property exposes it. `MainWindow` builds all three with `import_label`. Covered by `test_source_input_widget.py`. | `pytest tests/gui/test_source_input_widget.py` | |
| 12 | AC12 Import All in control row, per-input absent | PASS | `main_window.py` `controls_row` adds only `import_all_btn`, Run/Save/Open/Export; per-input buttons live in widgets. Test `test_main_window.py` additions verify layout. | `pytest tests/gui/test_main_window.py` | |
| 13 | AC13 `import_*_btn` properties resolve to widget buttons | PASS | `MainWindow.import_le_btn`/`import_aop_btn`/`import_skulu_btn` delegate to `self.<widget>.import_btn`; `set_import_button_enabled` adapter unchanged. Existing adapter tests pass. | `pytest tests/gui` | |
| 14 | AC14 toolchain clean + coverage thresholds | PASS | Black clean, Ruff clean, Pyright 0 errors, Pytest 444 passed. Repo-wide 99.38% line / 99.69% branch; new modules 100%; no regression on changed lines. Independently re-run by reviewer. | `black --check .`; `ruff check .`; `pyright`; `pytest --cov --cov-branch` | |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 14 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Optional: add a live `ThreadedRunner` end-to-end test observing UI-thread responsiveness during a slow import, to complement the deterministic `SynchronousRunner` verification.
2. Optional: track `app.py` (497) and `pipeline_presenter.py` (490) against the 500-line cap on future change.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All 14 criteria evaluated as PASS. The `issue.md` `## Acceptance Criteria` section already shows AC1–AC14 checked `[x]` (delivered by the executor); the reviewer confirms each is satisfied and leaves them checked.
- `spec.md` and `user-story.md` use a numbered/prose format; their AC checkboxes were left as authored (the spec list uses `- [ ]` sub-items under numbered entries). Reviewer status is recorded here rather than rewriting those source files.

### AC Status Summary

- Source: `docs/features/active/2026-05-28-gui-render-import-ux-27/issue.md` (mirror of spec AC1–AC14); authoritative full-feature sources `spec.md` and `user-story.md`
- Total AC items: 14
- Checked off (delivered): 14
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 14 | 14 | 0 | Checkbox-backed; AC1–AC14 already `[x]`, confirmed by reviewer |
| `spec.md` | 14 | 14 (status recorded here) | 0 | Numbered list with `- [ ]` sub-items; not rewritten; all PASS |
| `user-story.md` | 14 scenarios | 14 (status recorded here) | 0 | Prose Given/When/Then; not checkbox-backed; all mapped scenarios PASS |
