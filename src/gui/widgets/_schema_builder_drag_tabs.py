"""Drag-tab binding and view-setter routing for the schema-builder dialog.

This helper owns the integration between the schema-builder dialog's passive
view-protocol setters and the drag-and-drop Columns and Key tabs (Decision 2/4).
It is extracted from :mod:`src.gui.widgets.schema_builder_dialog` so that file
stays under the repository's 500-line cap once the drag tabs are wired.

The dialog constructs one :class:`DragTabBinder` over its
:class:`~src.gui.widgets._columns_tab_drag.ColumnsTabWidget` and
:class:`~src.gui.widgets._key_tab_drag.KeyTabWidget` and routes the
``SchemaBuilderViewProtocol`` setters/getters that concern columns and the key
through it. The binder maintains a private
:class:`~src.gui.presenters._schema_builder_state.SchemaBuilderState` mirroring
the pushed state and drives a
:class:`~src.gui.presenters._columns_tab_presenter.ColumnsTabPresenter` and a
:class:`~src.gui.presenters._key_tab_presenter.KeyTabPresenter` over it, so a
drop on either tab updates the shared state and re-renders the widget.

Responsibilities:
    - Translate ``set_columns``/``set_column_dtypes`` into the columns presenter's
      rendered rows, source-token pool, and per-row dtype indicators.
    - Translate ``set_key``/``set_key_parts`` into the key presenter's ordered
      parts and the key tab's draggable column-token pool.
    - Report the live column rows and key composition back through getters.

Scope boundaries:
    - Qt-widget routing plus presenter binding only. It performs no I/O and holds
      no schema-assembly logic; the tab presenters own state mutation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.presenters._columns_tab_presenter import ColumnsTabPresenter
from src.gui.presenters._key_tab_presenter import KeyTabPresenter
from src.gui.presenters._schema_builder_state import PreviewSlice, SchemaBuilderState

if TYPE_CHECKING:
    from src.gui.widgets._columns_tab_drag import ColumnsTabWidget
    from src.gui.widgets._key_tab_drag import KeyTabWidget

__all__ = ["DragTabBinder"]


class DragTabBinder:
    """Bind the drag Columns/Key tabs to a shared in-progress builder state.

    Purpose:
        Route the schema-builder dialog's column- and key-related view-protocol
        setters/getters to the drag-and-drop Columns and Key tab widgets, driving
        them through a :class:`ColumnsTabPresenter` and :class:`KeyTabPresenter`
        over one shared :class:`SchemaBuilderState`.

    Responsibilities:
        Maintain the mirrored builder state the master presenter pushes; render
        the columns rows, source-token pool, and dtype indicators; render the key
        parts and the key tab's column-token pool; report the live columns and key
        back to the dialog's getters. It performs no I/O.

    Usage:
        The dialog constructs one binder over its two drag widgets, then routes the
        relevant setters/getters to it. A drop on either widget mutates the shared
        state through the bound tab presenter, which re-renders the widget.

    Attributes:
        _columns_widget: The drag Columns tab widget driven by the columns
            presenter.
        _key_widget: The drag Key tab widget driven by the key presenter.
        _state: The mirrored in-progress builder state shared by both tab
            presenters.
        _columns_presenter: Drives the Columns tab over the shared state.
        _key_presenter: Drives the Key tab over the shared state.
    """

    def __init__(
        self, columns_widget: ColumnsTabWidget, key_widget: KeyTabWidget
    ) -> None:
        """Bind the tab presenters to the two drag widgets over a fresh state.

        Args:
            columns_widget: The drag Columns tab widget to drive.
            key_widget: The drag Key tab widget to drive.
        """
        self._columns_widget = columns_widget
        self._key_widget = key_widget
        self._state = SchemaBuilderState()
        self._columns_presenter = ColumnsTabPresenter(columns_widget, self._state)
        self._key_presenter = KeyTabPresenter(key_widget, self._state)
        # Route each widget's drop seam to its presenter so a drop mutates the
        # shared state and re-renders, instead of the widgets' default no-op.
        columns_widget.assign_column = self._columns_presenter.assign_column
        key_widget.add_key_part = self._key_presenter.add_part

    def set_columns(self, rows: list[tuple[str, str, bool, tuple[str, ...]]]) -> None:
        """Mirror the pushed column rows and render the Columns tab.

        Replaces the shared state's column rows, repopulates the source-token pool
        from any held preview slice, runs fuzzy pre-population so seeded rows reflect
        the source columns, and refreshes the Key tab's column-token pool so key
        parts are composed from the current canonical columns.

        Args:
            rows: One ``(canonical_name, role, required, aliases)`` tuple per
                column, in schema order.

        Returns:
            ``None``.

        Side effects:
            Rewrites the shared state's columns and source pool and re-renders both
            drag tabs.
        """
        self._state.columns = list(rows)
        # Reset the consumed map and rebuild the source pool from the slice header
        # so a re-push starts from a clean assignment state.
        self._state.consumed_columns = {}
        self._refresh_source_pool()
        # Pre-populate fuzzy matches and render rows/pool/indicators in one pass.
        self._columns_presenter.prepopulate()
        self._refresh_key_column_tokens()

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

    def get_columns(self) -> list[tuple[str, str, bool, tuple[str, ...]]]:
        """Return the live column rows from the shared state.

        Returns:
            One ``(canonical_name, role, required, aliases)`` tuple per column.
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
        self._columns_presenter.prepopulate()

    def set_key(self, columns: tuple[str, ...], sku_coercion: bool) -> None:
        """Mirror the flat key columns when no structured parts were pushed.

        Args:
            columns: The ordered key column names.
            sku_coercion: Whether SKU coercion is enabled.

        Returns:
            ``None``.

        Side effects:
            Records the SKU-coercion flag and, when no structured parts exist,
            renders the column-ref parts derived from ``columns``.
        """
        self._state.key_columns = columns
        self._state.sku_coercion = sku_coercion
        # Only derive parts from the flat columns when structured parts were not
        # already pushed, so set_key_parts (the richer signal) is not overwritten.
        if not self._state.key_parts:
            self._key_widget.set_parts([("column-ref", name) for name in columns])

    def set_key_parts(self, parts: list[tuple[str, str]]) -> None:
        """Mirror the structured key parts and render them on the Key tab.

        Args:
            parts: One ``(kind, value)`` tuple per key part, in order.

        Returns:
            ``None``.

        Side effects:
            Replaces the shared state's key parts and re-renders the Key tab,
            preserving interleaved literal-text segments.
        """
        from src.schema_model import column_ref, literal_text

        # Rebuild structured KeyPart objects so the shared state carries the full
        # composition (column-ref and literal-text) the model round-trips.
        rebuilt = [
            column_ref(value) if kind == "column-ref" else literal_text(value)
            for kind, value in parts
        ]
        self._state.key_parts = rebuilt
        self._key_widget.set_parts(parts)

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the live key composition from the shared state.

        Returns:
            A ``(columns, sku_coercion)`` tuple. ``columns`` is the ordered
            column-ref values of the structured parts when present, else the flat
            key columns.
        """
        # Prefer the structured parts' column-ref values so a drag-composed key
        # reports its referenced columns; fall back to the flat key columns.
        if self._state.key_parts:
            columns = tuple(p.value for p in self._state.key_parts if p.is_column_ref)
        else:
            columns = self._state.key_columns
        return (columns, self._state.sku_coercion)

    def set_sku_coercion(self, sku_coercion: bool) -> None:
        """Record the SKU-coercion flag read from the dialog's checkbox.

        Args:
            sku_coercion: Whether SKU coercion is enabled.

        Returns:
            ``None``.

        Side effects:
            Updates the shared state's SKU-coercion flag.
        """
        self._state.sku_coercion = sku_coercion

    def column_canonicals(self) -> list[str]:
        """Return the canonical column names for the discriminator dropdown.

        Returns:
            The declared canonical column names, in order.
        """
        return [canonical for canonical, _r, _req, _a in self._state.columns]

    def _refresh_source_pool(self) -> None:
        """Rebuild the source-token pool from the held preview slice header.

        Returns:
            ``None``.

        Side effects:
            Replaces the shared state's source-column pool with the slice header.
        """
        slice_ = self._state.preview_slice
        self._state.source_columns = list(slice_.header) if slice_ is not None else []

    def _refresh_key_column_tokens(self) -> None:
        """Refresh the Key tab's draggable column-token pool.

        The Key tab offers the same draggable column-name buttons as the Columns
        tab (spec section 5): the masked preview-slice header columns when a slice
        was seeded, so key parts are composed from the real source columns. Without
        a slice (the blank menu path) it falls back to the declared canonical names.

        Returns:
            ``None``.

        Side effects:
            Rebuilds the Key tab's column tokens from the preview-slice header (or
            the canonical names when no slice is present).
        """
        slice_ = self._state.preview_slice
        # Prefer the seeded source-header columns so the Key tab mirrors the Columns
        # tab's draggable buttons; fall back to canonical names for the blank path.
        if slice_ is not None and slice_.header:
            tokens = list(slice_.header)
        else:
            tokens = self.column_canonicals()
        self._key_widget.set_column_tokens(tokens)
