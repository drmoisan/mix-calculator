"""Columns-tab binding and view-setter routing for the schema-builder dialog.

This helper owns the integration between the schema-builder dialog's passive
view-protocol setters and the drag-and-drop Columns tab (Decision 4). It is
extracted from :mod:`src.gui.widgets.schema_builder_dialog` so that file stays
under the repository's 500-line cap once the drag tab is wired.

The dialog constructs one :class:`DragTabBinder` over its
:class:`~src.gui.widgets._columns_tab_drag.ColumnsTabWidget` and routes the
``SchemaBuilderViewProtocol`` setters/getters that concern columns through it.
The binder maintains a private
:class:`~src.gui.presenters._schema_builder_state.SchemaBuilderState` mirroring
the pushed state and drives a
:class:`~src.gui.presenters._columns_tab_presenter.ColumnsTabPresenter` over it,
so a drop on the Columns tab updates the shared state and re-renders the widget.
The Key tab is a multi-select (D-2) the dialog reads/writes directly, not here.

Responsibilities:
    - Translate ``set_columns``/``set_column_dtypes`` into the columns presenter's
      rendered rows, source-token pool, and per-row dtype indicators.
    - Mirror the masked preview slice for the source pool and the row chooser.
    - Report the live column rows back through ``get_columns``.

Scope boundaries:
    - Qt-widget routing plus presenter binding only. It performs no I/O and holds
      no schema-assembly logic; the columns presenter owns state mutation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.presenters._columns_tab_presenter import ColumnsTabPresenter
from src.gui.presenters._schema_builder_state import PreviewSlice, SchemaBuilderState

if TYPE_CHECKING:
    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget

__all__ = ["DragTabBinder"]


class DragTabBinder:
    """Bind the drag Columns tab to a shared in-progress builder state.

    Purpose:
        Route the schema-builder dialog's column-related view-protocol
        setters/getters to the drag-and-drop Columns tab widget, driving it
        through a :class:`ColumnsTabPresenter` over a shared
        :class:`SchemaBuilderState`.

    Responsibilities:
        Maintain the mirrored builder state the master presenter pushes; render
        the columns rows, source-token pool, and dtype indicators; report the live
        columns back to the dialog's getter. It performs no I/O.

    Usage:
        The dialog constructs one binder over its Columns tab widget, then routes
        the relevant setters/getters to it. A drop mutates the shared state through
        the bound columns presenter, which re-renders the widget.

    Attributes:
        _columns_widget: The drag Columns tab widget driven by the columns
            presenter.
        _state: The mirrored in-progress builder state.
        _columns_presenter: Drives the Columns tab over the shared state.
    """

    def __init__(self, columns_widget: ColumnsTabWidget) -> None:
        """Bind the columns presenter to the Columns tab widget over a fresh state.

        Args:
            columns_widget: The drag Columns tab widget to drive.
        """
        self._columns_widget = columns_widget
        self._state = SchemaBuilderState()
        self._columns_presenter = ColumnsTabPresenter(columns_widget, self._state)
        # Route the widget's drop seam to its presenter so a drop mutates the
        # shared state and re-renders, instead of the widget's default no-op.
        columns_widget.assign_column = self._columns_presenter.assign_column
        columns_widget.clear_row = self._columns_presenter.clear_row
        # Route the Columns-tab row chooser to the presenter so picking a preview
        # row swaps the dtype glyph for that row's masked source value (AC-6).
        columns_widget.set_on_row_chosen(self._columns_presenter.set_preview_row)

    def set_columns(
        self, rows: list[tuple[str, str, bool, bool, tuple[str, ...]]]
    ) -> None:
        """Mirror the pushed column rows and render the Columns tab.

        Replaces the shared state's column rows, repopulates the source-token pool
        from any held preview slice, and runs fuzzy pre-population so seeded rows
        reflect the source columns.

        Args:
            rows: One ``(canonical_name, role, required, in_output, aliases)``
                tuple per column, in schema order. ``in_output`` carries output
                membership, distinct from ``required`` (source-presence).

        Returns:
            ``None``.

        Side effects:
            Rewrites the shared state's columns and source pool and re-renders the
            Columns tab.
        """
        self._state.columns = list(rows)
        # Reset the consumed map and rebuild the source pool from the slice header
        # so a re-push starts from a clean assignment state.
        self._state.consumed_columns = {}
        self._refresh_source_pool()
        # Pre-populate fuzzy matches and render rows/pool/indicators in one pass.
        self._columns_presenter.prepopulate()

    def set_column_dtypes(self, dtypes: list[tuple[str, str | None]]) -> None:
        """Mirror per-column expected dtypes and refresh the dtype indicators.

        Args:
            dtypes: One ``(canonical_name, expected_dtype)`` tuple per column.

        Returns:
            ``None``.

        Side effects:
            Updates the shared state's ``column_dtypes`` and re-renders the Columns
            tab so each matched row shows its dtype-check indicator.
        """
        self._state.column_dtypes = {name: dtype for name, dtype in dtypes}
        # Re-render so each matched row recomputes its dtype indicator against the
        # newly-declared expected types.
        self._columns_presenter.prepopulate()

    def get_columns(self) -> list[tuple[str, str, bool, bool, tuple[str, ...]]]:
        """Return the live column rows from the shared state.

        Returns:
            One ``(canonical_name, role, required, in_output, aliases)`` tuple per
            column.
        """
        return list(self._state.columns)

    def set_derived(self, rows: list[tuple[str, str]]) -> None:
        """Mirror the derived columns so they surface on the Columns tab.

        Decision 7: derived columns authored on the Derived tab become selectable
        columns on the Columns tab. The columns presenter appends the shared state's
        derived rows when it renders, so mirroring them here makes a newly-accepted
        derived column appear among the Columns-tab rows.

        Args:
            rows: One ``(name, expression)`` tuple per derived column, in order.

        Returns:
            ``None``.

        Side effects:
            Replaces the shared state's derived rows and re-renders the Columns tab.
        """
        self._state.derived = list(rows)
        # Re-render so the appended derived columns appear as Columns-tab rows.
        self._columns_presenter.prepopulate()

    def set_preview_slice(self, preview_slice: PreviewSlice | None) -> None:
        """Record the masked preview slice the Columns tab reads.

        Args:
            preview_slice: The masked preview slice, or ``None`` for the blank path.

        Returns:
            ``None``.

        Side effects:
            Updates the shared state's preview slice and rebuilds the source pool.
        """
        self._state.preview_slice = preview_slice
        self._refresh_source_pool()
        # Bound the Columns-tab row chooser to the new slice's row count so the user
        # can only pick a valid preview-row index (AC-6).
        row_count = len(preview_slice.rows) if preview_slice is not None else 0
        self._columns_widget.set_row_chooser_bounds(row_count)
        self._columns_presenter.prepopulate()

    def _refresh_source_pool(self) -> None:
        """Rebuild the source-token pool from the held preview slice header.

        Returns:
            ``None``.

        Side effects:
            Replaces the shared state's source-column pool with the slice header.
        """
        slice_ = self._state.preview_slice
        self._state.source_columns = list(slice_.header) if slice_ is not None else []
