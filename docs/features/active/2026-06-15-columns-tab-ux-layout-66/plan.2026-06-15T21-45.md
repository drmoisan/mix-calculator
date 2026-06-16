# columns-tab-ux-layout (Plan)

- **Issue:** #66
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-15T21-45
- **Status:** Complete
- **Version:** 1.0

**Work Mode:** minor-audit

**Fail-closed evidence rule:** Include explicit baseline artifact tasks, final-QA artifact tasks, and coverage-comparison tasks for each in-scope language when policy requires coverage. If any required baseline artifact, QA artifact, or coverage-comparison artifact is missing, the audit verdict must be BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Record the expected artifact path or location in each evidence-producing task. Do not mark evidence-backed work complete without the artifact.

**Evidence path root:** `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/`

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record completion in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/baseline/phase0-instructions-read.md`. Required reads: (1) `CLAUDE.md`, (2) `.claude/rules/general-code-change.md`, (3) `.claude/rules/general-unit-test.md`, (4) `.claude/rules/python.md`, (5) `.claude/rules/python-suppressions.md`, (6) `.claude/rules/quality-tiers.md`. Artifact must include `Timestamp:`, `Policy Order:`, and an explicit list of files read.

- [x] [P0-T2] Run Black formatter baseline and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/baseline/black-baseline.md`. Command: `poetry run black --check .`. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T3] Run Ruff linter baseline and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/baseline/ruff-baseline.md`. Command: `poetry run ruff check .`. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T4] Run Pyright type-check baseline and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/baseline/pyright-baseline.md`. Command: `poetry run pyright`. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P0-T5] Run Pytest with coverage baseline and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/baseline/pytest-baseline.md`. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` with numeric line-coverage % and branch-coverage % values for the overall suite and for the files in scope (`src/gui/widgets/_columns_tab_drag.py`, `tests/gui/test_columns_tab_widgets.py`).

---

### Phase 1 — Create `ColumnAssignmentSlot` in New File

- [x] [P1-T1] Create `src/gui/widgets/_column_assignment_slot.py` (new file, target ~100 lines). The file must define module-level constant `CANONICAL_ORIGIN_MIME = "application/x-canonical-origin"` with a brief module docstring describing the slot widget's purpose. Confirm the file does not exist before creating.

- [x] [P1-T2] In `src/gui/widgets/_column_assignment_slot.py`, add imports: `from __future__ import annotations`, `from typing import TYPE_CHECKING`, Qt/PySide6 imports (`QDrag`, `QMimeData`, `Qt`, `QFrame`, `QHBoxLayout`, `QLabel`, `QPushButton`, `QWidget`), and `TYPE_CHECKING`-guarded imports for `Callable`, `QMouseEvent`, `QDragEnterEvent`, `QDropEvent`.

- [x] [P1-T3] In `src/gui/widgets/_column_assignment_slot.py`, define `class ColumnAssignmentSlot(QFrame)` with a class docstring covering purpose, responsibilities, attributes (`canonical`, `_current_source`, `_on_drop`, `_placeholder`, `_button`), and lifecycle. Add `__all__ = ["CANONICAL_ORIGIN_MIME", "ColumnAssignmentSlot"]`.

- [x] [P1-T4] In `ColumnAssignmentSlot.__init__`, implement the constructor with signature `(self, canonical: str, on_drop: Callable[[str, str], None], parent: QWidget | None = None) -> None`. Store `self.canonical`, `self._on_drop`, and `self._current_source: str | None = None`. Set `self.setAcceptDrops(True)`. Build `QHBoxLayout(self)` with `setContentsMargins(4, 2, 4, 2)`. Create `self._placeholder = QLabel("(drop here)")` centered. Create `self._button = QPushButton("")` with assigned styling `"background: #5c88d4; color: white; border-radius: 3px; padding: 2px 6px;"` and hide it (`self._button.setVisible(False)`). Add both to the layout. Apply the unassigned slot stylesheet: `"ColumnAssignmentSlot { border: 2px dashed #aaa; border-radius: 4px; min-height: 26px; }"`.

- [x] [P1-T5] In `ColumnAssignmentSlot`, implement `set_assignment(self, source: str | None) -> None`. When `source` is not `None`: set `self._current_source = source`, update `self._button.setText(source)`, show the button (`self._button.setVisible(True)`), hide the placeholder, apply assigned slot stylesheet `"ColumnAssignmentSlot { border: 2px solid #4a75c0; border-radius: 4px; min-height: 26px; background: #e8f0fd; }"`. When `source` is `None`: set `self._current_source = None`, hide the button, show the placeholder, restore unassigned slot stylesheet. Add a docstring covering purpose, args, side effects.

- [x] [P1-T6] In `ColumnAssignmentSlot`, implement `assignment_text(self) -> str`. Return `self._current_source` when assigned, else `"(drop here)"`. Add a docstring.

- [x] [P1-T7] In `ColumnAssignmentSlot`, implement `dragEnterEvent(self, e: QDragEnterEvent) -> None`. Accept when `e.mimeData().hasText()`. Add a docstring covering that this accepts both pool-token drags and assigned-slot re-drags because both carry `text/plain`.

- [x] [P1-T8] In `ColumnAssignmentSlot`, implement `dropEvent(self, e: QDropEvent) -> None`. Call `self._on_drop(e.mimeData().text(), self.canonical)` then `e.acceptProposedAction()`. Add a docstring noting the single-seam delegation to the presenter callback.

- [x] [P1-T9] In `ColumnAssignmentSlot`, implement `mouseMoveEvent(self, e: QMouseEvent) -> None`. Guard: no-op when `self._current_source is None` or left button not held. When active: construct `QDrag(self)`, build `QMimeData` with `setText(self._current_source)` and `setData(CANONICAL_ORIGIN_MIME, self.canonical.encode())`, call `drag.exec(Qt.DropAction.MoveAction)`. Add a docstring describing the two-MIME-key payload and when the drag is suppressed.

- [x] [P1-T10] Verify `src/gui/widgets/_column_assignment_slot.py` is at most 500 lines by counting the file's line count after all content is written.

---

### Phase 2 — Modify `_columns_tab_drag.py`

- [x] [P2-T1] In `src/gui/widgets/_columns_tab_drag.py`, replace the `CANONICAL_ORIGIN_MIME` constant definition and its comment block (lines 53-57) with a re-import: `from src.gui.widgets._column_assignment_slot import CANONICAL_ORIGIN_MIME`. Add `ColumnAssignmentSlot` to the same import line. Keep `CANONICAL_ORIGIN_MIME` in `__all__` so tests that import it from `_columns_tab_drag` continue to resolve it.

- [x] [P2-T2] In `src/gui/widgets/_columns_tab_drag.py`, update the top-level imports block to add `QFrame` and `QHBoxLayout` to the `PySide6.QtWidgets` import (needed for any remaining usage) and confirm `QVBoxLayout` remains present for `ColumnsTabWidget` outer layout; remove `QVBoxLayout` only if no usage remains after Phase 2 changes.

- [x] [P2-T3] In `ColumnDropRow.__init__` in `src/gui/widgets/_columns_tab_drag.py`, remove `self.setAcceptDrops(True)` (the slot handles drops), remove `self._assignment = QLabel("(unassigned)")`, replace `layout = QVBoxLayout(self)` with `row = QHBoxLayout(self)` with `row.setContentsMargins(4, 2, 4, 2)` and `row.setSpacing(8)`. Add `self._slot = ColumnAssignmentSlot(canonical, on_drop)`. Replace the three `layout.addWidget(...)` calls with `row.addWidget(self._label, 2)`, `row.addWidget(self._slot, 1)`, `row.addWidget(self._indicator, 0)`.

- [x] [P2-T4] In `ColumnDropRow.set_assignment` in `src/gui/widgets/_columns_tab_drag.py`, replace the body: set `self._current_source = source_column` then delegate `self._slot.set_assignment(source_column)`. Remove the `self._assignment.setText(...)` call.

- [x] [P2-T5] In `ColumnDropRow.assignment_text` in `src/gui/widgets/_columns_tab_drag.py`, replace the body with `return self._slot.assignment_text()`. Remove the reference to `self._assignment`.

- [x] [P2-T6] Remove `ColumnDropRow.dragEnterEvent`, `ColumnDropRow.dropEvent`, and `ColumnDropRow.mouseMoveEvent` from `src/gui/widgets/_columns_tab_drag.py` (all three methods move to `ColumnAssignmentSlot`). Confirm no remaining reference to these method bodies in the file.

- [x] [P2-T7] In `ColumnDropRow` class docstring in `src/gui/widgets/_columns_tab_drag.py`, update the Responsibilities and Attributes sections to reflect that drag/drop event handling now lives in `ColumnAssignmentSlot` and `_assignment` label is replaced by `_slot`.

- [x] [P2-T8] In `SourceColumnToken.__init__` in `src/gui/widgets/_columns_tab_drag.py`, add after `super().__init__(column_name, parent)`: `self.setStyleSheet("background: #5c88d4; color: white; border-radius: 3px; padding: 4px 8px; font-weight: bold;")`. This fixes AC-1 (invisible token text).

- [x] [P2-T9] In `ColumnsTabWidget.__init__` in `src/gui/widgets/_columns_tab_drag.py`, after `self._pool_box = QVBoxLayout()` add `self._pool_box.setSpacing(4)`. After `self._rows_box = QVBoxLayout()` add `self._rows_box.setSpacing(2)` and `self._rows_box.setContentsMargins(0, 0, 0, 0)`. These changes implement AC-4 (compact row spacing).

- [x] [P2-T10] Count the line count of `src/gui/widgets/_columns_tab_drag.py` after all Phase 2 changes. Confirm it is at most 499 lines. If it exceeds 499 lines, identify additional lines to remove (e.g., further docstring trimming) before proceeding.

---

### Phase 3 — Update Tests

- [x] [P3-T1] In `tests/gui/test_columns_tab_widgets.py`, update `test_drop_gesture_invokes_assign_column_once`: the `dropEvent` now lives on `ColumnAssignmentSlot`, not `ColumnDropRow`. Replace `row.dropEvent(_Event())` with access to `row._slot.dropEvent(_Event())`. Import `ColumnAssignmentSlot` is not needed; access via `row._slot`. Update the docstring to note the slot delegation.

- [x] [P3-T2] In `tests/gui/test_columns_tab_widgets.py`, update `test_drop_row_drag_enter_accepts_text_payload`: the `dragEnterEvent` now lives on `ColumnAssignmentSlot`. Replace `row.dragEnterEvent(_Event())` with `row._slot.dragEnterEvent(_Event())`. Update the docstring accordingly.

- [x] [P3-T3] In `tests/gui/test_columns_tab_widgets.py`, update `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`: the `mouseMoveEvent` now lives on `ColumnAssignmentSlot`. Update the patch target from `mod` (`_columns_tab_drag`) to also patch `_column_assignment_slot` module's `QDrag`, since `ColumnAssignmentSlot.mouseMoveEvent` references `QDrag` from its own module. Import `from src.gui.widgets import _column_assignment_slot as slot_mod`, patch `slot_mod.QDrag`, and call `row._slot.mouseMoveEvent(event)`. Verify the `CANONICAL_ORIGIN_MIME` import still resolves from `_columns_tab_drag` (re-exported via import).

- [x] [P3-T4] In `tests/gui/test_columns_tab_widgets.py`, update `test_unassigned_row_mousemove_does_not_start_drag`: same QDrag patch target change as P3-T3. Call `row._slot.mouseMoveEvent(event)` instead of `row.mouseMoveEvent(event)`.

- [x] [P3-T5] In `tests/gui/test_columns_tab_widgets.py`, add test `test_assignment_slot_unassigned_style_has_dashed_border`. Arrange: create `ColumnAssignmentSlot("Customer", lambda _s, _c: None)` (import from `src.gui.widgets._column_assignment_slot`). Act: read `slot.styleSheet()` before calling `set_assignment`. Assert: `"dashed"` is in the stylesheet string. Add a docstring covering AC-3 (unassigned visual affordance).

- [x] [P3-T6] In `tests/gui/test_columns_tab_widgets.py`, add test `test_assignment_slot_assigned_shows_source_button`. Arrange: create `ColumnAssignmentSlot("Customer", lambda _s, _c: None)`. Act: call `slot.set_assignment("col_a")`. Assert: `slot.assignment_text() == "col_a"`. Add a docstring covering AC-3 (assigned slot exposes source name).

- [x] [P3-T7] In `tests/gui/test_columns_tab_widgets.py`, add test `test_source_token_has_visible_styling`. Arrange: create `SourceColumnToken("col_x")` (import from `src.gui.widgets._columns_tab_drag`). Assert: `token.styleSheet()` is a non-empty string. Add a docstring covering AC-1 (token text visibility).

- [x] [P3-T8] Verify `tests/gui/test_columns_tab_widgets.py` is at most 500 lines after all additions. Count the line count explicitly.

---

### Phase 4 — Full QA Loop

Run the toolchain in order and restart from step 1 if any step fails or auto-modifies files. All steps must complete in a single clean pass.

- [x] [P4-T1] Run Black formatter and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/black-qa.md`. Command: `poetry run black .`. If Black modifies any file, restart the QA loop from P4-T1. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P4-T2] Run Ruff linter and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ruff-qa.md`. Command: `poetry run ruff check .`. If Ruff reports errors, fix them and restart from P4-T1. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P4-T3] Run Pyright type checker and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/pyright-qa.md`. Command: `poetry run pyright`. If Pyright reports errors, fix them and restart from P4-T1. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.

- [x] [P4-T4] Run Pytest with coverage and record result in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/pytest-qa.md`. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. If any test fails or coverage drops below line >= 85% / branch >= 75%, fix and restart from P4-T1. Artifact must include `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` with numeric post-change line-coverage % and branch-coverage % values for the overall suite and for the in-scope files.

---

### Phase 5 — Coverage Delta Verification

- [x] [P5-T1] Compare baseline coverage (from P0-T5 artifact) against post-change coverage (from P4-T4 artifact) and record in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/coverage-delta.md`. Artifact must include: baseline line coverage %, baseline branch coverage %, post-change line coverage %, post-change branch coverage %, and a PASS/FAIL verdict confirming no regression below the 85% line / 75% branch thresholds. If coverage regressed, the verdict is FAIL and implementation must be corrected before proceeding.

---

### Phase 6 — Acceptance Criteria Verification

- [x] [P6-T1] Verify AC-1 (source column tokens render with visible text): confirm `SourceColumnToken.styleSheet()` is non-empty and contains a foreground `color` property. Evidence: P4-T4 pytest result must include `test_source_token_has_visible_styling` as PASSED. Record outcome in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ac-verification.md`.

- [x] [P6-T2] Verify AC-2 (each canonical row is horizontal): confirm `ColumnDropRow.__init__` uses `QHBoxLayout`. Evidence: grep `src/gui/widgets/_columns_tab_drag.py` for `QHBoxLayout` within `ColumnDropRow.__init__`. Record grep output in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ac-verification.md`.

- [x] [P6-T3] Verify AC-3 (assignment slot shows dashed "(drop here)" unassigned and solid-border assigned button): confirm `test_assignment_slot_unassigned_style_has_dashed_border` and `test_assignment_slot_assigned_shows_source_button` both PASSED in P4-T4 pytest output. Record outcome in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ac-verification.md`.

- [x] [P6-T4] Verify AC-4 (compact row spacing): confirm `_rows_box.setSpacing(2)` and `_pool_box.setSpacing(4)` are present in `src/gui/widgets/_columns_tab_drag.py` via grep. Record grep output in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ac-verification.md`.

- [x] [P6-T5] Verify AC-5 (bidirectional drag behaviors from #64 continue to function): confirm all four updated drag/drop tests (`test_drop_gesture_invokes_assign_column_once`, `test_drop_row_drag_enter_accepts_text_payload`, `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`, `test_unassigned_row_mousemove_does_not_start_drag`) plus the pool unassign tests (`test_pool_dropEvent_with_canonical_origin_calls_clear_row`, `test_pool_dragEnterEvent_rejects_missing_canonical_origin`) are PASSED in P4-T4 pytest output. Record outcome in `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ac-verification.md`.
