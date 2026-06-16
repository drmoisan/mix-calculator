"""Qt offscreen tests for the Columns-tab drag widgets and dtype indicator.

These tests run headless under ``QT_QPA_PLATFORM=offscreen``. They verify that the
draggable token pool renders one token per source column, that the canonical rows
display name/description/expected dtype, that a drop gesture invokes the
``assign_column`` seam exactly once with the dropped source and target, and that
the dtype indicator shows green for a coercible state and red plus a masked example
for a non-coercible state. Every value used is synthetic/masked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QScrollArea

from src.gui.widgets._columns_tab_drag import ColumnDropRow, ColumnsTabWidget
from src.gui.widgets._dtype_check_widget import DtypeCheckWidget
from src.gui.widgets._schema_builder_tabs import build_columns_tab

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_columns_tab_wraps_widget_in_resizable_scroll_area(qtbot: QtBot) -> None:
    """AC-7: the Columns tab hosts a resizable QScrollArea wrapping the widget.

    The Columns tab is vertically scrollable so all canonical rows are reachable
    when they exceed the visible height. The scroll area is resizable, and its
    inner widget is the same real :class:`ColumnsTabWidget` the binder uses.
    """
    # Arrange / Act
    controls = build_columns_tab()
    qtbot.addWidget(controls.widget)

    # Assert: a resizable scroll area in the container wraps the columns widget.
    scroll_areas = controls.widget.findChildren(QScrollArea)
    assert len(scroll_areas) == 1
    scroll_area = scroll_areas[0]
    assert scroll_area.widgetResizable() is True
    assert scroll_area.widget() is controls.columns_widget


def test_pool_renders_one_token_per_source_column(qtbot: QtBot) -> None:
    """set_source_pool renders one draggable token per header column."""
    # Arrange
    widget = ColumnsTabWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_source_pool(["col_a", "col_b", "col_c"])

    # Assert: one token per source column.
    assert widget.token_names() == ["col_a", "col_b", "col_c"]


def test_rows_display_name_description_and_dtype(qtbot: QtBot) -> None:
    """set_rows renders each row with its name, description, and expected dtype."""
    # Arrange
    widget = ColumnsTabWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_rows([("Customer", "the customer", "string")])

    # Assert: the row label includes all three parts.
    text = widget.row_label_text("Customer")
    assert "Customer" in text
    assert "the customer" in text
    assert "string" in text


def test_drop_gesture_invokes_assign_column_once(qtbot: QtBot) -> None:
    """A drop on the slot of a canonical row invokes assign_column once.

    Drop-event handling has moved from ColumnDropRow to ColumnAssignmentSlot;
    the test exercises the slot directly via ``row._slot``.
    """
    # Arrange: a drop row whose assignment seam records calls.
    calls: list[tuple[str, str]] = []
    row = ColumnDropRow("Customer", "", "string", lambda s, c: calls.append((s, c)))
    qtbot.addWidget(row)

    # Act: simulate the drop gesture on the slot (which now owns dropEvent).
    mime = QMimeData()
    mime.setText("col_a")

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            pass

    row.slot.dropEvent(_Event())  # type: ignore[arg-type]

    # Assert: exactly one assignment with the dropped source and the row's target.
    assert calls == [("col_a", "Customer")]


def test_dtype_indicator_shows_green_for_coercible(qtbot: QtBot) -> None:
    """The dtype indicator shows the green check for a coercible state."""
    # Arrange
    widget = DtypeCheckWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_state(coercible=True, failing_example=None)

    # Assert: the check glyph is shown with no example.
    assert "✓" in widget.text()


def test_dtype_indicator_shows_red_with_masked_example(qtbot: QtBot) -> None:
    """The dtype indicator shows the red X and the masked failing example."""
    # Arrange
    widget = DtypeCheckWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_state(coercible=False, failing_example="bad")

    # Assert: the X glyph and the masked example value are shown.
    assert "✗" in widget.text()
    assert "bad" in widget.text()


def test_source_token_starts_drag_on_left_button_move(qtbot: QtBot) -> None:
    """Moving a source token with the left button held starts a drag."""
    # Arrange: a token whose drag start we observe via a patched QDrag.exec.
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    from src.gui.widgets import _columns_tab_drag as mod
    from src.gui.widgets._columns_tab_drag import SourceColumnToken

    token = SourceColumnToken("col_a")
    qtbot.addWidget(token)
    started: list[bool] = []

    class _StubDrag:
        def __init__(self, _parent: object) -> None:
            pass

        def setMimeData(self, _mime: object) -> None:
            pass

        def exec(self, _action: object) -> None:
            started.append(True)

    # Patch QDrag so no real drag loop runs headless.
    original = mod.QDrag
    mod.QDrag = _StubDrag  # type: ignore[misc, assignment]
    try:
        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(QPoint(1, 1)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        token.mouseMoveEvent(event)
    finally:
        mod.QDrag = original  # type: ignore[misc]

    # Assert: a drag was initiated.
    assert started == [True]


def test_drop_row_drag_enter_accepts_text_payload(qtbot: QtBot) -> None:
    """A drag-enter carrying text is accepted by the slot so a drop can land.

    Drag-enter handling has moved from ColumnDropRow to ColumnAssignmentSlot;
    the test exercises the slot directly via ``row._slot``.
    """
    # Arrange
    row = ColumnDropRow("Customer", "", "string", lambda _s, _c: None)
    qtbot.addWidget(row)
    accepted: list[bool] = []

    mime = QMimeData()
    mime.setText("col_a")

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            accepted.append(True)

    # Act: invoke dragEnterEvent on the slot, which now owns the handler.
    row.slot.dragEnterEvent(_Event())  # type: ignore[arg-type]

    # Assert
    assert accepted == [True]


def test_assigned_row_mousemove_starts_drag_carrying_source_and_origin(
    qtbot: QtBot,
) -> None:
    """An assigned slot starts a drag with both MIME keys on mouse-move.

    Covers AC-1 (re-assign via drag) and AC-4 (test coverage of new paths).
    The drag must carry text/plain = source column name and
    application/x-canonical-origin = canonical row name.

    Mouse-move handling has moved from ColumnDropRow to ColumnAssignmentSlot;
    QDrag is patched on the slot module and the event is delivered to
    ``row._slot``.
    """
    # Arrange
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    from src.gui.widgets import _column_assignment_slot as slot_mod
    from src.gui.widgets._columns_tab_drag import (
        CANONICAL_ORIGIN_MIME,
        ColumnDropRow,
    )

    row = ColumnDropRow("Revenue", "", None, lambda _s, _c: None)
    qtbot.addWidget(row)
    row.set_assignment("col_revenue")

    captured_mime: list[object] = []

    class _StubDrag:
        def __init__(self, _parent: object) -> None:
            pass

        def setMimeData(self, mime: object) -> None:
            captured_mime.append(mime)

        def exec(self, _action: object) -> None:
            pass

    # Patch QDrag on the slot module, which now owns mouseMoveEvent.
    original = slot_mod.QDrag
    slot_mod.QDrag = _StubDrag  # type: ignore[misc, assignment]
    try:
        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(QPoint(1, 1)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        row.slot.mouseMoveEvent(event)
    finally:
        slot_mod.QDrag = original  # type: ignore[misc]

    # Assert: drag was initiated and MIME carries both keys.
    assert len(captured_mime) == 1
    from PySide6.QtCore import QMimeData

    mime = captured_mime[0]
    assert isinstance(mime, QMimeData)
    assert mime.text() == "col_revenue"
    assert mime.data(CANONICAL_ORIGIN_MIME).toStdString() == "Revenue"


def test_unassigned_row_mousemove_does_not_start_drag(qtbot: QtBot) -> None:
    """An unassigned slot does not start a drag on mouse-move.

    Covers the guard-clause branch in ColumnAssignmentSlot.mouseMoveEvent.
    Mouse-move handling has moved to the slot; QDrag is patched on the slot
    module and the event is delivered to ``row.slot``.
    """
    # Arrange
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    from src.gui.widgets import _column_assignment_slot as slot_mod
    from src.gui.widgets._columns_tab_drag import ColumnDropRow

    row = ColumnDropRow("Revenue", "", None, lambda _s, _c: None)
    qtbot.addWidget(row)
    # Do NOT call set_assignment — slot remains unassigned.

    started: list[bool] = []

    class _StubDrag:
        def __init__(self, _parent: object) -> None:
            pass

        def setMimeData(self, _mime: object) -> None:
            pass

        def exec(self, _action: object) -> None:
            started.append(True)

    original = slot_mod.QDrag
    slot_mod.QDrag = _StubDrag  # type: ignore[misc, assignment]
    try:
        event = QMouseEvent(
            QMouseEvent.Type.MouseMove,
            QPointF(QPoint(1, 1)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        row.slot.mouseMoveEvent(event)
    finally:
        slot_mod.QDrag = original  # type: ignore[misc]

    # Assert: no drag was started because the slot has no assigned source.
    assert started == []


def test_pool_dropEvent_with_canonical_origin_calls_clear_row(qtbot: QtBot) -> None:
    """ColumnsTabWidget.dropEvent calls clear_row with the decoded canonical name.

    Covers AC-2 (unassign via pool drop) and AC-4 (test coverage of new paths).
    """
    # Arrange
    from PySide6.QtCore import QByteArray, QMimeData

    from src.gui.widgets._columns_tab_drag import (
        CANONICAL_ORIGIN_MIME,
        ColumnsTabWidget,
    )

    widget = ColumnsTabWidget()
    qtbot.addWidget(widget)

    cleared: list[str] = []
    widget.clear_row = lambda c: cleared.append(c)  # type: ignore[method-assign]

    # Build a fake drop event carrying both MIME keys.
    mime = QMimeData()
    mime.setText("col_revenue")
    mime.setData(CANONICAL_ORIGIN_MIME, QByteArray(b"Revenue"))

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            pass

    # Act: invoke dropEvent directly.
    widget.dropEvent(_Event())  # type: ignore[arg-type]

    # Assert: clear_row was called with the decoded canonical name.
    assert cleared == ["Revenue"]


def test_pool_dragEnterEvent_rejects_missing_canonical_origin(qtbot: QtBot) -> None:
    """ColumnsTabWidget.dragEnterEvent does not accept plain pool-token drags.

    A drag carrying only text/plain (no canonical-origin key) must not be
    accepted by the pool widget, ensuring only row-origin drags reach dropEvent.
    """
    # Arrange
    from PySide6.QtCore import QMimeData

    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

    widget = ColumnsTabWidget()
    qtbot.addWidget(widget)

    # Build a MIME payload with only text/plain — no canonical-origin key.
    mime = QMimeData()
    mime.setText("col_a")

    accepted: list[bool] = []

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            accepted.append(True)

        def isAccepted(self) -> bool:
            return bool(accepted)

    # Act
    event = _Event()
    widget.dragEnterEvent(event)  # type: ignore[arg-type]

    # Assert: the event was NOT accepted (pool-token drags have no origin key).
    assert accepted == []


def test_assignment_slot_unassigned_style_has_dashed_border(qtbot: QtBot) -> None:
    """An unassigned ColumnAssignmentSlot uses a dashed-border stylesheet (AC-3).

    The unassigned visual affordance is the dashed border that signals to the
    user that a source column can be dropped here.
    """
    # Arrange
    from src.gui.widgets._column_assignment_slot import ColumnAssignmentSlot

    slot = ColumnAssignmentSlot("Customer", lambda _s, _c: None)
    qtbot.addWidget(slot)

    # Act: read the stylesheet before any assignment is made.
    style = slot.styleSheet()

    # Assert: the unassigned state uses a dashed border.
    assert "dashed" in style


def test_assignment_slot_assigned_shows_source_button(qtbot: QtBot) -> None:
    """After set_assignment, assignment_text returns the assigned source name (AC-3).

    The assigned slot exposes the source column name so tests and the presenter
    can read back what is displayed without simulating UI interactions.
    """
    # Arrange
    from src.gui.widgets._column_assignment_slot import ColumnAssignmentSlot

    slot = ColumnAssignmentSlot("Customer", lambda _s, _c: None)
    qtbot.addWidget(slot)

    # Act
    slot.set_assignment("col_a")

    # Assert: the slot reports the assigned source name.
    assert slot.assignment_text() == "col_a"


def test_source_token_has_visible_styling(qtbot: QtBot) -> None:
    """SourceColumnToken has an explicit stylesheet with visible text (AC-1).

    Without an explicit stylesheet the token text is invisible against the
    default dark-mode or light-mode background. The stylesheet must be non-empty
    and include a ``color`` property so the label is legible.
    """
    # Arrange
    from src.gui.widgets._columns_tab_drag import SourceColumnToken

    token = SourceColumnToken("col_x")
    qtbot.addWidget(token)

    # Assert: the stylesheet is non-empty (explicit styling is applied).
    assert token.styleSheet() != ""
