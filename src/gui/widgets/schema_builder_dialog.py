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

        tabs = QTabWidget()
        tabs.addTab(self._identity.widget, "Identity")
        tabs.addTab(self._columns.widget, "Columns")
        tabs.addTab(self._key.widget, "Key")
        tabs.addTab(self._dedup.widget, "Dedup")
        tabs.addTab(self._derived.widget, "Derived")
        tabs.addTab(self._preview.widget, "Preview")

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

    def set_dedup(self, mode: str, discriminator: str | None) -> None:
        """Render the dedup mode and discriminator.

        Args:
            mode: The dedup mode (``"none"`` or ``"collapse"``).
            discriminator: The discriminator column for collapse, or ``None``.

        Returns:
            ``None``.

        Side effects:
            Updates the Dedup-tab controls.
        """
        self._dedup.mode.setCurrentText(mode)
        self._dedup.discriminator.setText(discriminator or "")

    def get_dedup(self) -> tuple[str, str | None]:
        """Return the user-entered dedup mode and discriminator.

        Returns:
            A ``(mode, discriminator)`` tuple; the discriminator is ``None`` when
            the field is blank.
        """
        mode = self._dedup.mode.currentText()
        text = self._dedup.discriminator.text().strip()
        return (mode, text or None)

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
