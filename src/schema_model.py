"""Typed, persisted schema-definition model for the configurable-schema subsystem.

This module defines the frozen dataclass tree that represents a single source
schema (for example AOP or LE) as data rather than hardcoded constant lists. A
:class:`SchemaDefinition` captures the canonical column set and order, each
column's role and match aliases, the business-key composition, the dedup policy,
derived columns, blank-total fill rules, drop columns, and the sentinel-clean
label columns. The model is rich enough to express both the AOP schema (no
collapse) and the LE schema (collapse-by-key with additive measures, a derived
``YTG`` column, and the as-built ``Super Category <- PPG`` quirk).

Responsibilities:
    - Define the value objects (``ColumnSpec``, ``MeasureAggregation``,
      ``DedupPolicy``, ``DerivedColumnSpec``, ``KeySpec``, ``FillRule``) and the
      top-level ``SchemaDefinition`` aggregate.
    - Enforce structural invariants at construction time via ``__post_init__``,
      raising :class:`SchemaValidationError` with a descriptive message that
      names the offending reference.

Scope boundaries:
    - This module is pure data plus structural validation. It does not evaluate
      derived-column ``expression`` strings (that is Feature C), perform any I/O,
      or depend on anything outside the standard library.

Key invariants (enforced in ``SchemaDefinition.__post_init__``):
    - ``name`` and ``version`` are non-empty.
    - Every ``key.columns`` entry, ``dedup.measure_aggregations`` measure,
      ``derived_columns`` reference (``copy_from`` and the structurally declared
      dependency name), and ``fill_rules`` reference (``total`` and each
      component) names a declared ``ColumnSpec.canonical_name``.
    - When ``dedup.mode == "collapse"``, a ``discriminator_column`` is present
      and names a declared column.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Allowed enumerations for the constrained string fields. These are validated
# structurally in __post_init__ so an out-of-range value fails fast with a
# descriptive error rather than silently passing through serialization.
COLUMN_ROLES: frozenset[str] = frozenset(
    {"dimension", "measure", "discriminator", "drop"}
)
MEASURE_MODES: frozenset[str] = frozenset({"additive", "select_from"})
DEDUP_MODES: frozenset[str] = frozenset({"none", "collapse"})


class SchemaValidationError(Exception):
    """Raised when a schema violates a structural invariant at construction.

    Purpose:
        Signal that a :class:`SchemaDefinition` (or a nested value object) was
        constructed with structurally inconsistent data, for example a key
        column that names a column the schema never declares, or ``collapse``
        dedup mode without a discriminator column.

    Usage:
        The dataclass ``__post_init__`` methods raise this exception with a
        message that names the offending field or reference so the caller can
        locate the defect. Serialization (:mod:`src.schema_serialization`)
        allows this exception to propagate from ``__post_init__`` unchanged.
    """


@dataclass(frozen=True)
class ColumnSpec:
    """A single canonical column in a schema.

    Purpose:
        Describe one output column: its canonical name, semantic role, whether
        it is required in the source, the match aliases used to resolve it from
        a raw header, whether it carries numeric data, and whether its sentinel
        values are cleaned to ``None``.

    Attributes:
        canonical_name: The canonical output column name (verbatim, including
            any as-built typo such as ``"SKU Descripiton"``).
        role: One of :data:`COLUMN_ROLES` (``dimension``, ``measure``,
            ``discriminator``, ``drop``).
        required: Whether the column must be present in the source to resolve.
        aliases: Ordered match aliases used to resolve the column from a raw
            header. Stored as a tuple so the value object stays hashable.
        numeric: Whether the column carries numeric (float-coercible) data.
        sentinel_clean: Whether sentinel values in this column are cleaned to
            ``None`` after coercion (used for label columns).

    Raises:
        SchemaValidationError: If ``canonical_name`` is empty or ``role`` is not
            a recognized role.
    """

    canonical_name: str
    role: str
    required: bool = True
    aliases: tuple[str, ...] = ()
    numeric: bool = False
    sentinel_clean: bool = False

    def __post_init__(self) -> None:
        """Validate the column's name and role at construction time.

        Raises:
            SchemaValidationError: If ``canonical_name`` is empty/blank or
                ``role`` is not one of :data:`COLUMN_ROLES`.
        """
        if not self.canonical_name or not self.canonical_name.strip():
            raise SchemaValidationError("ColumnSpec.canonical_name must be non-empty")
        if self.role not in COLUMN_ROLES:
            raise SchemaValidationError(
                f"ColumnSpec '{self.canonical_name}' has invalid role "
                f"'{self.role}'; expected one of {sorted(COLUMN_ROLES)}"
            )


@dataclass(frozen=True)
class MeasureAggregation:
    """Per-measure aggregation rule applied when collapsing duplicate rows.

    Purpose:
        Describe how a single measure column is aggregated when a dedup policy
        collapses every source row sharing a business key into one output row.

    Attributes:
        measure: The canonical name of the measure column being aggregated.
        mode: One of :data:`MEASURE_MODES`. ``additive`` sums the measure across
            collapsed rows; ``select_from`` picks the value from the row whose
            discriminator equals one of ``select_values``.
        select_values: For ``select_from`` mode, the discriminator value(s) that
            select the source row. Empty for ``additive`` mode.

    Raises:
        SchemaValidationError: If ``measure`` is empty, ``mode`` is unrecognized,
            or ``select_from`` mode is declared without ``select_values``.
    """

    measure: str
    mode: str = "additive"
    select_values: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the measure name, mode, and select-value consistency.

        Raises:
            SchemaValidationError: If ``measure`` is empty, ``mode`` is not in
                :data:`MEASURE_MODES`, or ``select_from`` lacks ``select_values``.
        """
        if not self.measure or not self.measure.strip():
            raise SchemaValidationError("MeasureAggregation.measure must be non-empty")
        if self.mode not in MEASURE_MODES:
            raise SchemaValidationError(
                f"MeasureAggregation for '{self.measure}' has invalid mode "
                f"'{self.mode}'; expected one of {sorted(MEASURE_MODES)}"
            )
        # select_from must name at least one discriminator value to be meaningful;
        # additive ignores select_values entirely.
        if self.mode == "select_from" and not self.select_values:
            raise SchemaValidationError(
                f"MeasureAggregation for '{self.measure}' uses 'select_from' "
                "but declares no select_values"
            )


@dataclass(frozen=True)
class DedupPolicy:
    """How duplicate rows sharing a business key are collapsed.

    Purpose:
        Capture whether a schema collapses duplicate-key rows and, if so, the
        discriminator column and the per-measure aggregation rules.

    Attributes:
        mode: One of :data:`DEDUP_MODES`. ``none`` keeps every row; ``collapse``
            merges rows sharing the business key into one output row.
        discriminator_column: For ``collapse`` mode, the column that distinguishes
            the duplicate halves (for example the LE ``YTD/YTG`` column). ``None``
            when ``mode == "none"``.
        measure_aggregations: Per-measure aggregation rules applied on collapse.

    Raises:
        SchemaValidationError: If ``mode`` is unrecognized, or ``collapse`` mode
            is declared without a ``discriminator_column``.
    """

    mode: str = "none"
    discriminator_column: str | None = None
    measure_aggregations: tuple[MeasureAggregation, ...] = ()

    def __post_init__(self) -> None:
        """Validate the dedup mode and discriminator presence.

        Raises:
            SchemaValidationError: If ``mode`` is not in :data:`DEDUP_MODES`, or
                ``collapse`` mode does not declare a ``discriminator_column``.
        """
        if self.mode not in DEDUP_MODES:
            raise SchemaValidationError(
                f"DedupPolicy has invalid mode '{self.mode}'; "
                f"expected one of {sorted(DEDUP_MODES)}"
            )
        # collapse requires a discriminator to identify which rows to merge; the
        # cross-reference against declared columns is enforced by SchemaDefinition.
        if self.mode == "collapse" and not self.discriminator_column:
            raise SchemaValidationError(
                "DedupPolicy mode 'collapse' requires a discriminator_column"
            )


@dataclass(frozen=True)
class DerivedColumnSpec:
    """A column computed from other columns rather than read from the source.

    Purpose:
        Describe a derived output column. The ``expression`` is stored verbatim
        and is not evaluated in this feature (evaluation is Feature C). The
        optional ``copy_from`` captures the as-built quirk where a derived column
        is populated directly from another column's values.

    Attributes:
        name: The canonical name of the derived column.
        expression: The verbatim formula string (not evaluated here).
        copy_from: Optional canonical name of a column whose values populate this
            derived column directly (the LE ``Super Category <- PPG`` quirk).

    Raises:
        SchemaValidationError: If ``name`` is empty.
    """

    name: str
    expression: str = ""
    copy_from: str | None = None

    def __post_init__(self) -> None:
        """Validate the derived column's name.

        Raises:
            SchemaValidationError: If ``name`` is empty/blank.
        """
        if not self.name or not self.name.strip():
            raise SchemaValidationError("DerivedColumnSpec.name must be non-empty")


@dataclass(frozen=True)
class KeySpec:
    """The ordered business-key composition for a schema.

    Purpose:
        Capture which columns, in order, form the business key, and whether the
        SKU component is coerced (mirroring the existing ``coerce_sku`` behavior).

    Attributes:
        columns: Ordered canonical column names that compose the business key.
        sku_coercion: Whether the SKU key component is coerced before keying.

    Raises:
        SchemaValidationError: If ``columns`` is empty.
    """

    columns: tuple[str, ...]
    sku_coercion: bool = False

    def __post_init__(self) -> None:
        """Validate that the key declares at least one column.

        Raises:
            SchemaValidationError: If ``columns`` is empty.
        """
        if not self.columns:
            raise SchemaValidationError(
                "KeySpec.columns must declare at least one column"
            )


@dataclass(frozen=True)
class FillRule:
    """A blank-total fill rule: a total column populated from component columns.

    Purpose:
        Describe how a blank total cell is filled from its component columns (for
        example ``FY <- Jan..Dec`` or ``Q1 <- Jan,Feb,Mar``).

    Attributes:
        total: The canonical name of the total column being filled.
        components: Ordered canonical names of the columns summed into the total.

    Raises:
        SchemaValidationError: If ``total`` is empty or ``components`` is empty.
    """

    total: str
    components: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate the total name and that components are present.

        Raises:
            SchemaValidationError: If ``total`` is empty/blank or ``components``
                is empty.
        """
        if not self.total or not self.total.strip():
            raise SchemaValidationError("FillRule.total must be non-empty")
        if not self.components:
            raise SchemaValidationError(
                f"FillRule for total '{self.total}' must declare components"
            )


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
        ``ColumnSpec`` objects; ``key`` is a ``KeySpec``; ``dedup`` is a
        ``DedupPolicy``; ``derived_columns`` and ``fill_rules`` are ordered
        lists.

    As-built quirk representation:
        The LE ``Super Category <- PPG`` quirk is represented as a
        ``DerivedColumnSpec`` whose ``copy_from`` names the ``PPG`` column,
        preserving the behavior as structured data without evaluating any
        expression.

    Attributes:
        name: Schema identity name (non-empty).
        version: Schema format/content version (non-empty), present from day one
            to support later format migration.
        description: Human-readable description.
        source_sheet_hints: Ordered hints used to locate the source sheet.
        header_row: Zero-based header row index in the source.
        columns: Ordered canonical column specs.
        key: The business-key composition.
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
    key: KeySpec = field(default_factory=lambda: KeySpec(columns=("",)))
    dedup: DedupPolicy = field(default_factory=DedupPolicy)
    derived_columns: tuple[DerivedColumnSpec, ...] = ()
    fill_rules: tuple[FillRule, ...] = ()
    drop_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Enforce identity and cross-reference invariants at construction.

        Validates that the schema has a non-empty identity, and that every key,
        dedup, derived-column, and fill-rule reference names a column declared in
        ``columns``. When dedup mode is ``collapse``, the discriminator column
        must be declared.

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
        """Validate that every key column names a declared column.

        Args:
            declared: The set of declared/derived canonical column names.

        Raises:
            SchemaValidationError: If a key column is not declared.
        """
        # Each key component must resolve to a real column so keying is well-defined.
        for column_name in self.key.columns:
            if column_name not in declared:
                raise SchemaValidationError(
                    f"KeySpec references undeclared column '{column_name}'"
                )

    def _validate_dedup_references(self, declared: frozenset[str]) -> None:
        """Validate dedup discriminator and per-measure references.

        Args:
            declared: The set of declared/derived canonical column names.

        Raises:
            SchemaValidationError: If the discriminator column (when collapse) or
                any aggregated measure is not declared.
        """
        # A collapse discriminator must name a real column; DedupPolicy already
        # guarantees it is present, so here we only check it is declared.
        if (
            self.dedup.mode == "collapse"
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
