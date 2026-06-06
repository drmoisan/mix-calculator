"""Qt drag-and-drop widgets for the Key tab (Decision 2, research G).

This module holds the passive Qt widgets for the Key tab: draggable column-name
tokens, a repeatable "Generic Text" token with a per-literal value input, and an
ordered drop area for the composed key parts. The widgets are thin: a column drop
or a Generic-Text drop translates into a single ``add_key_part(kind, value)`` call
on an injected callback, so the
:class:`~src.gui.presenters._key_tab_presenter.KeyTabPresenter` and its tests never
simulate Qt drag events.

Responsibilities:
    - ``KeyColumnToken``: a draggable column-name token (single-use semantics).
    - ``GenericTextToken``: the repeatable literal-text token carrying its input.
    - ``KeyDropArea``: accepts drops and reports each as one ``add_key_part`` call.
    - ``KeyTabWidget``: composes the tokens and the drop area and renders the parts.

Scope boundaries:
    - View only: no key assembly or validation. The presenter owns all decisions;
      the widget reports the drop gesture and renders pushed parts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtGui import QDropEvent, QMouseEvent

__all__ = [
    "GenericTextToken",
    "KeyColumnToken",
    "KeyDropArea",
    "KeyTabWidget",
]

# MIME prefixes distinguishing a column-ref drop from a Generic-Text drop. The
# drop area parses the prefix to decide the part kind.
_COLUMN_PREFIX = "column:"
_GENERIC_PREFIX = "generic:"


class KeyColumnToken(QPushButton):
    """A draggable column-name token for the Key tab.

    Purpose:
        Render one canonical column as a draggable token; a drag carries the
        column name with the column prefix so the drop area builds a column-ref
        part.

    Attributes:
        column_name: The canonical column name this token represents.
    """

    def __init__(self, column_name: str, parent: QWidget | None = None) -> None:
        """Build a token labeled with and carrying ``column_name``.

        Args:
            column_name: The canonical column name to display and drag.
            parent: Optional Qt parent widget.
        """
        super().__init__(column_name, parent)
        self.column_name = column_name

    def mouseMoveEvent(self, e: QMouseEvent) -> None:  # noqa: N802 - Qt override
        """Start a drag carrying the column name with the column prefix.

        Args:
            e: The Qt mouse-move event.

        Returns:
            ``None``.

        Side effects:
            Executes a :class:`QDrag` whose MIME text is ``column:<name>``.
        """
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"{_COLUMN_PREFIX}{self.column_name}")
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)


class GenericTextToken(QWidget):
    """The repeatable Generic-Text token with a per-literal value input.

    Purpose:
        Provide the only token placeable multiple times (Decision 2): a literal
        value input plus a draggable handle that carries the current literal value
        with the generic prefix so each drop adds a distinct literal-text part.

    Attributes:
        _input: The per-literal value input read at drag time.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the value input and the draggable handle.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Generic text value")
        self._handle = _GenericDragHandle("Generic Text", self._current_value)
        layout = QVBoxLayout(self)
        layout.addWidget(self._input)
        layout.addWidget(self._handle)

    def set_value(self, value: str) -> None:
        """Set the literal value (test/programmatic seam).

        Args:
            value: The literal value to carry on the next drag.

        Returns:
            ``None``.

        Side effects:
            Updates the value input.
        """
        self._input.setText(value)

    def _current_value(self) -> str:
        """Return the current literal value to carry on a drag.

        Returns:
            The value-input text.
        """
        return self._input.text()


class _GenericDragHandle(QPushButton):
    """Draggable handle that carries the Generic-Text token's current value.

    Attributes:
        _value_provider: Callable returning the current literal value at drag time.
    """

    def __init__(
        self,
        label: str,
        value_provider: Callable[[], str],
        parent: QWidget | None = None,
    ) -> None:
        """Build the handle bound to a value provider.

        Args:
            label: The handle's button label.
            value_provider: Callable returning the literal value to carry.
            parent: Optional Qt parent widget.
        """
        super().__init__(label, parent)
        self._value_provider = value_provider

    def mouseMoveEvent(self, e: QMouseEvent) -> None:  # noqa: N802 - Qt override
        """Start a drag carrying the current literal value with the generic prefix.

        Args:
            e: The Qt mouse-move event.

        Returns:
            ``None``.

        Side effects:
            Executes a :class:`QDrag` whose MIME text is ``generic:<value>``.
        """
        if not (e.buttons() & Qt.MouseButton.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"{_GENERIC_PREFIX}{self._value_provider()}")
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)


class KeyDropArea(QWidget):
    """The ordered drop area that accepts column and Generic-Text drops.

    Purpose:
        Accept dropped tokens and report each as a single ``add_key_part`` call,
        and render the ordered key parts the presenter pushes.

    Responsibilities:
        Parse the dropped MIME prefix into a part kind and value, call the injected
        ``on_add`` once per drop, and render the ordered parts. It performs no
        assembly or validation.

    Attributes:
        _on_add: The seam callback invoked with ``(kind, value)`` on a drop.
    """

    def __init__(
        self, on_add: Callable[[str, str], None], parent: QWidget | None = None
    ) -> None:
        """Build the drop area bound to the add seam.

        Args:
            on_add: Callback invoked with ``(kind, value)`` on each drop.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._on_add = on_add
        self.setAcceptDrops(True)
        self._parts_label = QLabel("(no key parts)")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Key parts (in order):"))
        layout.addWidget(self._parts_label)

    def render_parts(self, parts: list[tuple[str, str]]) -> None:
        """Render the ordered key parts as text.

        Args:
            parts: One ``(kind, value)`` tuple per part, in order.

        Returns:
            ``None``.

        Side effects:
            Updates the parts label.
        """
        if not parts:
            self._parts_label.setText("(no key parts)")
            return
        # Render each part compactly so the ordered composition is visible; the
        # kind disambiguates a column reference from a literal segment.
        self._parts_label.setText(
            " + ".join(f"[{kind}:{value}]" for kind, value in parts)
        )

    def parts_text(self) -> str:
        """Return the rendered parts text (test seam).

        Returns:
            The parts label text.
        """
        return self._parts_label.text()

    def dragEnterEvent(self, e: QDropEvent) -> None:  # noqa: N802 - Qt override
        """Accept a drag carrying prefixed text so a drop can land.

        Args:
            e: The Qt drag-enter event.

        Returns:
            ``None``.

        Side effects:
            Accepts the proposed action when the payload carries text.
        """
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:  # noqa: N802 - Qt override
        """Report the dropped token to the add seam with the parsed kind.

        Routing table by MIME prefix:
            - ``column:<name>`` → a ``column-ref`` part for ``name``.
            - ``generic:<value>`` → a ``literal-text`` part for ``value``.

        Args:
            e: The Qt drop event whose MIME text carries the prefixed payload.

        Returns:
            ``None``.

        Side effects:
            Calls ``on_add(kind, value)`` exactly once and accepts the action.
        """
        text = e.mimeData().text()
        # Parse the prefix to decide the part kind; an unrecognized payload is
        # ignored so a stray drop cannot add a malformed part.
        if text.startswith(_COLUMN_PREFIX):
            self._on_add("column-ref", text[len(_COLUMN_PREFIX) :])
        elif text.startswith(_GENERIC_PREFIX):
            self._on_add("literal-text", text[len(_GENERIC_PREFIX) :])
        e.acceptProposedAction()


class KeyTabWidget(QWidget):
    """Composes the column tokens, the Generic-Text token, and the drop area.

    Purpose:
        Provide the Key-tab view: a pool of draggable column tokens and one
        repeatable Generic-Text token above an ordered drop area, implementing the
        :class:`~src.gui._key_tab_protocol.KeyTabViewProtocol` and routing each drop
        to the injected add seam.

    Responsibilities:
        Build the column tokens and Generic-Text token; forward each drop to
        ``add_key_part``; render the ordered parts. It holds no assembly logic.
    """

    def __init__(
        self,
        on_add: Callable[[str, str], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Build the token pool, the Generic-Text token, and the drop area.

        Args:
            on_add: Optional add seam callback invoked with ``(kind, value)`` on a
                drop; defaults to a no-op until the composition root wires the
                presenter.
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self._on_add: Callable[[str, str], None] = on_add or (lambda _k, _v: None)
        self._tokens_box = QVBoxLayout()
        self._tokens: list[KeyColumnToken] = []
        self._generic = GenericTextToken()
        self._drop = KeyDropArea(self.add_key_part)
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("Columns"))
        outer.addLayout(self._tokens_box)
        outer.addWidget(QLabel("Generic Text (repeatable)"))
        outer.addWidget(self._generic)
        outer.addWidget(self._drop)

    def add_key_part(self, kind: str, value: str) -> None:
        """Route a dropped key part to the add seam.

        Args:
            kind: The part kind: ``"column-ref"`` or ``"literal-text"``.
            value: The referenced column or the literal value.

        Returns:
            ``None``.

        Side effects:
            Invokes the injected add callback.
        """
        self._on_add(kind, value)

    def set_parts(self, parts: list[tuple[str, str]]) -> None:
        """Render the ordered key parts.

        Args:
            parts: One ``(kind, value)`` tuple per part, in order.

        Returns:
            ``None``.

        Side effects:
            Updates the drop area's rendered parts.
        """
        self._drop.render_parts(parts)

    def reorder_parts(self, order: list[int]) -> None:
        """No-op reorder hook (drag reordering is presenter-driven in tests).

        Args:
            order: The requested ordering (unused by this passive widget).

        Returns:
            ``None``.
        """
        del order

    def parts_text(self) -> str:
        """Return the rendered key-parts text (public test seam).

        Returns:
            The drop area's rendered parts text.
        """
        return self._drop.parts_text()

    def column_token_names(self) -> list[str]:
        """Return the current column-token names (public test seam).

        Returns:
            The canonical names of the draggable column tokens, in order.
        """
        return [token.column_name for token in self._tokens]

    def set_column_tokens(self, columns: list[str]) -> None:
        """Rebuild the draggable column-token pool.

        Args:
            columns: The canonical column names to offer as tokens, in order.

        Returns:
            ``None``.

        Side effects:
            Clears and recreates the column tokens.
        """
        # Clear existing tokens before rebuilding so the pool reflects the current
        # column set exactly.
        for token in self._tokens:
            token.setParent(None)
        self._tokens = []
        for name in columns:
            token = KeyColumnToken(name)
            self._tokens.append(token)
            self._tokens_box.addWidget(token)
