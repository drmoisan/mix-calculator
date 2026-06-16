"""Spec value objects for the configurable-schema model.

This module holds the frozen dataclass value objects that compose a
:class:`~src.schema_model.SchemaDefinition`: ``ColumnSpec``,
``MeasureAggregation``, ``DedupPolicy``, ``DerivedColumnSpec``, ``KeySpec`` (and
its structured ``KeyPart`` parts), and ``FillRule``. It also defines the shared
:class:`SchemaValidationError` and the constrained-field enumerations
(``COLUMN_ROLES``, ``MEASURE_MODES``, ``DEDUP_MODES``, ``DTYPE_VOCAB``).

Responsibilities:
    - Define the spec-level value objects and enforce their structural
      invariants at construction time via ``__post_init__``.
    - Provide the dtype vocabulary and the legacy ``numeric``-to-dtype derivation
      so callers can resolve a column's expected data type deterministically.

Scope boundaries:
    - Pure data plus structural validation. No I/O, no expression evaluation, no
      dependency outside the standard library.
    - The top-level aggregate (:class:`~src.schema_model.SchemaDefinition`) and
      the cross-reference invariants live in :mod:`src.schema_model`, which
      re-exports every name defined here for backward-compatible imports.
"""

from __future__ import annotations

from dataclasses import dataclass

# Allowed enumerations for the constrained string fields. These are validated
# structurally in __post_init__ so an out-of-range value fails fast with a
# descriptive error rather than silently passing through serialization.
COLUMN_ROLES: frozenset[str] = frozenset(
    {"dimension", "measure", "discriminator", "drop"}
)
MEASURE_MODES: frozenset[str] = frozenset({"additive", "select_from"})
DEDUP_MODES: frozenset[str] = frozenset({"none", "collapse", "aggregate", "auto"})

# The expected-data-type vocabulary for ColumnSpec.expected_dtype. A column may
# declare exactly one of these, or None when no explicit type is asserted.
DTYPE_VOCAB: frozenset[str] = frozenset({"string", "integer", "float", "date", "bool"})

# The structured key-part kinds. A "column-ref" part references a canonical
# column by name; a "literal-text" part carries an arbitrary user-supplied
# string (the "Generic Text" token in the Key tab).
KEY_PART_KINDS: frozenset[str] = frozenset({"column-ref", "literal-text"})


class SchemaValidationError(Exception):
    """Raised when a schema violates a structural invariant at construction.

    Purpose:
        Signal that a :class:`~src.schema_model.SchemaDefinition` (or a nested
        value object) was constructed with structurally inconsistent data, for
        example a key column that names a column the schema never declares, or
        ``collapse`` dedup mode without a discriminator column.

    Usage:
        The dataclass ``__post_init__`` methods raise this exception with a
        message that names the offending field or reference so the caller can
        locate the defect. Serialization (:mod:`src.schema_serialization`)
        allows this exception to propagate from ``__post_init__`` unchanged.
    """


def derive_expected_dtype(*, numeric: bool, expected_dtype: str | None) -> str | None:
    """Resolve a column's effective expected data type.

    Purpose:
        Map a column's legacy ``numeric`` flag and its optional explicit
        ``expected_dtype`` to a single effective dtype string so callers (the
        dtype-check logic) have one deterministic answer.

    Args:
        numeric: The column's legacy ``numeric`` flag.
        expected_dtype: The explicit dtype declared on the column, or ``None``.

    Returns:
        The explicit ``expected_dtype`` when one is set; otherwise ``"float"``
        when ``numeric`` is True (legacy numeric columns coerce to float);
        otherwise ``None`` when no type can be derived.
    """
    # An explicit declaration always wins over the legacy boolean.
    if expected_dtype is not None:
        return expected_dtype
    # A legacy numeric column maps deterministically to float.
    if numeric:
        return "float"
    return None


@dataclass(frozen=True)
class ColumnSpec:
    """A single canonical column in a schema.

    Purpose:
        Describe one canonical column: its name, semantic role, whether it is
        required in the source, whether it appears in the final output, the match
        aliases used to resolve it from a raw header, whether it carries numeric
        data, its optional expected data type, and whether its sentinel values
        are cleaned to ``None``.

    Required vs. in_output:
        ``required`` and ``in_output`` are independent concepts. ``required``
        governs source-presence (must the column exist in the source workbook for
        the load to succeed; enforced by ``resolve_columns``). ``in_output``
        governs output-membership (does the column appear in the final table).
        They genuinely differ: ``KEY`` is ``required=False`` but ``in_output``
        (created by the loader, kept in output); the LE ``YTD/YTG`` discriminator
        is ``required=False, in_output=False`` (present in source, used for dedup,
        excluded from output); AOP ``YTG`` is ``required=False`` but ``in_output``
        (optional in source, produced by a fill rule, kept in output).

    Attributes:
        canonical_name: The canonical output column name (verbatim, including
            any as-built typo such as ``"SKU Descripiton"``).
        role: One of :data:`COLUMN_ROLES` (``dimension``, ``measure``,
            ``discriminator``, ``drop``).
        required: Whether the column must be present in the source to resolve.
            This is source-presence only; it does not determine output-membership.
        in_output: Whether the column appears in the final output table. Defaults
            to ``True``. Set ``False`` for processing-only columns (such as a
            dedup discriminator) that must be carried through resolve/collapse but
            excluded from the emitted output. Distinct from ``required``, which is
            source-presence.
        aliases: Ordered match aliases used to resolve the column from a raw
            header. This is also the persisted store for matched
            source-column-to-canonical mappings produced by the schema builder:
            on source-tab activation, matching consults these alias columns
            first to confirm a pre-existing schema matches the active sheet.
            Stored as a tuple so the value object stays hashable.
        numeric: Whether the column carries numeric (float-coercible) data.
        expected_dtype: Optional explicit expected data type, one of
            :data:`DTYPE_VOCAB` (``string``, ``integer``, ``float``, ``date``,
            ``bool``) or ``None``. When ``None`` and ``numeric`` is True, the
            effective dtype derives to ``"float"`` (see
            :func:`derive_expected_dtype`).
        sentinel_clean: Whether sentinel values in this column are cleaned to
            ``None`` after coercion (used for label columns).

    Raises:
        SchemaValidationError: If ``canonical_name`` is empty, ``role`` is not
            a recognized role, or ``expected_dtype`` is not in :data:`DTYPE_VOCAB`.
    """

    canonical_name: str
    role: str
    required: bool = True
    in_output: bool = True
    aliases: tuple[str, ...] = ()
    numeric: bool = False
    expected_dtype: str | None = None
    sentinel_clean: bool = False

    def __post_init__(self) -> None:
        """Validate the column's name, role, and expected dtype at construction.

        Raises:
            SchemaValidationError: If ``canonical_name`` is empty/blank, ``role``
                is not one of :data:`COLUMN_ROLES`, or ``expected_dtype`` is set
                to a value outside :data:`DTYPE_VOCAB`.
        """
        if not self.canonical_name or not self.canonical_name.strip():
            raise SchemaValidationError("ColumnSpec.canonical_name must be non-empty")
        if self.role not in COLUMN_ROLES:
            raise SchemaValidationError(
                f"ColumnSpec '{self.canonical_name}' has invalid role "
                f"'{self.role}'; expected one of {sorted(COLUMN_ROLES)}"
            )
        # An explicit expected dtype, when present, must be in the vocabulary so
        # the dtype check has a well-defined target type.
        if self.expected_dtype is not None and self.expected_dtype not in DTYPE_VOCAB:
            raise SchemaValidationError(
                f"ColumnSpec '{self.canonical_name}' has invalid expected_dtype "
                f"'{self.expected_dtype}'; expected one of {sorted(DTYPE_VOCAB)}"
            )

    def effective_dtype(self) -> str | None:
        """Return this column's effective expected data type.

        Returns:
            The explicit ``expected_dtype`` when set; otherwise ``"float"`` when
            ``numeric`` is True; otherwise ``None``.
        """
        return derive_expected_dtype(
            numeric=self.numeric, expected_dtype=self.expected_dtype
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
            and ``aggregate`` both merge rows sharing the business key into one
            output row using the per-measure aggregations; ``auto`` (D-3) groups by
            all ``dimension``-role columns and sums all ``measure``-role columns
            with no explicit discriminator.
        discriminator_column: For ``collapse``/``aggregate`` mode, the column
            that distinguishes the duplicate halves (for example the LE
            ``YTD/YTG`` column, or the schema Key). ``None`` when
            ``mode == "none"`` or ``mode == "auto"``.
        measure_aggregations: Per-measure aggregation rules applied on collapse.

    Raises:
        SchemaValidationError: If ``mode`` is unrecognized, or a collapsing mode
            (``collapse``/``aggregate``) is declared without a
            ``discriminator_column``. The ``auto`` mode requires no discriminator.
    """

    mode: str = "none"
    discriminator_column: str | None = None
    measure_aggregations: tuple[MeasureAggregation, ...] = ()

    def __post_init__(self) -> None:
        """Validate the dedup mode and discriminator presence.

        Raises:
            SchemaValidationError: If ``mode`` is not in :data:`DEDUP_MODES`, or
                a collapsing mode does not declare a ``discriminator_column``.
        """
        if self.mode not in DEDUP_MODES:
            raise SchemaValidationError(
                f"DedupPolicy has invalid mode '{self.mode}'; "
                f"expected one of {sorted(DEDUP_MODES)}"
            )
        # Only collapse and aggregate require a discriminator to identify which
        # rows to merge; the cross-reference against declared columns is enforced
        # by SchemaDefinition. The auto mode (D-3) derives the groupby from the
        # dimension roles and so requires no discriminator; none keeps all rows.
        if self.mode in {"collapse", "aggregate"} and not self.discriminator_column:
            raise SchemaValidationError(
                f"DedupPolicy mode '{self.mode}' requires a discriminator_column"
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
class KeyPart:
    """One ordered part of a structured business key.

    Purpose:
        Represent a single element of the business key as structured data,
        distinguishing a column reference from a literal-text ("Generic Text")
        segment. Replaces the former flat ``columns: tuple[str, ...]`` so literal
        text can be interleaved with column references without string overloading.

    Attributes:
        kind: One of :data:`KEY_PART_KINDS`. ``column-ref`` references a declared
            canonical column by name; ``literal-text`` carries an arbitrary
            user-supplied string concatenated into the key.
        value: For ``column-ref``, the referenced canonical column name (must be
            non-empty). For ``literal-text``, the literal string value (may be
            any string, including empty).

    Raises:
        SchemaValidationError: If ``kind`` is not recognized, or a ``column-ref``
            part has an empty ``value``.
    """

    kind: str
    value: str

    def __post_init__(self) -> None:
        """Validate the part kind and column-ref value at construction.

        Raises:
            SchemaValidationError: If ``kind`` is not in :data:`KEY_PART_KINDS`,
                or a ``column-ref`` part carries an empty/blank ``value``.
        """
        if self.kind not in KEY_PART_KINDS:
            raise SchemaValidationError(
                f"KeyPart has invalid kind '{self.kind}'; "
                f"expected one of {sorted(KEY_PART_KINDS)}"
            )
        # A column-ref must name a real column; a literal-text part may hold any
        # string, so only the column-ref case requires a non-empty value.
        if self.kind == "column-ref" and (not self.value or not self.value.strip()):
            raise SchemaValidationError(
                "KeyPart of kind 'column-ref' must reference a non-empty column name"
            )

    @property
    def is_column_ref(self) -> bool:
        """Return whether this part references a column.

        Returns:
            True when ``kind == "column-ref"``, otherwise False.
        """
        return self.kind == "column-ref"


def column_ref(name: str) -> KeyPart:
    """Construct a column-reference key part.

    Args:
        name: The canonical column name the part references.

    Returns:
        A ``KeyPart`` of kind ``"column-ref"`` for ``name``.
    """
    return KeyPart(kind="column-ref", value=name)


def literal_text(value: str) -> KeyPart:
    """Construct a literal-text key part.

    Args:
        value: The literal string the part contributes to the key.

    Returns:
        A ``KeyPart`` of kind ``"literal-text"`` for ``value``.
    """
    return KeyPart(kind="literal-text", value=value)


@dataclass(frozen=True)
class KeySpec:
    """The ordered business-key composition for a schema.

    Purpose:
        Capture which parts, in order, form the business key, and whether the
        SKU component is coerced (mirroring the existing ``coerce_sku`` behavior).
        Each part is a structured :class:`KeyPart` distinguishing column
        references from literal-text segments.

    Attributes:
        parts: Ordered :class:`KeyPart` parts composing the business key. Must
            contain at least one ``column-ref`` part.
        sku_coercion: Whether the SKU key component is coerced before keying.

    Raises:
        SchemaValidationError: If ``parts`` is empty or contains no
            ``column-ref`` part.
    """

    parts: tuple[KeyPart, ...]
    sku_coercion: bool = False

    def __post_init__(self) -> None:
        """Validate that the key declares at least one column-ref part.

        Raises:
            SchemaValidationError: If ``parts`` is empty or every part is a
                literal-text part (an all-literal key references no column).
        """
        if not self.parts:
            raise SchemaValidationError("KeySpec.parts must declare at least one part")
        # A key must reference at least one real column; an all-literal key is
        # not a meaningful business key.
        if not any(part.is_column_ref for part in self.parts):
            raise SchemaValidationError(
                "KeySpec must contain at least one column-ref part"
            )

    @property
    def column_names(self) -> tuple[str, ...]:
        """Return the ordered canonical names of the column-ref parts.

        Returns:
            A tuple of the ``value`` of each ``column-ref`` part, in order,
            excluding literal-text parts. Used by cross-reference validation and
            by callers that only need the referenced columns.
        """
        # Collect the referenced column names in order, ignoring literal parts.
        return tuple(part.value for part in self.parts if part.is_column_ref)


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
