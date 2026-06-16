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
    """A drop on a canonical row invokes assign_column once with source+target."""
    # Arrange: a drop row whose assignment seam records calls.
    calls: list[tuple[str, str]] = []
    row = ColumnDropRow("Customer", "", "string", lambda s, c: calls.append((s, c)))
    qtbot.addWidget(row)

    # Act: simulate the drop gesture by invoking dropEvent with a MIME-text
    # payload, which is exactly what the Qt drop gesture produces.
    mime = QMimeData()
    mime.setText("col_a")

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            pass

    row.dropEvent(_Event())  # type: ignore[arg-type]

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
    """A drag-enter carrying text is accepted so a drop can land."""
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

    # Act
    row.dragEnterEvent(_Event())  # type: ignore[arg-type]

    # Assert
    assert accepted == [True]
