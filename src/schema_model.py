"""Typed, persisted schema-definition model for the configurable-schema subsystem.

This module defines the top-level :class:`SchemaDefinition` aggregate that
represents a single source schema (for example AOP or LE) as data rather than
hardcoded constant lists. A :class:`SchemaDefinition` captures the canonical
column set and order, each column's role, match aliases, and expected data type,
the structured business-key composition, the dedup policy, derived columns,
blank-total fill rules, and drop columns. The model is rich enough to express
both the AOP schema (no collapse) and the LE schema (collapse-by-key with
additive measures, a derived ``YTG`` column, and the as-built
``Super Category <- PPG`` quirk).

Column flag semantics (format 3.0):
    - ``required`` means "required OUTPUT column": the column is part of the
      output-identity set (one value column plus its dimension columns). It no
      longer means source-presence. A column that is read only to feed a derived
      formula or a dedup discriminator is not ``required`` under 3.0.
    - ``in_output`` means "emitted in the final output table". It may be ``True``
      without ``required`` (for example a measure column that is emitted but is
      not part of the required-output identity set).

The spec-level value objects (``ColumnSpec``, ``MeasureAggregation``,
``DedupPolicy``, ``DerivedColumnSpec``, ``KeyPart``, ``KeySpec``, ``FillRule``),
the :class:`SchemaValidationError`, and the constrained-field enumerations live
in :mod:`src._schema_model_specs` and are re-exported here so existing imports
from ``src.schema_model`` continue to resolve unchanged.

Responsibilities:
    - Define the top-level ``SchemaDefinition`` aggregate.
    - Enforce cross-reference invariants at construction time via
      ``__post_init__``, raising :class:`SchemaValidationError` with a
      descriptive message that names the offending reference.
    - Publish :data:`SCHEMA_FORMAT_VERSION`, the current write-format version
      string (``"3.0"``).

Scope boundaries:
    - This module is pure data plus structural validation. It does not evaluate
      derived-column ``expression`` strings (that is Feature C), perform any I/O,
      or depend on anything outside the standard library.

Key invariants (enforced in ``SchemaDefinition.__post_init__``):
    - ``name`` and ``version`` are non-empty.
    - Every key column-ref part, ``dedup.measure_aggregations`` measure,
      ``derived_columns`` reference (``copy_from`` and the structurally declared
      dependency name), and ``fill_rules`` reference (``total`` and each
      component) names a declared ``ColumnSpec.canonical_name``.
    - When ``dedup.mode`` is ``collapse`` or ``aggregate``, a
      ``discriminator_column`` is present and names a declared column.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src._schema_model_specs import (
    COLUMN_ROLES,
    DEDUP_MODES,
    DTYPE_VOCAB,
    KEY_PART_KINDS,
    MEASURE_MODES,
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeyPart,
    KeySpec,
    MeasureAggregation,
    SchemaValidationError,
    column_ref,
    derive_expected_dtype,
    literal_text,
)

# The current schema write-format version. This is the single source of truth
# for the format version emitted by serialization and targeted by the forward
# migration in src.schema_serialization. The 3.0 bump introduces the
# required-output meaning of ``required``: a column's ``required`` flag now
# denotes membership in the required OUTPUT identity set (one value column plus
# its dimension columns), not mere source-presence. The forward migration
# recomputes ``required(3.0) = required(2.0) AND in_output(2.0)`` while
# preserving ``in_output`` so emitted output is unchanged. (The 2.0 bump that
# preceded it introduced the structured key-part model, the expected_dtype
# field, and the aggregate dedup mode.) SchemaDefinition.version remains a
# required per-instance field with no dataclass default; this constant is the
# value the current write path emits.
SCHEMA_FORMAT_VERSION: str = "3.0"

__all__ = [
    "COLUMN_ROLES",
    "DEDUP_MODES",
    "DTYPE_VOCAB",
    "KEY_PART_KINDS",
    "MEASURE_MODES",
    "SCHEMA_FORMAT_VERSION",
    "ColumnSpec",
    "DedupPolicy",
    "DerivedColumnSpec",
    "FillRule",
    "KeyPart",
    "KeySpec",
    "MeasureAggregation",
    "SchemaDefinition",
    "SchemaValidationError",
    "column_ref",
    "derive_expected_dtype",
    "literal_text",
]


@dataclass(frozen=True)
class SchemaDefinition:
    """A complete, self-contained schema definition for one source layout.

    Purpose:
        Represent the entire schema for a source (AOP or LE) as data: identity,
        source-sheet hints, header row, the canonical column set and order, the
        business key, the dedup policy, derived columns, blank-total fill rules,
        and drop columns. This is the serializable contract that later features
        (matching, configurable ETL, the GUI builder) read and write.

    JSON shape (mirrored by :mod:`src.schema_serialization`):
        ``{"name", "version", "description", "source_sheet_hints",
        "header_row", "columns", "key", "dedup", "derived_columns",
        "fill_rules", "drop_columns"}``. ``columns`` is an ordered list of
        ``ColumnSpec`` objects; ``key`` is a ``KeySpec`` with structured parts;
        ``dedup`` is a ``DedupPolicy``; ``derived_columns`` and ``fill_rules``
        are ordered lists.

    Version:
        The current write format is :data:`SCHEMA_FORMAT_VERSION` (``"3.0"``).
        The 3.0 format defines ``required`` as "required OUTPUT column" and
        ``in_output`` as "emitted in output (may be true without ``required``)".
        ``version`` is a required per-instance field with no dataclass default;
        the serialization layer emits :data:`SCHEMA_FORMAT_VERSION` as the
        current format and the forward migration upgrades pre-3.0 JSON to it,
        recomputing ``required`` from ``required AND in_output`` while preserving
        ``in_output`` so emitted output is unchanged.

    As-built quirk representation:
        The LE ``Super Category <- PPG`` quirk is represented as a
        ``DerivedColumnSpec`` whose ``copy_from`` names the ``PPG`` column,
        preserving the behavior as structured data without evaluating any
        expression.

    Attributes:
        name: Schema identity name (non-empty).
        version: Schema format/content version (non-empty). See
            :data:`SCHEMA_FORMAT_VERSION` for the current write format.
        description: Human-readable description.
        source_sheet_hints: Ordered hints used to locate the source sheet.
        header_row: Zero-based header row index in the source.
        columns: Ordered canonical column specs.
        key: The structured business-key composition.
        dedup: The dedup policy.
        derived_columns: Ordered derived column specs.
        fill_rules: Ordered blank-total fill rules.
        drop_columns: Ordered canonical names of columns dropped from the output.

    Raises:
        SchemaValidationError: If any structural invariant is violated (see the
            module docstring for the full list).
    """

    name: str
    version: str
    description: str = ""
    source_sheet_hints: tuple[str, ...] = ()
    header_row: int = 0
    columns: tuple[ColumnSpec, ...] = ()
    key: KeySpec = field(
        default_factory=lambda: KeySpec(parts=(KeyPart(kind="column-ref", value=" "),))
    )
    dedup: DedupPolicy = field(default_factory=DedupPolicy)
    derived_columns: tuple[DerivedColumnSpec, ...] = ()
    fill_rules: tuple[FillRule, ...] = ()
    drop_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Enforce identity and cross-reference invariants at construction.

        Validates that the schema has a non-empty identity, and that every key,
        dedup, derived-column, and fill-rule reference names a column declared in
        ``columns``. When dedup mode is ``collapse`` or ``aggregate``, the
        discriminator column must be declared.

        Raises:
            SchemaValidationError: With a message naming the offending reference
                when any invariant is violated.
        """
        if not self.name or not self.name.strip():
            raise SchemaValidationError("SchemaDefinition.name must be non-empty")
        if not self.version or not self.version.strip():
            raise SchemaValidationError("SchemaDefinition.version must be non-empty")

        declared = self._declared_column_names()
        self._validate_key_references(declared)
        self._validate_dedup_references(declared)
        self._validate_derived_references(declared)
        self._validate_fill_rule_references(declared)

    def required_output_columns(self) -> tuple[str, ...]:
        """Return the ordered canonical names of the required-output columns.

        Purpose:
            Expose the required OUTPUT identity set for this schema under the 3.0
            ``required`` semantics: the columns that together identify a row in
            the emitted output (one value column plus its dimension columns).
            Callers (matching, the configurable ETL gate, the GUI builder) read
            this to know which columns a source must supply to produce a valid
            output identity, independent of which additional columns are merely
            emitted (``in_output`` without ``required``).

        Returns:
            An ordered ``tuple[str, ...]`` of canonical names: every declared
            ``ColumnSpec`` whose ``required`` flag is ``True``, in declared
            ``columns`` order, followed by the names of any ``DerivedColumnSpec``
            the schema designates as a required output. The bundled schemas
            designate no required derived column, so the derived contribution is
            empty; the structure nonetheless supports a designated required
            derived name for later features. The result reads only ``required``
            and never ``in_output``, so an emitted-but-not-required column (for
            example the LE ``Super Category``) is excluded.
        """
        # Collect source columns flagged as required-output identity members,
        # preserving declared order so callers see a stable, schema-defined set.
        required_source = tuple(
            column.canonical_name for column in self.columns if column.required
        )
        # No DerivedColumnSpec carries a required-output designation in CF1, so
        # the derived contribution is empty; an empty tuple keeps the accessor
        # structurally extensible without changing current behavior.
        required_derived: tuple[str, ...] = ()
        return required_source + required_derived

    def _declared_column_names(self) -> frozenset[str]:
        """Return the set of canonical names declared by ``columns``.

        Derived columns are also valid reference targets for fill rules because a
        derived column (for example LE ``YTG``) can itself be a total; they are
        included so a fill rule may reference a derived total.

        Returns:
            A frozenset of every declared and derived canonical column name.
        """
        # Both source-declared and derived names are valid reference targets.
        column_names = {column.canonical_name for column in self.columns}
        derived_names = {derived.name for derived in self.derived_columns}
        return frozenset(column_names | derived_names)

    def _validate_key_references(self, declared: frozenset[str]) -> None:
        """Validate that every key column-ref part names a declared column.

        Args:
            declared: The set of declared/derived canonical column names.

        Raises:
            SchemaValidationError: If a key column-ref is not declared.
        """
        # Each column-ref part must resolve to a real column so keying is
        # well-defined; literal-text parts contribute no column reference.
        for column_name in self.key.column_names:
            if column_name not in declared:
                raise SchemaValidationError(
                    f"KeySpec references undeclared column '{column_name}'"
                )

    def _validate_dedup_references(self, declared: frozenset[str]) -> None:
        """Validate dedup discriminator and per-measure references.

        Args:
            declared: The set of declared/derived canonical column names.

        Raises:
            SchemaValidationError: If the discriminator column (when collapsing)
                or any aggregated measure is not declared.
        """
        # A collapsing discriminator must name a real column; DedupPolicy already
        # guarantees it is present, so here we only check it is declared.
        if (
            self.dedup.mode in {"collapse", "aggregate"}
            and self.dedup.discriminator_column is not None
            and self.dedup.discriminator_column not in declared
        ):
            raise SchemaValidationError(
                "DedupPolicy discriminator_column "
                f"'{self.dedup.discriminator_column}' is not a declared column"
            )
        # Every aggregated measure must resolve to a declared column.
        for aggregation in self.dedup.measure_aggregations:
            if aggregation.measure not in declared:
                raise SchemaValidationError(
                    "DedupPolicy measure_aggregations references undeclared "
                    f"measure '{aggregation.measure}'"
                )

    def _validate_derived_references(self, declared: frozenset[str]) -> None:
        """Validate that each derived column's ``copy_from`` is declared.

        Args:
            declared: The set of declared/derived canonical column names.

        Raises:
            SchemaValidationError: If a ``copy_from`` reference is not declared.
        """
        # copy_from is the only structurally declared dependency in Feature A; the
        # expression string is stored verbatim and not parsed for references here.
        for derived in self.derived_columns:
            if derived.copy_from is not None and derived.copy_from not in declared:
                raise SchemaValidationError(
                    f"DerivedColumnSpec '{derived.name}' copy_from references "
                    f"undeclared column '{derived.copy_from}'"
                )

    def _validate_fill_rule_references(self, declared: frozenset[str]) -> None:
        """Validate that fill-rule totals and components name declared columns.

        Args:
            declared: The set of declared/derived canonical column names.

        Raises:
            SchemaValidationError: If a fill-rule total or any component is not
                declared.
        """
        # Both the total and each contributing component must resolve to a real
        # column so the fill is computable downstream.
        for rule in self.fill_rules:
            if rule.total not in declared:
                raise SchemaValidationError(
                    f"FillRule references undeclared total column '{rule.total}'"
                )
            for component in rule.components:
                if component not in declared:
                    raise SchemaValidationError(
                        f"FillRule for total '{rule.total}' references undeclared "
                        f"component column '{component}'"
                    )
