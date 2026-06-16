"""Schema-builder dialog (passive tabbed Qt view for Feature D, AC4/AC5).

This passive Qt dialog implements :class:`SchemaBuilderViewProtocol`. It hosts
the Identity, Columns, Key, Dedup, Derived/Formula, and Preview tabs (built by
:mod:`src.gui.widgets._schema_builder_tabs`) and translates between the protocol's
structured state and the per-tab controls. It holds no service, matching, or
transform logic; the
:class:`~src.gui.presenters.schema_builder_presenter.SchemaBuilderPresenter` drives
it. Splitting tab construction into the helper module keeps this file under the
repository's 500-line cap.

Responsibilities:
    - Render the pushed identity/columns/key/dedup/derived/preview state.
    - Report user edits back through the protocol getters.
    - Surface and clear the inline formula-validation error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets import _key_multiselect_widget as keys
from src.gui.widgets import _schema_builder_derived_format as derived_fmt
from src.gui.widgets import _schema_builder_tabs as tabs_mod
from src.gui.widgets import _schema_dedup_discriminator as dedup
from src.gui.widgets import _schema_dialog_surfaces as surfaces
from src.gui.widgets import _schema_preview_table as preview
from src.gui.widgets._schema_builder_drag_tabs import DragTabBinder
from src.gui.widgets._schema_builder_window_setup import (
    apply_schema_builder_window_flags,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.presenters._schema_builder_state import PreviewSlice

__all__ = ["SchemaBuilderDialog"]


class SchemaBuilderDialog(QDialog):
    """Passive tabbed dialog implementing :class:`SchemaBuilderViewProtocol`.

    Purpose:
        Let the user author or edit a schema across tabs, with inline formula
        validation feedback and a preview of the applied schema.

    Responsibilities:
        Render the pushed state and report edits back through the protocol
        getters; surface and clear the inline formula error. It holds no logic;
        the presenter drives it.

    Usage:
        Constructed at the composition root. The presenter pushes state via the
        setters and reads the getters; tests drive edits by setting the control
        text directly and asserting on the getters.

    Attributes:
        _identity: The Identity-tab controls.
        _columns: The Columns-tab controls (drag-and-drop columns widget).
        _key: The Key-tab controls (drag-and-drop key widget + SKU checkbox).
        _dedup: The Dedup-tab controls.
        _derived: The Derived-tab controls (editor + "New derived column" button).
        _preview: The Preview-tab controls.
        _drag: The drag-tab binder routing the columns/key view setters and getters
            to the drag widgets via the columns/key tab presenters.
        _on_new_derived: Optional handler the composition root installs to open the
            derived-formula dialog when the "New derived column" button is clicked.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the tabbed dialog.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Schema Builder")
        # Make the dialog a resizable top-level window with min/max/restore
        # controls and a default size so all rows are reachable (AC-8).
        apply_schema_builder_window_flags(self)

        self._identity = tabs_mod.build_identity_tab()
        self._columns = tabs_mod.build_columns_tab()
        self._key = tabs_mod.build_key_tab()
        self._dedup = tabs_mod.build_dedup_tab()
        self._derived = tabs_mod.build_derived_tab()
        self._preview = tabs_mod.build_preview_tab()

        # Bind the drag Columns tab to a shared in-progress state so the column
        # rows, source-token pool, and dtype indicators are driven by the columns
        # presenter (Decision 4). The dialog's columns view setters/getters route
        # through this binder. The Key tab is a multi-select (D-2) the dialog reads
        # and writes directly, not through the binder.
        self._drag = DragTabBinder(self._columns.columns_widget)

        # The Derived-tab "New derived column" button opens the formula dialog; the
        # composition root installs the handler via set_new_derived_handler so the
        # dialog stays free of evaluator/state-assembly logic.
        self._on_new_derived: Callable[[], None] | None = None
        self._derived.new_button.clicked.connect(self._handle_new_derived_clicked)

        # Decision 10: tab order is Identity -> Derived -> Columns -> Key ->
        # Dedup -> Preview so derived columns are authored before they are
        # referenced on the Columns and Key tabs.
        tabs = QTabWidget()
        tabs.addTab(self._identity.widget, "Identity")
        tabs.addTab(self._derived.widget, "Derived")
        tabs.addTab(self._columns.widget, "Columns")
        tabs.addTab(self._key.widget, "Key")
        tabs.addTab(self._dedup.widget, "Dedup")
        tabs.addTab(self._preview.widget, "Preview")
        # Retain the tab widget so the tab order can be inspected (test seam).
        self._tabs = tabs

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(self._buttons)

    def set_identity(self, name: str, version: str, description: str) -> None:
        """Render the schema identity fields.

        Args:
            name: The schema name.
            version: The schema version.
            description: The schema description.

        Returns:
            ``None``.

        Side effects:
            Updates the Identity-tab inputs.
        """
        tabs_mod.set_identity_controls(self._identity, name, version, description)

    def get_identity(self) -> tuple[str, str, str]:
        """Return the user-entered identity fields.

        Returns:
            A ``(name, version, description)`` tuple.
        """
        return tabs_mod.read_identity_controls(self._identity)

    def set_columns(
        self, rows: list[tuple[str, str, bool, bool, tuple[str, ...]]]
    ) -> None:
        """Render the column rows on the drag Columns tab.

        Args:
            rows: One ``(canonical_name, role, required, in_output, aliases)``
                tuple per column. ``in_output`` carries output membership,
                distinct from ``required`` (source-presence).

        Returns:
            ``None``.

        Side effects:
            Drives the drag Columns-tab widget (source pool, canonical rows, dtype
            indicators) and repopulates the Key multi-select with the declared
            canonical columns (D-2), preserving the current key selection.
        """
        self._drag.set_columns(rows)
        # The Key tab selects from the declared canonical columns, so repopulate
        # its multi-select whenever the columns change (D-2, Option C).
        self._key.key_widget.set_available_columns(
            [canonical for canonical, _r, _req, _io, _a in rows]
        )

    def get_columns(self) -> list[tuple[str, str, bool, bool, tuple[str, ...]]]:
        """Return the live column rows from the drag Columns tab.

        Returns:
            One ``(canonical_name, role, required, in_output, aliases)`` tuple per
            column.
        """
        return self._drag.get_columns()

    def set_columns_preview_slice(self, preview_slice: PreviewSlice | None) -> None:
        """Seed the drag Columns tab with the masked preview slice (Decision 5).

        The composition root calls this before seeding so the draggable source-token
        pool reflects the opened sheet's masked header and the dtype check runs
        against the masked sample values.

        Args:
            preview_slice: The masked preview slice the builder reads, or ``None``.

        Returns:
            ``None``.

        Side effects:
            Records the slice on the binder and rebuilds the source-token pool.
        """
        self._drag.set_preview_slice(preview_slice)

    def set_key(self, columns: tuple[str, ...], sku_coercion: bool) -> None:
        """Render the key as a multi-select of declared columns (D-2, Option C).

        Args:
            columns: The ordered key column names to mark as selected.
            sku_coercion: Whether SKU coercion is enabled.

        Returns:
            ``None``.

        Side effects:
            Checks the selected columns in the Key multi-select and updates the
            retained SKU-coercion checkbox.
        """
        keys.set_key_controls(self._key, columns, sku_coercion)

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the live key selection from the Key multi-select (D-2).

        Returns:
            A ``(columns, sku_coercion)`` tuple; ``columns`` are the checked
            canonical columns in selection order, and the SKU-coercion flag is read
            from the checkbox.
        """
        return keys.read_key_controls(self._key)

    def set_key_parts(self, parts: list[tuple[str, str]]) -> None:
        """Select the ordered column-ref parts on the Key multi-select (D-2).

        Interleaved literal-text separators are ignored (re-derived at assembly).

        Args:
            parts: One ``(kind, value)`` tuple per key part, in order.

        Returns:
            ``None``.

        Side effects:
            Selects the ordered column-ref columns in the Key multi-select.
        """
        keys.set_key_parts_controls(self._key, parts)

    def set_column_dtypes(self, dtypes: list[tuple[str, str | None]]) -> None:
        """Render the per-column expected dtype on the drag Columns tab.

        Drives the binder so each canonical row shows its expected dtype and each
        matched row recomputes its dtype-check indicator against the masked preview
        slice.

        Args:
            dtypes: One ``(canonical_name, expected_dtype)`` tuple per column.

        Returns:
            ``None``.

        Side effects:
            Updates the binder's expected dtypes and re-renders the Columns tab.
        """
        self._drag.set_column_dtypes(dtypes)

    def set_dedup(self, mode: str, discriminator: str | None) -> None:
        """Render the dedup mode and discriminator.

        The discriminator control is a dropdown populated from the existing
        canonical and derived column names plus the ``Key`` sentinel (Decision 6),
        so a non-existent column cannot be selected. A discriminator not present in
        the dropdown is ignored (the selection stays at the current valid value).

        Args:
            mode: The dedup mode (auto/aggregate/collapse/none).
            discriminator: The discriminator column for collapse/aggregate, else
                ``None`` (auto/none require none).

        Returns:
            ``None``.

        Side effects:
            Repopulates the discriminator dropdown and updates the dedup controls.
        """
        canonical = [name for name, _r, _req, _io, _a in self.get_columns()]
        derived = [name for name, _expr in self.get_derived()]
        dedup.select_dedup_discriminator(
            self._dedup, mode, discriminator, canonical, derived
        )

    def get_dedup(self) -> tuple[str, str | None]:
        """Return the user-entered dedup mode and discriminator.

        Returns:
            A ``(mode, discriminator)`` tuple; the discriminator is ``None`` when
            the mode is ``auto`` (D-3) or the dropdown has no selectable column.
        """
        return dedup.read_dedup_controls(self._dedup)

    def set_derived(self, rows: list[tuple[str, str]]) -> None:
        """Render derived rows as ``name = expression`` lines for display.

        Known ``col("Name")`` references render in the bracketed ``[Name]`` display
        form (AC-4); the stored form is unchanged (D-1).

        Args:
            rows: One ``(name, stored_expression)`` tuple per derived column.

        Returns:
            ``None``.

        Side effects:
            Replaces the Derived-tab editor text and mirrors the derived columns to
            the drag Columns tab so they appear as selectable rows (Decision 7).
        """
        # Re-bracket known references for display; known names are the declared
        # canonical columns. Storage stays as bare ``col("Name")`` (D-1).
        known = [canonical for canonical, _r, _req, _io, _a in self.get_columns()]
        derived_fmt.render_derived_editor(self._derived.editor, rows, known)
        # Mirror the derived columns onto the drag Columns tab so an accepted
        # derived column surfaces as a selectable canonical row.
        self._drag.set_derived(rows)

    def get_derived(self) -> list[tuple[str, str]]:
        """Return the user-entered derived rows in stored ``col("Name")`` form.

        Display ``[Name]`` references are stripped to the stored form (AC-4, D-1)
        so nothing bracketed reaches the formula engine.

        Returns:
            One ``(name, stored_expression)`` tuple per non-empty editor line.
        """
        return derived_fmt.read_derived_editor(self._derived.editor)

    def show_preview(self, rows: list[list[str]]) -> None:
        """Render the applied-schema result rows in the Preview table (AC-9/AC-10).

        Thin wrapper: delegates table population and the empty-result message to
        :func:`~src.gui.widgets._schema_preview_table.render_preview`.

        Args:
            rows: The preview result rows, each a list of string cell values.

        Returns:
            ``None``.

        Side effects:
            Replaces the Preview-tab table contents and message label.
        """
        preview.render_preview(self._preview, rows)

    def show_error(self, message: str) -> None:
        """Render a general (non-formula) error on the error surfaces (AC-10).

        Thin wrapper over
        :func:`~src.gui.widgets._schema_dialog_surfaces.show_general_error`.

        Args:
            message: The error text to display.

        Returns:
            ``None``.

        Side effects:
            Updates the Derived-tab error label and the Preview-tab message label.
        """
        surfaces.show_general_error(self._derived, self._preview, message)

    def show_formula_error(self, message: str) -> None:
        """Display an inline formula-validation error (thin wrapper).

        Args:
            message: The descriptive formula error text.

        Returns:
            ``None``.

        Side effects:
            Updates the Derived-tab error label.
        """
        surfaces.set_formula_error(self._derived, message)

    def clear_formula_error(self) -> None:
        """Clear the inline formula-validation error surface (thin wrapper).

        Returns:
            ``None``.

        Side effects:
            Resets the Derived-tab error label.
        """
        surfaces.clear_formula_error(self._derived)

    def formula_error_text(self) -> str:
        """Return the inline formula/general error text (public test seam).

        Returns:
            The Derived-tab error label text.
        """
        return surfaces.formula_error_text(self._derived)

    def preview_text(self) -> str:
        """Return the rendered preview table cell values joined (public test seam).

        Returns:
            The Preview-tab table cell texts joined with spaces (empty when the
            table has no rows).
        """
        return preview.read_table_text(self._preview.table)

    def preview_message(self) -> str:
        """Return the Preview-tab message text (public test seam, AC-10).

        Returns:
            The Preview-tab message label text.
        """
        return surfaces.preview_message_text(self._preview)

    def set_new_derived_handler(self, handler: Callable[[], None]) -> None:
        """Install the handler the "New derived column" button invokes (Decision 7).

        The composition root installs a handler that opens the
        :class:`~src.gui.widgets._derived_formula_dialog.DerivedFormulaDialog`,
        keeping the dialog free of evaluator and state-assembly logic.

        Args:
            handler: A zero-argument callable invoked on each button click.

        Returns:
            ``None``.

        Side effects:
            Replaces the stored Derived-button handler.
        """
        self._on_new_derived = handler

    def _handle_new_derived_clicked(self) -> None:
        """Invoke the installed Derived-button handler when one is present.

        Returns:
            ``None``.

        Side effects:
            Calls the installed new-derived handler; a no-op when none is installed.
        """
        # The button is harmless until the composition root installs a handler;
        # without one a click does nothing rather than raising.
        if self._on_new_derived is not None:
            self._on_new_derived()

    def set_preview_refresh_handler(self, handler: Callable[[], None]) -> None:
        """Run ``handler`` whenever the user navigates to the Preview tab (AC-9).

        Connects the tab widget's ``currentChanged`` so ``handler`` runs when the
        Preview tab becomes current; the composition root installs a handler that
        drives ``presenter.update_preview`` so the preview renders on navigation.

        Args:
            handler: A zero-argument callable invoked on switching to Preview.

        Returns:
            ``None``.

        Side effects:
            Connects a ``currentChanged`` slot that calls ``handler`` for Preview.
        """
        preview_index = self._tabs.indexOf(self._preview.widget)

        def _on_changed(index: int) -> None:
            if index == preview_index:
                handler()

        self._tabs.currentChanged.connect(_on_changed)

    def tab_labels(self) -> list[str]:
        """Return the tab labels in display order (public test seam).

        Returns:
            The tab text for each tab, left to right (Decision 10 order).
        """
        return [self._tabs.tabText(index) for index in range(self._tabs.count())]

    def discriminator_options(self) -> list[str]:
        """Return the discriminator dropdown options (public test seam).

        Returns:
            The discriminator dropdown item texts, in order.
        """
        combo = self._dedup.discriminator
        return [combo.itemText(index) for index in range(combo.count())]
