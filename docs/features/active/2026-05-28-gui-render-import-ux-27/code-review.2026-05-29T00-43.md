# Code Review: gui-render-import-ux (Issue #27)

**Review Date:** 2026-05-29
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-05-28-gui-render-import-ux-27`
**Feature Folder Selection Rule:** Folder suffix `-27` matches issue #27 (the author-asserted autoclose issue) and contains the material scoping-doc changes (`spec.md`, `user-story.md`).
**Base Branch:** `main` (`8ea722e8a8c904732910c669fe0e79c95a10f68c`)
**Head Branch:** `mix-calculator-wt-2026-05-28-23-17` (`5b4266c238c0a1a7a797a067c2dce524b178a706`)
**Review Type:** Initial review

---

## Executive Summary

This change delivers the four issue #27 GUI usability improvements: single-selection Render-tab checkboxes, off-UI-thread import dispatch through the existing `RunnerProtocol` seam, status-bar completion messages for import-one and import-all, and relocation of the per-input Import buttons into their `SourceInputWidget`. The implementation is confined to the GUI presentation and composition layers and introduces no transform, loader, or persistence change. The branch diff is 2,792 insertions / 139 deletions across 29 files (14 Python source/test, 15 docs/evidence), in a single commit.

**What changed:**
Three new modules — `_render_exclusivity.py` (checkbox wiring), `_import_dispatch_wiring.py` (import signal-to-runner wiring), and `presenters/import_dispatch.py` (pure task-building and success/error callbacks behind an `ImportDispatchContext` protocol). `app.py` wires the new helpers at the composition root; `main_window.py` removes per-input Import buttons from the global control row and re-exports them as widget-owned properties; `pipeline_presenter.py` gains thin delegating methods onto `import_dispatch`; `source_input_widget.py` gains an optional in-widget Import button exposed via `import_btn`. The off-thread dispatch reuses the unchanged `ThreadedRunner`/`PipelineWorker` and `SynchronousRunner` test seam.

**Top 3 risks:**
1. Off-thread responsiveness (AC for "window remains responsive") is verified deterministically through `SynchronousRunner`, not by a live `ThreadedRunner` UI-thread observation; the production responsiveness claim rests on reuse of the unchanged threaded path. This is the spec's intended verification model and is acceptable, but no end-to-end threaded responsiveness test exists.
2. `app.py` (497 lines) and `pipeline_presenter.py` (490 lines) are close to the 500-line cap; future additions to either will require further extraction.
3. The `import_btn` property raises `AttributeError` when a widget is constructed without `import_label`; callers that assume a button always exists would fail at access time rather than construction. In this feature all three widgets are constructed with labels, so the path is safe, but the contract is access-time, not construction-time.

**PR readiness recommendation:** **Go** — All 14 acceptance criteria are satisfied with passing tests, the toolchain is clean, coverage exceeds thresholds, and no blocking or major findings were identified.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/app.py` | whole file (497 lines) | File is within 3 lines of the 500-line cap. | Monitor on future change; the dispatch extraction already mitigates this. | Headroom is small; the next addition may breach the cap. | `wc -l src/gui/app.py` = 497 |
| Info | `src/gui/presenters/pipeline_presenter.py` | whole file (490 lines) | File is within 10 lines of the 500-line cap. | Continue delegating new logic to `import_dispatch`/helper modules. | Limited headroom for future presenter growth. | `wc -l` = 490 |
| Nit | `src/gui/widgets/source_input_widget.py` | `import_btn` property, lines 137-159 | Accessing `import_btn` on a widget built without `import_label` raises `AttributeError` at access time. | Acceptable as designed; the docstring documents it. Optionally promote to a construction-time invariant if a label-less widget is ever wired to an import action. | Access-time failure is later than construction-time failure, but the only constructed widgets all supply labels. | Code inspection; all three `MainWindow` widgets pass `import_label`. |
| Info | `tests/` | n/a | No live `ThreadedRunner` responsiveness test; off-thread behavior verified via `SynchronousRunner`. | None required; matches spec's deterministic verification model. | The threaded path is unchanged and reused; deterministic seam testing is the repo's determinism policy. | `spec.md` Test Strategy / Determinism section |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The off-thread dispatch reuses the existing `RunnerProtocol`/`ThreadedRunner`/`PipelineWorker` seam without modifying it, mirroring the established Run-path task/callback structure. This keeps the change small and consistent with prior architecture.
- Cross-cutting Qt wiring (checkbox exclusivity, import dispatch) is correctly placed at the composition root rather than inside presenters or widgets, preserving the MVP passive-view boundary stated in the spec.
- The `blockSignals(True)`/`setChecked(False)`/`blockSignals(False)` guard spans exactly the displaced uncheck, so the displaced box emits no `toggled(False)` and the preview-clear closure does not fire — directly satisfying AC2 and keeping the zero-checked state reachable (AC3). The decision to avoid `QButtonGroup` is documented with rationale.
- Dispatch logic was extracted into `import_dispatch.py` behind an `ImportDispatchContext` Protocol, decoupling it from the concrete presenter and keeping `pipeline_presenter.py` under the 500-line cap while preserving encapsulation.
- Busy-state handling is consistent: `set_busy(True)` at dispatch in the wiring layer, `set_busy(False)` in every success and error callback, with the documented ordering (clear busy before recomputing `can_run`).

#### Typing and API notes

- All new public functions carry complete type hints; `Callable[[], dict[str, pd.DataFrame]]` task signatures match the runner contract. No `Any` introduced. Pyright reports 0 errors.
- The new public surface (`make_import_one_task`, `on_import_one_success`, `on_import_all_success`, etc.) grows the presenter API additively without breaking existing callers; `PipelineViewProtocol` is unchanged.
- `MainWindow.import_le_btn`/`import_aop_btn`/`import_skulu_btn` are re-exposed as read-only properties delegating to the widget-owned buttons, preserving the `set_import_button_enabled` attribute contract (AC13).

#### Error handling and logging

- Only `ValueError` is caught at the dispatch boundary and routed to `show_error`; `KeyError` for an unknown import key propagates, so genuine misuse is not masked. This matches the repo's fail-fast policy.
- `pipeline_presenter` logs import actions through `logging.getLogger(__name__)`; no `print` statements were added.
- `wire_render_checkboxes` raises `ValueError` on a checkbox/callback length mismatch, enforcing the pairing invariant at wiring time.

---

## Test Quality Audit

The reviewer independently re-ran the full toolchain. Black, Ruff, and Pyright are clean; Pytest reports 444 passed / 0 failed with repo-wide coverage 99.38% line and 99.69% branch. The new and modified Python modules are at 100% line+branch coverage except `source_input_widget.py` (97%; the two uncovered lines are in the pre-existing `set_current_sheet` append branch, untouched by this feature).

### Reviewed test and QA artifacts

- `tests/gui/test_app_wiring_render.py` — verifies single-selection (AC1), no-spurious-clear on displacement (AC2), zero-checked reachability (AC3), and a direct unit test of the pure exclusivity guard, plus the length-mismatch ValueError. Deterministic, headless.
- `tests/gui/test_app_wiring_dispatch.py` — proves import-one/import-all dispatch through the injected runner (not the synchronous path) using a `_RecordingRunner` that records but does not run the task (AC4, AC5).
- `tests/gui/integration/test_behavioral_import_buttons.py` — fully-wired `SynchronousRunner` tests for button enable/disable, error routing, busy clear, and completion messages (AC6–AC10).
- `docs/.../evidence/qa-gates/pytest-coverage.2026-05-29T00-34.md` and `coverage-delta.2026-05-29T00-34.md` — executor coverage evidence; confirmed against the reviewer's re-run.

### Quality assessment prompts

- **Determinism:** `SynchronousRunner` makes dispatch run in-process before assertions; exclusivity is asserted by checkbox state and the absence of spurious clear-preview calls, not by timing. No sleeps or real threads in tests.
- **Isolation:** Each test targets a single behavior with an AC-tagged docstring.
- **Speed:** 444 tests in 20.06s (reviewer run).
- **Diagnostics:** Assertions compare exact status text and boolean enabled states, producing actionable failures.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff inspection; no credentials or tokens added. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess use in the diff; pure Qt signal wiring and pandas frames. |
| Input validation at boundaries | ✅ PASS | `wire_render_checkboxes` validates list-length pairing; unknown import keys raise `KeyError`. |
| Error handling remains explicit | ✅ PASS | Only `ValueError` caught at the dispatch boundary; other exceptions propagate. |
| Configuration / path handling is safe | ✅ PASS | `resolve_path_for_key` routes spec fields without filesystem mutation; SKU_LU path falls back to LE path deterministically. |

---

## Research Log

No external research was required. The review relied on the branch diff, the PR-context artifacts (`artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`), the feature scoping docs, the executor evidence artifacts, and an independent toolchain re-run.

---

## Verdict

The change is ready for normal PR flow. It implements all four issue #27 changes cleanly within the MVP passive-view architecture, reuses the existing runner seam without modification, and is supported by deterministic behavioral and unit tests at high coverage. The toolchain passes clean in a single pass and no suppressions were introduced. The only observations are informational (two files near the 500-line cap and a documented access-time `AttributeError` on `import_btn` for label-less widgets, which no current caller triggers). This conclusion is consistent with the Findings Table (no Blocker or Major findings) and the Go recommendation above.
