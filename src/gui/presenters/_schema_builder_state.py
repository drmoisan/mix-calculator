"""Pure in-progress schema state and assembly for the schema builder (Feature D).

This module holds the mutable, Qt-free working state of the schema-builder
presenter and the pure assembly of that state into a Feature A
:class:`~src.schema_model.SchemaDefinition`. Keeping assembly here (separate from
the presenter) lets both files stay under the 500-line cap and keeps the
state-to-model transform unit-testable in isolation.

Responsibilities:
    - ``SchemaBuilderState``: a plain mutable holder for identity, column rows,
      key, dedup, and derived/formula rows the presenter edits tab by tab.
    - ``assemble_schema``: build a validated ``SchemaDefinition`` from a state,
      letting the model's ``__post_init__`` raise ``SchemaValidationError`` on
      structurally invalid input.
    - ``known_column_names``: the canonical names a derived formula may reference.

Scope boundaries:
    - No Qt import, no I/O, no clock/RNG. Pure data plus a pure transform.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    KeySpec,
    SchemaDefinition,
)

__all__ = [
    "SchemaBuilderState",
    "assemble_schema",
    "known_column_names",
]


@dataclass
class SchemaBuilderState:
    """Mutable in-progress schema authored across the builder's tabs.

    Purpose:
        Hold the editable working data the schema-builder presenter accumulates
        from the Identity, Columns, Key, Dedup, and Derived tabs before it is
        assembled into an immutable :class:`SchemaDefinition`.

    Responsibilities:
        Carry plain-Python field values only; it performs no validation and no
        transform. Validation happens at assembly time via
        :func:`assemble_schema` (delegated to the model).

    Attributes:
        name: The schema name.
        version: The schema version.
        description: The schema description.
        columns: One ``(canonical_name, role, required, aliases)`` tuple per
            column, in schema order.
        key_columns: The ordered key column names.
        sku_coercion: Whether SKU coercion is enabled for the key.
        dedup_mode: The dedup mode (``"none"`` or ``"collapse"``).
        discriminator: The discriminator column for collapse, or ``None``.
        derived: One ``(name, expression)`` tuple per derived column.
    """

    name: str = ""
    version: str = "1.0"
    description: str = ""
    columns: list[tuple[str, str, bool, tuple[str, ...]]] = field(
        default_factory=lambda: []
    )
    key_columns: tuple[str, ...] = ()
    sku_coercion: bool = False
    dedup_mode: str = "none"
    discriminator: str | None = None
    derived: list[tuple[str, str]] = field(default_factory=lambda: [])


def known_column_names(state: SchemaBuilderState) -> list[str]:
    """Return the canonical names a derived formula may reference.

    Args:
        state: The in-progress builder state.

    Returns:
        The declared column canonical names followed by the derived column names,
        in order. Used to validate runtime formula entry against the known set.
    """
    # Both source columns and already-declared derived columns are valid formula
    # references, matching the model's reference-resolution rules.
    declared = [canonical for canonical, _role, _required, _aliases in state.columns]
    derived_names = [name for name, _expression in state.derived]
    return [*declared, *derived_names]


def assemble_schema(state: SchemaBuilderState) -> SchemaDefinition:
    """Assemble a validated :class:`SchemaDefinition` from the builder state.

    Builds the column, key, dedup, and derived value objects from the plain-data
    state and constructs the aggregate. Structural validation is delegated to the
    model's ``__post_init__``, so a structurally invalid state raises
    :class:`~src.schema_model.SchemaValidationError` here.

    Args:
        state: The in-progress builder state to assemble.

    Returns:
        The assembled, structurally valid :class:`SchemaDefinition`.

    Raises:
        SchemaValidationError: When the state violates a model invariant (for
            example an empty name, an undeclared key column, or ``collapse`` dedup
            without a discriminator), propagated from the model constructors.
    """
    # Build the column specs in order; each ColumnSpec validates its own
    # name/role at construction.
    column_specs = tuple(
        ColumnSpec(
            canonical_name=canonical,
            role=role,
            required=required,
            aliases=aliases,
        )
        for canonical, role, required, aliases in state.columns
    )

    # KeySpec requires at least one column; an empty key surfaces the model's
    # validation error rather than silently building an invalid schema.
    key = KeySpec(columns=state.key_columns, sku_coercion=state.sku_coercion)

    # DedupPolicy enforces that collapse mode carries a discriminator; pass the
    # discriminator through so collapse-mode schemas validate correctly.
    dedup = DedupPolicy(
        mode=state.dedup_mode,
        discriminator_column=state.discriminator,
    )

    derived_specs = tuple(
        DerivedColumnSpec(name=name, expression=expression)
        for name, expression in state.derived
    )

    return SchemaDefinition(
        name=state.name,
        version=state.version,
        description=state.description,
        columns=column_specs,
        key=key,
        dedup=dedup,
        derived_columns=derived_specs,
    )
