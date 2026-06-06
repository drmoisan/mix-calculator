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

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets._schema_builder_tabs import (
    build_columns_tab,
    build_dedup_tab,
    build_derived_tab,
    build_identity_tab,
    build_key_tab,
    build_preview_tab,
)

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
        _columns: The Columns-tab controls.
        _key: The Key-tab controls.
        _dedup: The Dedup-tab controls.
        _derived: The Derived-tab controls.
        _preview: The Preview-tab controls.
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
        """Render the column rows as one ``canonical|role|required|aliases`` line.

        Args:
            rows: One ``(canonical_name, role, required, aliases)`` tuple per
                column.

        Returns:
            ``None``.

        Side effects:
            Replaces the Columns-tab editor text.
        """
        # Encode each column as a single pipe-delimited line; aliases are joined
        # with commas. This keeps the passive editor simple while preserving every
        # field the protocol carries.
        lines = [
            f"{canonical}|{role}|{int(required)}|{','.join(aliases)}"
            for canonical, role, required, aliases in rows
        ]
        self._columns.editor.setPlainText("\n".join(lines))

    def get_columns(self) -> list[tuple[str, str, bool, tuple[str, ...]]]:
        """Return the user-entered column rows.

        Returns:
            One ``(canonical_name, role, required, aliases)`` tuple per non-empty
            editor line.
        """
        rows: list[tuple[str, str, bool, tuple[str, ...]]] = []
        # Parse each non-blank line back into the structured column tuple; blank
        # lines are skipped so trailing newlines do not create empty columns.
        for line in self._columns.editor.toPlainText().splitlines():
            if not line.strip():
                continue
            canonical, role, required, aliases = self._parse_column_line(line)
            rows.append((canonical, role, required, aliases))
        return rows

    @staticmethod
    def _parse_column_line(line: str) -> tuple[str, str, bool, tuple[str, ...]]:
        """Parse one ``canonical|role|required|aliases`` editor line.

        Args:
            line: The pipe-delimited column line.

        Returns:
            The parsed ``(canonical, role, required, aliases)`` tuple. Missing
            trailing fields default to ``dimension`` role, required ``True``, and
            no aliases.
        """
        parts = line.split("|")
        canonical = parts[0].strip()
        role = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "dimension"
        required = parts[2].strip() != "0" if len(parts) > 2 else True
        # Aliases are an optional trailing comma-separated field; split and drop
        # empties so "a,," does not yield blank aliases.
        if len(parts) > 3 and parts[3].strip():
            aliases = tuple(a.strip() for a in parts[3].split(",") if a.strip())
        else:
            aliases = ()
        return (canonical, role, required, aliases)

    def set_key(self, columns: tuple[str, ...], sku_coercion: bool) -> None:
        """Render the key composition.

        Args:
            columns: The ordered key column names.
            sku_coercion: Whether SKU coercion is enabled.

        Returns:
            ``None``.

        Side effects:
            Updates the Key-tab inputs.
        """
        self._key.columns.setText(", ".join(columns))
        self._key.sku_coercion.setChecked(sku_coercion)

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the user-entered key composition.

        Returns:
            A ``(columns, sku_coercion)`` tuple; blank entries are dropped.
        """
        raw = self._key.columns.text()
        columns = tuple(part.strip() for part in raw.split(",") if part.strip())
        return (columns, self._key.sku_coercion.isChecked())

    # Sentinel discriminator value meaning "use the schema Key" (Decision 6). The
    # dedup dropdown offers this plus the existing column/derived names.
    _KEY_DISCRIMINATOR = "Key"

    def set_key_parts(self, parts: list[tuple[str, str]]) -> None:
        """Render the structured key parts on the Key tab.

        The passive Key tab edits the column-ref parts as a comma-separated list
        (its existing control); the structured parts are flattened to the
        column-ref names here so a loaded structured key still displays. Literal
        ("Generic Text") parts are omitted from this passive rendering because the
        comma-separated control carries column names only; the drag-based Key tab
        (Phase 9) renders the full structured composition.

        Args:
            parts: One ``(kind, value)`` tuple per key part, in order.

        Returns:
            ``None``.

        Side effects:
            Updates the Key-tab columns control with the column-ref names.
        """
        # Render only the column-ref values in the comma-separated control so a
        # loaded structured key still shows its referenced columns.
        column_names = [value for kind, value in parts if kind == "column-ref"]
        self._key.columns.setText(", ".join(column_names))

    def set_column_dtypes(self, dtypes: list[tuple[str, str | None]]) -> None:
        """Accept per-column expected dtypes (passive no-op for this dialog).

        The text-based Columns tab does not render a dedicated expected-dtype
        column; the drag-based Columns tab (Phase 7) shows the expected dtype. This
        method exists so the dialog satisfies the view protocol; it intentionally
        does not alter the passive columns editor.

        Args:
            dtypes: One ``(canonical_name, expected_dtype)`` tuple per column.

        Returns:
            ``None``.
        """
        # The passive columns editor encodes only canonical|role|required|aliases,
        # so the expected dtype is not rendered here; the drag-based tab shows it.
        del dtypes

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
            Replaces the Derived-tab editor text.
        """
        lines = [f"{name}|{expression}" for name, expression in rows]
        self._derived.editor.setPlainText("\n".join(lines))

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
