# columns-tab-bidirectional-drag (Plan)

- **Issue:** #64
- **Issue URL:** https://github.com/drmoisan/mix-calculator/issues/64
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-15
- **Status:** Complete
- **Version:** 1.0
- **Work Mode:** minor-audit

**Fail-closed evidence rule:** Include explicit baseline artifact tasks, final-QA artifact tasks, and coverage-comparison tasks for each in-scope language when policy requires coverage. If any required baseline artifact, QA artifact, or coverage-comparison artifact is missing, the audit verdict must be BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Record the expected artifact path or location in each evidence-producing task. Do not mark evidence-backed work complete without the artifact.

**Non-overridable evidence path:** All evidence artifacts write to `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/<kind>/`. Paths under `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical root are rejected.

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record the read in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/baseline/phase0-instructions-read.md`. Required policy order: (1) `CLAUDE.md`, (2) `.claude/rules/general-code-change.md`, (3) `.claude/rules/general-unit-test.md`, (4) `.claude/rules/python.md`, (5) `.claude/rules/python-suppressions.md`. Artifact must include: `Timestamp:`, `Policy Order:`, and explicit list of files read.

- [x] [P0-T2] Run Black (format check, no write) and record outcome in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/baseline/baseline-black.md`. Command: `poetry run black --check .`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T3] Run Ruff (lint check) and record outcome in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/baseline/baseline-ruff.md`. Command: `poetry run ruff check .`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T4] Run Pyright (type check) and record outcome in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/baseline/baseline-pyright.md`. Command: `poetry run pyright`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T5] Run Pytest with coverage and record baseline numeric coverage values in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/baseline/baseline-pytest.md`. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (including overall line coverage %, branch coverage %, and pass/fail count). Numeric coverage values are mandatory; placeholder values such as `UNVERIFIED` are not permitted.

---

### Phase 1 — Production Changes: `_columns_tab_drag.py`

- [x] [P1-T1] In `src/gui/widgets/_columns_tab_drag.py`, add the module-level constant `_CANONICAL_ORIGIN_MIME = "application/x-canonical-origin"` immediately after the existing imports block. Add a short inline comment explaining its role (secondary MIME key identifying the canonical row a drag originated from). Verify the constant is placed before any class definition in the file.

- [x] [P1-T2] In `src/gui/widgets/_columns_tab_drag.py`, inside `ColumnDropRow.__init__`, add the instance variable `self._current_source: str | None = None` after the existing `__init__` setup. Update the class docstring to mention `_current_source` as the currently assigned source column (or `None` when unassigned).

- [x] [P1-T3] In `src/gui/widgets/_columns_tab_drag.py`, inside `ColumnDropRow.set_assignment`, add `self._current_source = source_column` as the first line of the method body (before the label update). When `source_column` is `None` or the unassigned sentinel value, `self._current_source` must be set to `None`. Update the method docstring to reflect this side effect.

- [x] [P1-T4] In `src/gui/widgets/_columns_tab_drag.py`, add a new method `ColumnDropRow.mouseMoveEvent(self, e: QMouseEvent) -> None`. The method must: (a) return immediately if `self._current_source is None` or the left mouse button is not held; (b) construct a `QMimeData` instance with `mime.setText(self._current_source)` and `mime.setData(_CANONICAL_ORIGIN_MIME, self.canonical.encode())`; (c) create and execute a `QDrag` instance. Add a docstring explaining the method purpose, drag-source condition, and both MIME keys set. Add `QMouseEvent` to the existing PySide6 import block if not already present.

- [x] [P1-T5] In `src/gui/widgets/_columns_tab_drag.py`, inside `ColumnsTabWidget.__init__`, add `self.setAcceptDrops(True)` and `self._on_release: Callable[[str], None] = lambda _c: None`. Import `Callable` from `collections.abc` (or `typing`) if not already imported. Update the class docstring to document `_on_release` and the pool-area drop behavior.

- [x] [P1-T6] In `src/gui/widgets/_columns_tab_drag.py`, add a new method `ColumnsTabWidget.clear_row(self, canonical: str) -> None` that calls `self._on_release(canonical)`. Add a docstring explaining that this method is monkey-patched by `DragTabBinder` to `ColumnsTabPresenter.clear_row`, mirroring the `assign_column` pattern.

- [x] [P1-T7] In `src/gui/widgets/_columns_tab_drag.py`, add a new method `ColumnsTabWidget.dragEnterEvent(self, e: QDragEnterEvent) -> None` that accepts the event only when `e.mimeData().hasText()` is `True` AND `e.mimeData().hasFormat(_CANONICAL_ORIGIN_MIME)` is `True`; otherwise ignores it. Import `QDragEnterEvent` from PySide6 if not already present. Add a docstring explaining the acceptance condition.

- [x] [P1-T8] In `src/gui/widgets/_columns_tab_drag.py`, add a new method `ColumnsTabWidget.dropEvent(self, e: QDropEvent) -> None` that: (a) reads the canonical origin with `e.mimeData().data(_CANONICAL_ORIGIN_MIME).data().decode("utf-8")`; (b) calls `self.clear_row(canonical_origin)`; (c) calls `e.acceptProposedAction()`. Add a docstring. Verify the file remains at or below 500 lines after all Phase 1 changes.

---

### Phase 2 — Production Changes: `_schema_builder_drag_tabs.py`

- [x] [P2-T1] In `src/gui/widgets/_schema_builder_drag_tabs.py`, in `DragTabBinder.__init__`, locate the existing line `columns_widget.assign_column = self._columns_presenter.assign_column`. Immediately after that line add `columns_widget.clear_row = self._columns_presenter.clear_row`. Verify line count remains at or below 500 after the change.

---

### Phase 3 — Test Changes: `tests/gui/test_columns_tab_widgets.py`

- [x] [P3-T1] In `tests/gui/test_columns_tab_widgets.py`, add test `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`. The test must: (a) instantiate a `ColumnDropRow` with a canonical name; (b) call `set_assignment` with a source column name; (c) simulate a `mouseMoveEvent` with the left mouse button held (use `monkeypatch` or a `QDrag` mock/spy to intercept the drag); (d) assert that `QDrag.setMimeData` was called with a `QMimeData` whose `text()` equals the source column and whose `data(_CANONICAL_ORIGIN_MIME)` decodes to the canonical name. This test covers AC-1 and AC-4.

- [x] [P3-T2] In `tests/gui/test_columns_tab_widgets.py`, add test `test_unassigned_row_mousemove_does_not_start_drag`. The test must: (a) instantiate a `ColumnDropRow` without calling `set_assignment`; (b) simulate a `mouseMoveEvent` with the left button held; (c) assert that no `QDrag` was started. This test covers the guard-clause branch added in P1-T4.

- [x] [P3-T3] In `tests/gui/test_columns_tab_widgets.py`, add test `test_pool_dropEvent_with_canonical_origin_calls_clear_row`. The test must: (a) instantiate a `ColumnsTabWidget`; (b) assign a recording callable to `columns_widget.clear_row`; (c) construct a `QDropEvent` (or simulate via direct method call using a fake `QMimeData`) carrying both `text/plain` and `application/x-canonical-origin` data; (d) call `ColumnsTabWidget.dropEvent` directly; (e) assert the recording callable was invoked with the expected canonical name. This test covers AC-2 and AC-4.

- [x] [P3-T4] In `tests/gui/test_columns_tab_widgets.py`, add test `test_pool_dragEnterEvent_rejects_missing_canonical_origin`. The test must: (a) instantiate a `ColumnsTabWidget`; (b) construct a fake `QMimeData` with only `text/plain` (no `application/x-canonical-origin`); (c) call `ColumnsTabWidget.dragEnterEvent` with a fake drag-enter event wrapping that MIME data; (d) assert the event was NOT accepted (i.e., `e.isAccepted()` is `False` or the event object shows it was ignored). This test covers the negative path of P1-T7.

---

### Phase 4 — Full QA Loop

Run the toolchain in the order below. If any step fails or auto-modifies files, restart from step 1 and repeat until all four steps pass in a single uninterrupted pass.

- [x] [P4-T1] Run Black (write mode) and record outcome in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/qa-black.md`. Command: `poetry run black .`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. If Black rewrites any file, return to P4-T1.

- [x] [P4-T2] Run Ruff (check mode) and record outcome in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/qa-ruff.md`. Command: `poetry run ruff check .`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. If Ruff reports errors, fix them and return to P4-T1.

- [x] [P4-T3] Run Pyright and record outcome in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/qa-pyright.md`. Command: `poetry run pyright`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. If Pyright reports type errors, fix them and return to P4-T1.

- [x] [P4-T4] Run Pytest with branch coverage and record post-change numeric coverage values in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/qa-pytest.md`. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Artifact must include: `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (overall line coverage %, branch coverage %, pass/fail count). Numeric values are mandatory. If any test fails, fix the failure and return to P4-T1.

- [x] [P4-T5] Verify coverage thresholds and record a coverage-comparison artifact in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/qa-coverage-comparison.md`. The artifact must record: baseline line coverage % (from P0-T5), post-change line coverage % (from P4-T4), baseline branch coverage % (from P0-T5), post-change branch coverage % (from P4-T4). Assert line coverage >= 85% and branch coverage >= 75%. Assert no regression on changed lines. If either threshold is not met, remediate and return to P4-T1.

---

### Phase 5 — Acceptance Criteria Verification

- [x] [P5-T1] Verify AC-1 (re-assign via drag): confirm P3-T1 passes and the `mouseMoveEvent` test exercises both MIME keys, demonstrating that dragging an assigned source onto another canonical row would re-assign it via the existing `assign_column` path. Record finding in `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/ac-verification.md`.

- [x] [P5-T2] Verify AC-2 (unassign via pool drop): confirm P3-T3 passes and demonstrates that `ColumnsTabWidget.dropEvent` calls `clear_row` with the correct canonical name. Record finding in the same `ac-verification.md` artifact.

- [x] [P5-T3] Verify AC-3 (no regression on pool-to-row drag): confirm the existing pool-to-row drag tests remain green in the P4-T4 run (no pre-existing tests deleted or weakened). Record finding in the same `ac-verification.md` artifact.

- [x] [P5-T4] Verify AC-4 (test coverage of new paths): confirm all four new tests from Phase 3 are present, named correctly, and passed in the P4-T4 run. Record finding in the same `ac-verification.md` artifact.
