"""Qt offscreen tests for the Key-tab drag widgets (Decision 2).

These tests run headless under ``QT_QPA_PLATFORM=offscreen``. They verify that a
column drop and a Generic-Text drop each invoke the ``add_key_part`` seam with the
correct part kind and value, and that the drop area renders the ordered parts the
presenter pushes. All fixture values are synthetic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData

from src.gui.widgets._key_tab_drag import KeyDropArea, KeyTabWidget

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def _drop(area: KeyDropArea, payload: str) -> None:
    """Invoke the drop area's dropEvent with a MIME-text payload.

    Args:
        area: The drop area under test.
        payload: The MIME text the drop carries.

    Returns:
        ``None``.
    """
    mime = QMimeData()
    mime.setText(payload)

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            pass

    area.dropEvent(_Event())  # type: ignore[arg-type]


def test_column_drop_invokes_add_key_part_as_column_ref(qtbot: QtBot) -> None:
    """A column drop invokes add_key_part with a column-ref part."""
    # Arrange
    calls: list[tuple[str, str]] = []
    area = KeyDropArea(on_add=lambda kind, value: calls.append((kind, value)))
    qtbot.addWidget(area)

    # Act: a column-prefixed drop.
    _drop(area, "column:Customer")

    # Assert
    assert calls == [("column-ref", "Customer")]


def test_generic_text_drop_invokes_add_key_part_as_literal(qtbot: QtBot) -> None:
    """A Generic-Text drop invokes add_key_part with a literal-text part."""
    # Arrange
    calls: list[tuple[str, str]] = []
    area = KeyDropArea(on_add=lambda kind, value: calls.append((kind, value)))
    qtbot.addWidget(area)

    # Act: a generic-prefixed drop carrying a literal value.
    _drop(area, "generic:-")

    # Assert
    assert calls == [("literal-text", "-")]


def test_widget_renders_ordered_parts(qtbot: QtBot) -> None:
    """set_parts renders the ordered key parts in the drop area."""
    # Arrange
    widget = KeyTabWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_parts(
        [("column-ref", "Customer"), ("literal-text", "-"), ("column-ref", "SKU #")]
    )

    # Assert: the rendered text reflects the ordered composition.
    text = widget.parts_text()
    assert "Customer" in text
    assert "SKU #" in text
    assert text.index("Customer") < text.index("SKU #")


def test_column_tokens_rebuilt_from_columns(qtbot: QtBot) -> None:
    """set_column_tokens rebuilds the draggable column-token pool."""
    # Arrange
    widget = KeyTabWidget()
    qtbot.addWidget(widget)

    # Act
    widget.set_column_tokens(["Customer", "SKU #"])

    # Assert
    assert widget.column_token_names() == ["Customer", "SKU #"]


def test_key_column_token_starts_drag(qtbot: QtBot) -> None:
    """Moving a key column token with the left button starts a column drag."""
    # Arrange
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    from src.gui.widgets import _key_tab_drag as mod
    from src.gui.widgets._key_tab_drag import KeyColumnToken

    token = KeyColumnToken("Customer")
    qtbot.addWidget(token)
    payloads: list[str] = []

    class _StubMime:
        def setText(self, text: str) -> None:
            payloads.append(text)

    class _StubDrag:
        def __init__(self, _parent: object) -> None:
            pass

        def setMimeData(self, _mime: object) -> None:
            pass

        def exec(self, _action: object) -> None:
            pass

    original_drag = mod.QDrag
    original_mime = mod.QMimeData
    mod.QDrag = _StubDrag  # type: ignore[misc, assignment]
    mod.QMimeData = _StubMime  # type: ignore[misc, assignment]
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
        mod.QDrag = original_drag  # type: ignore[misc]
        mod.QMimeData = original_mime  # type: ignore[misc]

    # Assert: the drag payload carries the column prefix and the column name.
    assert payloads == ["column:Customer"]


def test_key_drop_area_drag_enter_accepts_text(qtbot: QtBot) -> None:
    """A drag-enter carrying text is accepted by the key drop area."""
    # Arrange
    area = KeyDropArea(on_add=lambda _k, _v: None)
    qtbot.addWidget(area)
    accepted: list[bool] = []
    mime = QMimeData()
    mime.setText("column:Customer")

    class _Event:
        def mimeData(self) -> QMimeData:
            return mime

        def acceptProposedAction(self) -> None:
            accepted.append(True)

    # Act
    area.dragEnterEvent(_Event())  # type: ignore[arg-type]

    # Assert
    assert accepted == [True]


def test_key_drop_area_empty_renders_placeholder(qtbot: QtBot) -> None:
    """Rendering an empty part list shows the no-parts placeholder."""
    # Arrange
    area = KeyDropArea(on_add=lambda _k, _v: None)
    qtbot.addWidget(area)

    # Act
    area.render_parts([])

    # Assert
    assert "no key parts" in area.parts_text()
