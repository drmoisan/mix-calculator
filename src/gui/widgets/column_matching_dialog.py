"""Manual column-matching dialog (passive Qt view for Feature D, AC3).

This passive Qt dialog implements :class:`ColumnMatchingViewProtocol`. It renders
the unmatched required columns (with their declared aliases), the source columns,
and the ranked fuzzy suggestions the presenter pushes, and reports the user's
assignments and the accept-and-save choice. It contains no service, matching, or
transform logic; the ``ColumnMatchingPresenter`` drives it and the composition
root wires user actions to the presenter.

Responsibilities:
    - Render unmatched-required, source-column, and fuzzy-suggestion state.
    - Reflect assignments and ignore marks the presenter pushes.
    - Report the current required-to-source assignments and the save choice.
    - Provide public test seams (``assign``/``set_accept_and_save``) mirroring the
      :class:`~src.gui.widgets.export_dialog.ExportDialog` pattern.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

__all__ = ["ColumnMatchingDialog"]


class ColumnMatchingDialog(QDialog):
    """Passive dialog implementing :class:`ColumnMatchingViewProtocol`.

    Purpose:
        Let the user resolve a schema header mismatch by assigning unmatched
        required columns to source columns, reviewing fuzzy suggestions, and
        choosing whether to persist the additions.

    Responsibilities:
        Render the unmatched-required list (with aliases), the source-column
        list, and per-column fuzzy suggestions; reflect assignments and ignore
        marks; and report assignments and the accept-and-save choice. It holds no
        logic; the presenter drives it.

    Usage:
        Constructed at the composition root. The presenter pushes state via the
        setters and reads :meth:`get_assignments`; tests drive assignments through
        the :meth:`assign` seam.

    Attributes:
        _unmatched_list: The unmatched-required display list.
        _source_list: The source-column display list.
        _suggestions_label: The rendered fuzzy-suggestions text.
        _error_label: The error-message surface.
        _save_checkbox: The "accept and save to schema" control.
        _assignments: The current required-to-source assignments.
        _ignored: The set of ignored required column names.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the dialog controls.

        Args:
            parent: Optional Qt parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Match Columns")

        self._unmatched_list = QListWidget()
        self._source_list = QListWidget()
        self._suggestions_label = QLabel("")
        self._error_label = QLabel("")
        self._save_checkbox = QCheckBox("Accept and save to schema")
        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Unmatched required columns:"))
        layout.addWidget(self._unmatched_list)
        layout.addWidget(QLabel("Source columns:"))
        layout.addWidget(self._source_list)
        layout.addWidget(self._suggestions_label)
        layout.addWidget(self._error_label)
        layout.addWidget(self._save_checkbox)
        layout.addWidget(self._buttons)

        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        # The presenter owns assignment/ignore state; the dialog mirrors it so it
        # can report the assignments back through the protocol getter.
        self._assignments: dict[str, str] = {}
        self._ignored: set[str] = set()
        self._optional_required: set[str] = set()

    def set_unmatched_required(self, items: list[tuple[str, tuple[str, ...]]]) -> None:
        """Render the unmatched required columns with their declared aliases.

        Args:
            items: ``(canonical_name, aliases)`` pairs, in report order.

        Returns:
            ``None``.

        Side effects:
            Replaces the unmatched-required list and resets assignment state.
        """
        self._unmatched_list.clear()
        self._assignments = {}
        self._ignored = set()
        # Render each unmatched column with its aliases so the operator sees what
        # the schema expected; aliases are shown inline when present.
        for canonical, aliases in items:
            alias_text = f" (aliases: {', '.join(aliases)})" if aliases else ""
            self._unmatched_list.addItem(f"{canonical}{alias_text}")

    def set_source_columns(self, names: list[str]) -> None:
        """Render the available source column names.

        Args:
            names: The source header names, in source order.

        Returns:
            ``None``.

        Side effects:
            Replaces the source-column list.
        """
        self._source_list.clear()
        for name in names:
            self._source_list.addItem(name)

    def set_fuzzy_suggestions(self, items: dict[str, list[tuple[str, float]]]) -> None:
        """Render ranked fuzzy suggestions per unmatched required column.

        Args:
            items: Mapping of required canonical name to ``(source, score)`` pairs
                ranked by descending similarity.

        Returns:
            ``None``.

        Side effects:
            Updates the suggestions label text.
        """
        lines: list[str] = []
        # Render one line per required column listing its ranked candidates with
        # two-decimal scores so the operator can pick the most likely source.
        for required, candidates in items.items():
            rendered = ", ".join(
                f"{source} ({score:.2f})" for source, score in candidates
            )
            lines.append(f"{required}: {rendered}")
        self._suggestions_label.setText("\n".join(lines))

    def set_assignment(self, required: str, source: str) -> None:
        """Reflect that ``required`` has been assigned to a ``source`` column.

        Args:
            required: The required canonical name.
            source: The assigned source column.

        Returns:
            ``None``.

        Side effects:
            Records the assignment and clears any prior ignore for ``required``.
        """
        self._ignored.discard(required)
        self._assignments[required] = source

    def mark_ignored(self, required: str) -> None:
        """Reflect that the optional column ``required`` is marked ignored.

        Args:
            required: The ignored canonical name.

        Returns:
            ``None``.

        Side effects:
            Records the ignore and clears any prior assignment for ``required``.
        """
        self._assignments.pop(required, None)
        self._ignored.add(required)

    def show_error(self, message: str) -> None:
        """Display an error message to the user.

        Args:
            message: The error text to display.

        Returns:
            ``None``.

        Side effects:
            Updates the error label.
        """
        self._error_label.setText(message)

    def get_assignments(self) -> dict[str, str]:
        """Return the user's current required-to-source assignments.

        Returns:
            A copy of the current assignment map.
        """
        return dict(self._assignments)

    def unmatched_texts(self) -> list[str]:
        """Return the rendered unmatched-required item texts (public test seam).

        Returns:
            The display text of each unmatched-required list item, in order.
        """
        return [
            self._unmatched_list.item(index).text()
            for index in range(self._unmatched_list.count())
        ]

    def source_texts(self) -> list[str]:
        """Return the rendered source-column item texts (public test seam).

        Returns:
            The display text of each source-column list item, in order.
        """
        return [
            self._source_list.item(index).text()
            for index in range(self._source_list.count())
        ]

    def suggestions_text(self) -> str:
        """Return the rendered fuzzy-suggestions text (public test seam).

        Returns:
            The suggestions label text.
        """
        return self._suggestions_label.text()

    def error_text(self) -> str:
        """Return the rendered error text (public test seam).

        Returns:
            The error label text.
        """
        return self._error_label.text()

    def set_optional_required(self, names: set[str]) -> None:
        """Record which required columns are optional (ignorable).

        The Ignore control is enabled only for optional columns; the presenter
        supplies the optional set so the dialog can gate the control.

        Args:
            names: The canonical names of optional (ignorable) columns.

        Returns:
            ``None``.

        Side effects:
            Replaces the optional-required set.
        """
        self._optional_required = set(names)

    def is_ignorable(self, required: str) -> bool:
        """Return whether ``required`` may be ignored (it is optional).

        Args:
            required: The canonical name to test.

        Returns:
            ``True`` when ``required`` is in the optional set.
        """
        return required in self._optional_required

    def assign(self, required: str, source: str) -> None:
        """Public test seam: record an assignment as a user action would.

        Args:
            required: The required canonical name.
            source: The assigned source column.

        Returns:
            ``None``.

        Side effects:
            Records the assignment (same path as :meth:`set_assignment`).
        """
        self.set_assignment(required, source)

    def set_accept_and_save(self, checked: bool) -> None:
        """Public test seam: set the accept-and-save checkbox state.

        Args:
            checked: The desired checkbox state.

        Returns:
            ``None``.

        Side effects:
            Updates the save checkbox.
        """
        self._save_checkbox.setChecked(checked)

    def is_accept_and_save_checked(self) -> bool:
        """Return whether the "accept and save to schema" box is checked.

        Returns:
            ``True`` when the user opted to persist the alias additions.
        """
        return self._save_checkbox.isChecked()
