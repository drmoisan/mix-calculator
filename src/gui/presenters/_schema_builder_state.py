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

import re
from dataclasses import dataclass, field

from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    KeyPart,
    KeySpec,
    SchemaDefinition,
    column_ref,
    literal_text,
)

__all__ = [
    "PreviewSlice",
    "SchemaBuilderState",
    "assemble_schema",
    "known_column_names",
    "parse_key_pattern",
]


@dataclass(frozen=True)
class PreviewSlice:
    """A masked slice of already-read source rows passed into the builder.

    Purpose:
        Carry a confidentiality-masked sample of the active source's rows so the
        builder can render draggable source-column tokens and run the dtype check
        without performing any I/O of its own (spec Decision 5). The slice is a
        pure value object: the caller reads the rows once from the source preview,
        masks them, and hands the result to the builder.

    Responsibilities:
        Hold the header row and up to roughly 200 masked sample rows. It performs
        no reading, no masking, and no validation beyond shape; masking is the
        caller's responsibility and is enforced separately by the masking scan.

    Attributes:
        header: The ordered source column names (the masked preview header row).
        rows: The masked sample rows, each a tuple of cell values aligned to
            ``header`` by position. At most ~200 rows by convention.

    Constraints:
        No real workbook values or proprietary source column names may appear in
        any committed instance; only synthetic/masked content is permitted.
    """

    header: tuple[str, ...] = ()
    rows: tuple[tuple[object, ...], ...] = ()

    def column_values(self, name: str) -> list[object]:
        """Return the sampled values for one source column.

        Args:
            name: The source column name to extract; must appear in ``header``.

        Returns:
            The values in each sample row at ``name``'s position, in row order.
            An empty list when ``name`` is not present in ``header``.
        """
        # A name not in the header yields no values rather than raising, so the
        # dtype-check orchestration can skip unmatched columns gracefully.
        if name not in self.header:
            return []
        index = self.header.index(name)
        # Collect each row's value at the column's position; rows shorter than the
        # header (ragged input) contribute no value for the missing position.
        return [row[index] for row in self.rows if index < len(row)]


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
        dedup_mode: The dedup mode (``"none"``, ``"collapse"``, or
            ``"aggregate"``).
        discriminator: The discriminator column for collapse/aggregate, or
            ``None``.
        derived: One ``(name, expression)`` tuple per derived column.
        source_columns: The draggable source-column pool available for
            assignment, in source order. Recomputed at open time from the masked
            preview slice header; consumed columns are removed as they are
            matched to rows.
        consumed_columns: Mapping of canonical target name to the source column
            currently assigned (consumed) for it. A consumed source column may
            not match a second row until released.
        key_parts: The structured, ordered key parts (column-ref vs literal-text)
            authored on the Key tab, replacing the flat ``key_columns`` view once
            the Key tab drives composition.
        column_dtypes: Mapping of canonical column name to its expected data type
            (one of the dtype vocabulary values) or ``None`` when no explicit
            type is declared. Carried alongside the column rows so the Columns tab
            can render the expected type and the dtype check can target it.
        preview_slice: The masked preview slice the builder reads for the
            draggable token pool and the dtype check, or ``None`` for the blank
            menu path. The builder performs no I/O; it reads only this slice.
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
    source_columns: list[str] = field(default_factory=lambda: [])
    consumed_columns: dict[str, str] = field(default_factory=lambda: {})
    key_parts: list[KeyPart] = field(default_factory=lambda: [])
    column_dtypes: dict[str, str | None] = field(default_factory=lambda: {})
    preview_slice: PreviewSlice | None = None


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


# A default key pattern uses ``{ColumnName}`` for a column-ref part; any text
# outside braces is a literal-text ("Generic Text") part. This compiled pattern
# captures each ``{...}`` token so the parser can split the pattern into ordered
# column-ref and literal-text segments.
_KEY_PATTERN_TOKEN = re.compile(r"\{([^{}]*)\}")


def parse_key_pattern(pattern: str) -> list[KeyPart]:
    """Parse a default key pattern string into ordered structured key parts.

    Pattern grammar:
        A ``{ColumnName}`` token becomes a ``column-ref`` :class:`KeyPart`
        referencing ``ColumnName`` (trimmed). Any run of characters outside braces
        becomes a ``literal-text`` part carrying that exact substring. Tokens and
        literals are emitted in their left-to-right order so the rendered key
        preserves the pattern's composition. An empty ``{}`` token is invalid
        because a column-ref must name a column.

    Args:
        pattern: The default key pattern, for example ``"{Customer}-{SKU #}"``.
            An empty string yields no parts.

    Returns:
        The ordered :class:`KeyPart` list parsed from ``pattern``. Empty when
        ``pattern`` is empty.

    Raises:
        SchemaValidationError: If a ``{}`` token names an empty column (raised by
            :class:`KeyPart` construction for a blank column-ref value).
    """
    parts: list[KeyPart] = []
    cursor = 0
    # Walk each ``{...}`` token in order; the text between tokens is literal.
    for match in _KEY_PATTERN_TOKEN.finditer(pattern):
        # Any text preceding this token is a literal-text segment; preserve it
        # verbatim (including surrounding spaces such as separators).
        if match.start() > cursor:
            parts.append(literal_text(pattern[cursor : match.start()]))
        # The braced content names a column; trim incidental whitespace so the
        # reference matches a declared canonical name.
        parts.append(column_ref(match.group(1).strip()))
        cursor = match.end()
    # Trailing text after the last token is a final literal-text segment.
    if cursor < len(pattern):
        parts.append(literal_text(pattern[cursor:]))
    return parts


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
    # name/role at construction. The expected dtype is read from the parallel
    # column_dtypes map so a loaded/edited type round-trips into the model.
    column_specs = tuple(
        ColumnSpec(
            canonical_name=canonical,
            role=role,
            required=required,
            aliases=aliases,
            expected_dtype=state.column_dtypes.get(canonical),
        )
        for canonical, role, required, aliases in state.columns
    )

    # Prefer the structured key parts authored on the Key tab when present so
    # interleaved literal-text segments survive assembly. Fall back to deriving
    # column-ref parts from the flat key_columns for callers that only set names.
    # Either way an empty/all-literal key surfaces the model's validation error
    # rather than silently building an invalid schema.
    if state.key_parts:
        key_parts = tuple(state.key_parts)
    else:
        key_parts = tuple(column_ref(name) for name in state.key_columns)
    key = KeySpec(parts=key_parts, sku_coercion=state.sku_coercion)

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
