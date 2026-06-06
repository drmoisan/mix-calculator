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

from src.gui.widgets._schema_builder_drag_tabs import DragTabBinder
from src.gui.widgets._schema_builder_tabs import (
    build_columns_tab,
    build_dedup_tab,
    build_derived_tab,
    build_identity_tab,
    build_key_tab,
    build_preview_tab,
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

        self._identity = build_identity_tab()
        self._columns = build_columns_tab()
        self._key = build_key_tab()
        self._dedup = build_dedup_tab()
        self._derived = build_derived_tab()
        self._preview = build_preview_tab()

        # Bind the drag Columns/Key tabs to a shared in-progress state so the
        # column rows, source-token pool, dtype indicators, and ordered key parts
        # are driven by the tab presenters (Decision 2/4). The dialog's columns/key
        # view setters and getters route through this binder.
        self._drag = DragTabBinder(self._columns.columns_widget, self._key.key_widget)

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
        self._identity.name.setText(name)
        self._identity.version.setText(version)
        self._identity.description.setText(description)

    def get_identity(self) -> tuple[str, str, str]:
        """Return the user-entered identity fields.

        Returns:
            A ``(name, version, description)`` tuple.
        """
        return (
            self._identity.name.text(),
            self._identity.version.text(),
            self._identity.description.text(),
        )

    def set_columns(self, rows: list[tuple[str, str, bool, tuple[str, ...]]]) -> None:
        """Render the column rows on the drag Columns tab.

        Args:
            rows: One ``(canonical_name, role, required, aliases)`` tuple per
                column.

        Returns:
            ``None``.

        Side effects:
            Drives the drag Columns-tab widget (source pool, canonical rows, dtype
            indicators) and refreshes the Key tab's column-token pool via the binder.
        """
        self._drag.set_columns(rows)

    def get_columns(self) -> list[tuple[str, str, bool, tuple[str, ...]]]:
        """Return the live column rows from the drag Columns tab.

        Returns:
            One ``(canonical_name, role, required, aliases)`` tuple per column.
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
        """Render the key composition on the drag Key tab.

        Args:
            columns: The ordered key column names.
            sku_coercion: Whether SKU coercion is enabled.

        Returns:
            ``None``.

        Side effects:
            Renders the key column-ref parts (when no structured parts were pushed)
            and updates the retained SKU-coercion checkbox via the binder.
        """
        self._drag.set_key(columns, sku_coercion)
        self._key.sku_coercion.setChecked(sku_coercion)

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the live key composition from the drag Key tab.

        Returns:
            A ``(columns, sku_coercion)`` tuple; ``columns`` are the structured
            parts' column-ref values (or the flat key columns when none were
            composed), and the SKU-coercion flag is read from the checkbox.
        """
        # Read the SKU-coercion flag from the live checkbox into the binder so the
        # reported composition reflects the user's current checkbox state.
        self._drag.set_sku_coercion(self._key.sku_coercion.isChecked())
        return self._drag.get_key()

    # Sentinel discriminator value meaning "use the schema Key" (Decision 6). The
    # dedup dropdown offers this plus the existing column/derived names.
    _KEY_DISCRIMINATOR = "Key"

    def set_key_parts(self, parts: list[tuple[str, str]]) -> None:
        """Render the full structured key parts on the drag Key tab.

        The drag Key tab renders the complete ordered composition, including
        interleaved literal-text ("Generic Text") segments, not just the column-ref
        names :meth:`set_key` carries.

        Args:
            parts: One ``(kind, value)`` tuple per key part, in order.

        Returns:
            ``None``.

        Side effects:
            Replaces the binder's key parts and re-renders the drag Key tab.
        """
        self._drag.set_key_parts(parts)

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
            mode: The dedup mode (``"none"``, ``"collapse"``, or ``"aggregate"``).
            discriminator: The discriminator column for collapse/aggregate, or
                ``None``.

        Returns:
            ``None``.

        Side effects:
            Repopulates the discriminator dropdown and updates the dedup controls.
        """
        self._populate_discriminator_options()
        self._dedup.mode.setCurrentText(mode)
        # Only select a discriminator that exists in the dropdown so the invariant
        # "discriminator references an existing column (or the Key)" always holds.
        if discriminator is not None:
            index = self._dedup.discriminator.findText(discriminator)
            if index >= 0:
                self._dedup.discriminator.setCurrentIndex(index)

    def get_dedup(self) -> tuple[str, str | None]:
        """Return the user-entered dedup mode and discriminator.

        Returns:
            A ``(mode, discriminator)`` tuple; the discriminator is ``None`` when
            the dropdown is empty (no selectable column).
        """
        mode = self._dedup.mode.currentText()
        text = self._dedup.discriminator.currentText().strip()
        return (mode, text or None)

    def _populate_discriminator_options(self) -> None:
        """Populate the discriminator dropdown from existing columns + the Key.

        Builds the option list from the current Columns-tab canonical names and
        Derived-tab names plus the ``Key`` sentinel, so the dropdown only ever
        offers existing columns (or the Key) as discriminator (Decision 6).

        Returns:
            ``None``.

        Side effects:
            Rebuilds the discriminator dropdown items, preserving the current
            selection when it is still valid.
        """
        current = self._dedup.discriminator.currentText()
        # The Key sentinel is always offered as the default discriminator; the
        # existing canonical and derived names follow so only real targets appear.
        options = [self._KEY_DISCRIMINATOR]
        options.extend(canonical for canonical, _r, _req, _a in self.get_columns())
        options.extend(name for name, _expr in self.get_derived())
        self._dedup.discriminator.clear()
        self._dedup.discriminator.addItems(options)
        # Restore the prior selection when it is still a valid option so a
        # repopulate does not silently drop the user's choice.
        index = self._dedup.discriminator.findText(current)
        if index >= 0:
            self._dedup.discriminator.setCurrentIndex(index)

    def set_derived(self, rows: list[tuple[str, str]]) -> None:
        """Render the derived/formula rows as one ``name|expression`` line each.

        Args:
            rows: One ``(name, expression)`` tuple per derived column.

        Returns:
            ``None``.

        Side effects:
            Replaces the Derived-tab editor text and mirrors the derived columns to
            the drag Columns tab so they appear as selectable rows (Decision 7).
        """
        lines = [f"{name}|{expression}" for name, expression in rows]
        self._derived.editor.setPlainText("\n".join(lines))
        # Mirror the derived columns onto the drag Columns tab so an accepted
        # derived column surfaces as a selectable canonical row.
        self._drag.set_derived(rows)

    def get_derived(self) -> list[tuple[str, str]]:
        """Return the user-entered derived/formula rows.

        Returns:
            One ``(name, expression)`` tuple per non-empty editor line.
        """
        rows: list[tuple[str, str]] = []
        # Parse each non-blank line into a (name, expression) pair; the expression
        # may itself contain pipes, so split only on the first separator.
        for line in self._derived.editor.toPlainText().splitlines():
            if not line.strip():
                continue
            name, _, expression = line.partition("|")
            rows.append((name.strip(), expression.strip()))
        return rows

    def show_preview(self, rows: list[list[str]]) -> None:
        """Render preview rows produced by applying the in-progress schema.

        Args:
            rows: The preview rows, each a list of string cell values.

        Returns:
            ``None``.

        Side effects:
            Updates the Preview-tab label.
        """
        self._preview.rows_label.setText("\n".join(" | ".join(row) for row in rows))

    def show_error(self, message: str) -> None:
        """Display a general (non-formula) error in the formula-error surface.

        Args:
            message: The error text to display.

        Returns:
            ``None``.

        Side effects:
            Updates the Derived-tab error label.
        """
        self._derived.error_label.setText(message)

    def show_formula_error(self, message: str) -> None:
        """Display an inline formula-validation error.

        Args:
            message: The descriptive formula error text.

        Returns:
            ``None``.

        Side effects:
            Updates the Derived-tab error label.
        """
        self._derived.error_label.setText(message)

    def clear_formula_error(self) -> None:
        """Clear the inline formula-validation error surface.

        Returns:
            ``None``.

        Side effects:
            Resets the Derived-tab error label.
        """
        self._derived.error_label.setText("")

    def formula_error_text(self) -> str:
        """Return the inline formula/general error text (public test seam).

        Returns:
            The Derived-tab error label text.
        """
        return self._derived.error_label.text()

    def preview_text(self) -> str:
        """Return the rendered preview text (public test seam).

        Returns:
            The Preview-tab rows label text.
        """
        return self._preview.rows_label.text()

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
