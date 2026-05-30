"""Feature D view Protocol interfaces (column-matching and schema builder).

This module defines the two ``typing.Protocol`` view contracts the Feature D
presenters depend on, kept separate from :mod:`src.gui.protocols` so that file
stays under the repository's 500-line cap and the existing four view protocols
are not moved. ``src.gui.protocols`` re-exports both names, so callers import
every GUI view protocol from one place.

Responsibilities:
    - Declare ``ColumnMatchingViewProtocol`` (manual matching dialog) and
      ``SchemaBuilderViewProtocol`` (tabbed schema-builder dialog).
    - Carry only the methods the presenters call; no Qt import, no Qt types.

Both protocols are ``@runtime_checkable`` and structural: any object (Qt widget
or test fake) implementing the listed methods satisfies the contract.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = [
    "ColumnMatchingViewProtocol",
    "SchemaBuilderViewProtocol",
]


@runtime_checkable
class ColumnMatchingViewProtocol(Protocol):
    """Contract for the manual column-matching dialog view.

    Purpose:
        The view that lets the user resolve a schema non-match by assigning
        unmatched required columns to source columns, reviewing fuzzy
        suggestions, and optionally marking optional columns as ignored.

    Responsibilities:
        Render the unmatched-required list, the source-column list, and ranked
        fuzzy suggestions; reflect assignments and ignore marks the presenter
        pushes; surface errors; and report the user's current assignments. It
        holds no logic; the ``ColumnMatchingPresenter`` drives it. All data is
        plain Python (``str``/``float`` in lists/dicts/tuples); no Qt types
        appear in the contract.

    Usage:
        The presenter calls the setters in response to a ``MatchResult`` and
        user actions; a Qt ``ColumnMatchingDialog`` (or a test fake) implements
        the contract.
    """

    def set_unmatched_required(self, items: list[tuple[str, tuple[str, ...]]]) -> None:
        """Render the unmatched required columns with their declared aliases.

        Args:
            items: One ``(canonical_name, aliases)`` pair per unmatched required
                column, in report order.

        Returns:
            ``None``.

        Side effects:
            Updates the view's unmatched-required list.
        """
        ...

    def set_source_columns(self, names: list[str]) -> None:
        """Render the available source column names.

        Args:
            names: The source header names, in source order.

        Returns:
            ``None``.

        Side effects:
            Updates the view's source-column list.
        """
        ...

    def set_fuzzy_suggestions(self, items: dict[str, list[tuple[str, float]]]) -> None:
        """Render ranked fuzzy suggestions per unmatched required column.

        Args:
            items: Mapping of unmatched required canonical name to a list of
                ``(source_name, score)`` candidate pairs, ranked by descending
                similarity score in ``[0.0, 1.0]``.

        Returns:
            ``None``.

        Side effects:
            Updates the view's suggestion surface.
        """
        ...

    def set_assignment(self, required: str, source: str) -> None:
        """Reflect that ``required`` has been assigned to a ``source`` column.

        Args:
            required: The canonical name of the required column.
            source: The source column name now assigned to ``required``.

        Returns:
            ``None``.

        Side effects:
            Updates the view's assignment display for ``required``.
        """
        ...

    def mark_ignored(self, required: str) -> None:
        """Reflect that the optional column ``required`` is marked ignored.

        Args:
            required: The canonical name of the optional column being ignored.

        Returns:
            ``None``.

        Side effects:
            Updates the view's ignore display for ``required``.
        """
        ...

    def show_error(self, message: str) -> None:
        """Display an error message to the user.

        Args:
            message: The human-readable error text to display.

        Returns:
            ``None``.

        Side effects:
            Updates the view's error surface.
        """
        ...

    def get_assignments(self) -> dict[str, str]:
        """Return the user's current required-to-source assignments.

        Returns:
            A mapping of required canonical name to the assigned source column
            name. Required columns the user has not assigned are absent.
        """
        ...


@runtime_checkable
class SchemaBuilderViewProtocol(Protocol):
    """Contract for the tabbed schema-builder dialog view.

    Purpose:
        The view that lets the user author or edit a schema across tabs
        (identity, columns, key, dedup, derived/formula, preview), with inline
        formula validation feedback.

    Responsibilities:
        Render the state the presenter pushes (identity, column rows, key, dedup,
        derived rows, preview rows) and report user edits back through getters;
        surface and clear inline formula errors. It holds no logic; the
        ``SchemaBuilderPresenter`` drives it. All data is plain Python; no Qt
        types appear in the contract.

    Usage:
        The presenter calls the setters as the in-progress schema changes and
        reads the getters when assembling the schema; a Qt ``SchemaBuilderDialog``
        (or a test fake) implements the contract.
    """

    def set_identity(self, name: str, version: str, description: str) -> None:
        """Render the schema identity fields.

        Args:
            name: The schema name.
            version: The schema version.
            description: The schema description.

        Returns:
            ``None``.

        Side effects:
            Updates the view's identity controls.
        """
        ...

    def get_identity(self) -> tuple[str, str, str]:
        """Return the user-entered identity fields.

        Returns:
            A ``(name, version, description)`` tuple.
        """
        ...

    def set_columns(self, rows: list[tuple[str, str, bool, tuple[str, ...]]]) -> None:
        """Render the column rows.

        Args:
            rows: One ``(canonical_name, role, required, aliases)`` tuple per
                column, in schema order.

        Returns:
            ``None``.

        Side effects:
            Updates the view's columns table.
        """
        ...

    def get_columns(self) -> list[tuple[str, str, bool, tuple[str, ...]]]:
        """Return the user-entered column rows.

        Returns:
            One ``(canonical_name, role, required, aliases)`` tuple per column.
        """
        ...

    def set_key(self, columns: tuple[str, ...], sku_coercion: bool) -> None:
        """Render the key composition.

        Args:
            columns: The ordered key column names.
            sku_coercion: Whether SKU coercion is enabled.

        Returns:
            ``None``.

        Side effects:
            Updates the view's key controls.
        """
        ...

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the user-entered key composition.

        Returns:
            A ``(columns, sku_coercion)`` tuple.
        """
        ...

    def set_dedup(self, mode: str, discriminator: str | None) -> None:
        """Render the dedup mode and discriminator.

        Args:
            mode: The dedup mode (``"none"`` or ``"collapse"``).
            discriminator: The discriminator column for collapse, or ``None``.

        Returns:
            ``None``.

        Side effects:
            Updates the view's dedup controls.
        """
        ...

    def get_dedup(self) -> tuple[str, str | None]:
        """Return the user-entered dedup mode and discriminator.

        Returns:
            A ``(mode, discriminator)`` tuple.
        """
        ...

    def set_derived(self, rows: list[tuple[str, str]]) -> None:
        """Render the derived/formula rows.

        Args:
            rows: One ``(name, expression)`` tuple per derived column.

        Returns:
            ``None``.

        Side effects:
            Updates the view's derived/formula controls.
        """
        ...

    def get_derived(self) -> list[tuple[str, str]]:
        """Return the user-entered derived/formula rows.

        Returns:
            One ``(name, expression)`` tuple per derived column.
        """
        ...

    def show_preview(self, rows: list[list[str]]) -> None:
        """Render preview rows produced by applying the in-progress schema.

        Args:
            rows: The preview rows, each a list of string cell values.

        Returns:
            ``None``.

        Side effects:
            Updates the view's preview surface.
        """
        ...

    def show_error(self, message: str) -> None:
        """Display a general (non-formula) error to the user.

        Args:
            message: The human-readable error text, for example a structural
                schema-validation failure surfaced on save or preview.

        Returns:
            ``None``.

        Side effects:
            Updates the view's error surface.
        """
        ...

    def show_formula_error(self, message: str) -> None:
        """Display an inline formula-validation error.

        Args:
            message: The descriptive formula error text.

        Returns:
            ``None``.

        Side effects:
            Updates the view's inline formula-error surface.
        """
        ...

    def clear_formula_error(self) -> None:
        """Clear the inline formula-validation error surface.

        Returns:
            ``None``.

        Side effects:
            Resets the view's inline formula-error surface.
        """
        ...
