"""Layout helpers for ColumnsTabWidget's responsive splitter (Decision 4, issue #68).

This module provides panel-construction and orientation-switch functions used by
:class:`~src.gui.widgets._columns_tab_drag.ColumnsTabWidget` to keep
``_columns_tab_drag.py`` under the 500-line file-size limit while preserving the
full layout logic in a testable, documented location.

Responsibilities:
    - ``build_columns_panels``: construct the pool panel and the scroll-wrapped rows
      panel from their respective layout containers.
    - ``apply_splitter_orientation``: reorder the two panels inside a ``QSplitter``
      when the layout mode changes between wide and narrow.

Scope boundaries:
    - Pure Qt widget manipulation; no domain logic, no I/O.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QSplitter, QVBoxLayout, QWidget

__all__ = ["apply_splitter_orientation", "build_columns_panels"]


def build_columns_panels(
    pool_box: QVBoxLayout,
    rows_box: QVBoxLayout,
) -> tuple[QWidget, QScrollArea]:
    """Construct the pool panel and the scroll-wrapped rows panel.

    Creates two panels from the provided layout containers:

    1. ``pool_panel`` — a ``QWidget`` titled "Source columns" whose body is
       ``pool_box`` followed by a stretch to push tokens to the top.
    2. ``rows_scroll`` — a resizable ``QScrollArea`` wrapping a ``QWidget``
       titled "Canonical columns" whose body is ``rows_box`` followed by a
       stretch. The scroll area allows rows beyond the visible height to be
       reached by scrolling (AC-1, AC-2).

    Args:
        pool_box: The ``QVBoxLayout`` that will hold draggable source tokens.
        rows_box: The ``QVBoxLayout`` that will hold canonical drop rows.

    Returns:
        A ``(pool_panel, rows_scroll)`` tuple ready to be added to a splitter.

    Side effects:
        Adds child widgets/layouts to ``pool_box`` and ``rows_box`` parent chains.
    """
    # Pool panel: titled wrapper for the draggable source-token layout.
    pool_panel = QWidget()
    pool_layout = QVBoxLayout(pool_panel)
    pool_layout.setContentsMargins(0, 0, 0, 0)
    pool_layout.addWidget(QLabel("Source columns"))
    pool_layout.addLayout(pool_box)
    pool_layout.addStretch()

    # Rows inner widget: titled wrapper for the canonical drop-row layout.
    rows_inner = QWidget()
    rows_inner_layout = QVBoxLayout(rows_inner)
    rows_inner_layout.setContentsMargins(0, 0, 0, 0)
    rows_inner_layout.addWidget(QLabel("Canonical columns"))
    rows_inner_layout.addLayout(rows_box)
    rows_inner_layout.addStretch()

    # Wrap the rows inner widget in a scroll area so all rows remain reachable.
    rows_scroll = QScrollArea()
    rows_scroll.setWidget(rows_inner)
    rows_scroll.setWidgetResizable(True)

    return pool_panel, rows_scroll


def apply_splitter_orientation(
    splitter: QSplitter,
    pool_panel: QWidget,
    rows_scroll: QScrollArea,
    wide: bool,
) -> None:
    """Reorder ``splitter`` children to match wide or narrow layout mode.

    Panel order is enforced by detaching both children with ``setParent(None)``
    and re-adding them via ``addWidget`` in the correct order, because
    ``QSplitter.setOrientation`` alone does not reposition existing children.

    Wide mode (``wide=True``): horizontal splitter; ``rows_scroll`` on the left
    (index 0), ``pool_panel`` on the right (index 1).

    Narrow mode (``wide=False``): vertical splitter; ``pool_panel`` on top
    (index 0), ``rows_scroll`` on the bottom (index 1).

    Args:
        splitter: The ``QSplitter`` whose orientation and child order to update.
        pool_panel: The source-token pool panel widget.
        rows_scroll: The ``QScrollArea`` wrapping the canonical rows panel.
        wide: ``True`` for wide (horizontal) mode; ``False`` for narrow
            (vertical) mode.

    Returns:
        ``None``.

    Side effects:
        Modifies ``splitter`` orientation and child-widget order in place.
    """
    # Detach both panels first so they can be re-inserted in the target order.
    rows_scroll.setParent(None)  # type: ignore[call-overload]
    pool_panel.setParent(None)  # type: ignore[call-overload]

    # Wide mode: horizontal splitter, rows (scrollable) left, pool right.
    # Narrow mode: vertical splitter, pool top, rows (scrollable) bottom.
    if wide:
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.addWidget(rows_scroll)
        splitter.addWidget(pool_panel)
    else:
        splitter.setOrientation(Qt.Orientation.Vertical)
        splitter.addWidget(pool_panel)
        splitter.addWidget(rows_scroll)
