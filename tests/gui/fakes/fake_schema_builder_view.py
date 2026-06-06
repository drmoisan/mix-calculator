"""Fake schema-builder view for the GUI presenter test suite.

Implements the schema-builder view Protocol, records the calls the presenter
makes, and returns controlled identity/column/key/dedup/derived edits. The fake
holds no logic; it lets presenter tests run with no ``QApplication`` and assert
on what the presenter pushed to the view.
"""

from __future__ import annotations


class FakeSchemaBuilderView:
    """Records calls and returns controlled edits for a schema-builder view.

    Purpose:
        Let schema-builder presenter tests assert on rendered state and supply
        controlled identity/column/key/dedup/derived edits, with no Qt.

    Attributes:
        identity_set: Each ``set_identity`` call as ``(name, version, desc)``.
        columns_set: Each ``set_columns`` argument, in order.
        keys_set: Each ``set_key`` call as ``(columns, sku_coercion)``.
        key_parts_set: Each ``set_key_parts`` call as a list of ``(kind, value)``.
        column_dtypes_set: Each ``set_column_dtypes`` call as a list of
            ``(canonical_name, expected_dtype)``.
        dedups_set: Each ``set_dedup`` call as ``(mode, discriminator)``.
        deriveds_set: Each ``set_derived`` argument, in order.
        previews: Each ``show_preview`` argument, in order.
        formula_errors: Each ``show_formula_error`` message, in order.
        clear_formula_calls: The number of ``clear_formula_error`` calls.
        errors: Each ``show_error`` message, in order.
        identity: The controlled ``get_identity`` tuple.
        columns: The controlled ``get_columns`` rows.
        key: The controlled ``get_key`` tuple.
        dedup: The controlled ``get_dedup`` tuple.
        derived: The controlled ``get_derived`` rows.
    """

    def __init__(self) -> None:
        """Initialize empty records and default controlled edit values."""
        self.identity_set: list[tuple[str, str, str]] = []
        self.columns_set: list[list[tuple[str, str, bool, bool, tuple[str, ...]]]] = []
        self.keys_set: list[tuple[tuple[str, ...], bool]] = []
        self.key_parts_set: list[list[tuple[str, str]]] = []
        self.column_dtypes_set: list[list[tuple[str, str | None]]] = []
        self.dedups_set: list[tuple[str, str | None]] = []
        self.deriveds_set: list[list[tuple[str, str]]] = []
        self.previews: list[list[list[str]]] = []
        self.formula_errors: list[str] = []
        self.clear_formula_calls = 0
        self.errors: list[str] = []
        # Controlled getter values the presenter reads on sync_from_view.
        self.identity: tuple[str, str, str] = ("", "1.0", "")
        self.columns: list[tuple[str, str, bool, bool, tuple[str, ...]]] = []
        self.key: tuple[tuple[str, ...], bool] = ((), False)
        self.dedup: tuple[str, str | None] = ("none", None)
        self.derived: list[tuple[str, str]] = []

    def set_identity(self, name: str, version: str, description: str) -> None:
        """Record an identity render call.

        Args:
            name: The schema name.
            version: The schema version.
            description: The schema description.

        Returns:
            ``None``.
        """
        self.identity_set.append((name, version, description))

    def get_identity(self) -> tuple[str, str, str]:
        """Return the controlled identity tuple.

        Returns:
            The configured ``(name, version, description)``.
        """
        return self.identity

    def set_columns(
        self, rows: list[tuple[str, str, bool, bool, tuple[str, ...]]]
    ) -> None:
        """Record a columns render call.

        Args:
            rows: The column rows.

        Returns:
            ``None``.
        """
        self.columns_set.append(list(rows))

    def get_columns(self) -> list[tuple[str, str, bool, bool, tuple[str, ...]]]:
        """Return the controlled column rows.

        Returns:
            The configured column rows.
        """
        return list(self.columns)

    def set_key(self, columns: tuple[str, ...], sku_coercion: bool) -> None:
        """Record a key render call.

        Args:
            columns: The key column names.
            sku_coercion: The SKU coercion flag.

        Returns:
            ``None``.
        """
        self.keys_set.append((columns, sku_coercion))

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the controlled key tuple.

        Returns:
            The configured ``(columns, sku_coercion)``.
        """
        return self.key

    def set_key_parts(self, parts: list[tuple[str, str]]) -> None:
        """Record a structured key-parts render call.

        Args:
            parts: One ``(kind, value)`` tuple per key part, in order.

        Returns:
            ``None``.
        """
        self.key_parts_set.append(list(parts))

    def set_column_dtypes(self, dtypes: list[tuple[str, str | None]]) -> None:
        """Record a per-column expected-dtype render call.

        Args:
            dtypes: One ``(canonical_name, expected_dtype)`` tuple per column.

        Returns:
            ``None``.
        """
        self.column_dtypes_set.append(list(dtypes))

    def set_dedup(self, mode: str, discriminator: str | None) -> None:
        """Record a dedup render call.

        Args:
            mode: The dedup mode.
            discriminator: The discriminator column, or ``None``.

        Returns:
            ``None``.
        """
        self.dedups_set.append((mode, discriminator))

    def get_dedup(self) -> tuple[str, str | None]:
        """Return the controlled dedup tuple.

        Returns:
            The configured ``(mode, discriminator)``.
        """
        return self.dedup

    def set_derived(self, rows: list[tuple[str, str]]) -> None:
        """Record a derived render call.

        Args:
            rows: The derived ``(name, expression)`` rows.

        Returns:
            ``None``.
        """
        self.deriveds_set.append(list(rows))

    def get_derived(self) -> list[tuple[str, str]]:
        """Return the controlled derived rows.

        Returns:
            The configured derived rows.
        """
        return list(self.derived)

    def show_preview(self, rows: list[list[str]]) -> None:
        """Record a preview render call.

        Args:
            rows: The preview rows.

        Returns:
            ``None``.
        """
        self.previews.append([list(row) for row in rows])

    def show_formula_error(self, message: str) -> None:
        """Record an inline formula error.

        Args:
            message: The formula error text.

        Returns:
            ``None``.
        """
        self.formula_errors.append(message)

    def clear_formula_error(self) -> None:
        """Record a formula-error clear call.

        Returns:
            ``None``.
        """
        self.clear_formula_calls += 1

    def show_error(self, message: str) -> None:
        """Record a general error message.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)
