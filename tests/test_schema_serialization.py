"""Unit and property tests for :mod:`src.schema_serialization`.

Covers a positive JSON round-trip on a representative schema, descriptive
error handling for malformed JSON / missing fields / unknown keys (top-level and
nested), and a ``hypothesis`` property asserting the round-trip is lossless for
generated valid schemas. All tests are pure string transforms; no temp files,
network, or filesystem access is used.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.schema_model import (
    SCHEMA_FORMAT_VERSION,
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeyPart,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
    column_ref,
    literal_text,
)
from src.schema_serialization import (
    SchemaSerializationError,
    schema_from_json,
    schema_to_json,
)


def _key(*names: str) -> KeySpec:
    """Build a column-ref-only ``KeySpec`` from the given column names.

    Args:
        names: Canonical column names that become ordered column-ref parts.

    Returns:
        A ``KeySpec`` whose parts are column-ref parts for ``names``.
    """
    return KeySpec(parts=tuple(column_ref(name) for name in names))


def _representative_schema() -> SchemaDefinition:
    """Return a schema exercising every nested shape for round-trip tests.

    Returns:
        A ``SchemaDefinition`` with columns, a multi-column key, a collapse
        dedup policy with an additive measure aggregation, a derived column with
        ``copy_from``, a fill rule, and a drop column.
    """
    return SchemaDefinition(
        name="representative",
        version=SCHEMA_FORMAT_VERSION,
        description="exercises every nested shape",
        source_sheet_hints=("Sheet1", "Data"),
        header_row=2,
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension", aliases=("Cust",)),
            ColumnSpec(canonical_name="Type", role="discriminator"),
            ColumnSpec(
                canonical_name="Jan",
                role="measure",
                numeric=True,
                expected_dtype="float",
            ),
            ColumnSpec(canonical_name="PPG", role="dimension", sentinel_clean=True),
        ),
        key=KeySpec(
            parts=(column_ref("Customer"), literal_text("-"), column_ref("Type")),
            sku_coercion=True,
        ),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Type",
            measure_aggregations=(MeasureAggregation(measure="Jan", mode="additive"),),
        ),
        derived_columns=(DerivedColumnSpec(name="Super Category", copy_from="PPG"),),
        fill_rules=(FillRule(total="Jan", components=("Jan",)),),
        drop_columns=("Type",),
    )


def test_round_trip_is_lossless() -> None:
    """A representative schema survives a JSON round-trip unchanged."""
    # Arrange
    schema = _representative_schema()

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored == schema


def test_malformed_json_raises() -> None:
    """Non-JSON text raises a descriptive serialization error."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaSerializationError, match="malformed"):
        schema_from_json("{not valid json")


def test_missing_required_field_raises() -> None:
    """A schema object missing 'version' raises a field-named error."""
    # Arrange
    text = '{"name": "x", "key": {"columns": ["x"]}, ' '"columns": []}'

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="missing required field 'version'"
    ):
        schema_from_json(text)


def test_unknown_top_level_key_raises() -> None:
    """An unknown top-level key is rejected and named in the message."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension"}], '
        '"bogus": 1}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="unknown key.*bogus"):
        schema_from_json(text)


def test_unknown_nested_key_raises() -> None:
    """An unknown key inside a nested column object is rejected and named."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension", '
        '"surprise": true}]}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="unknown key.*surprise"):
        schema_from_json(text)


def test_root_not_object_raises() -> None:
    """A JSON value that is not an object is rejected at the root."""
    # Arrange / Act / Assert
    with pytest.raises(SchemaSerializationError, match="must be a JSON object"):
        schema_from_json("[1, 2, 3]")


def test_string_field_wrong_type_raises() -> None:
    """A non-string value for a required string field is rejected by name."""
    # Arrange
    text = '{"name": 5, "version": "1.0", "key": {"columns": ["x"]}}'

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="field 'name' must be a string"):
        schema_from_json(text)


def test_optional_string_field_wrong_type_raises() -> None:
    """A non-string value for an optional string field is rejected by name."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "description": 7, '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'description' must be a string"
    ):
        schema_from_json(text)


def test_bool_field_wrong_type_raises() -> None:
    """A non-boolean value for a boolean field is rejected by name."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension", '
        '"numeric": 1}]}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'numeric' must be a boolean"
    ):
        schema_from_json(text)


def test_int_field_wrong_type_raises() -> None:
    """A non-integer (and bool) value for header_row is rejected by name."""
    # Arrange: a boolean is explicitly not accepted for the integer field.
    text = (
        '{"name": "x", "version": "1.0", "header_row": true, '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'header_row' must be an integer"
    ):
        schema_from_json(text)


def test_str_tuple_field_wrong_type_raises() -> None:
    """A non-list value where a list of strings is expected is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "drop_columns": "nope", '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'drop_columns' must be a list of strings"
    ):
        schema_from_json(text)


def test_str_tuple_non_string_element_raises() -> None:
    """A non-string element inside a string-list field is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "drop_columns": [1], '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="must contain only strings"):
        schema_from_json(text)


def test_nullable_string_wrong_type_raises() -> None:
    """A non-string, non-null value for a nullable string field is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "key": {"columns": ["x"]}, '
        '"columns": [{"canonical_name": "x", "role": "dimension"}], '
        '"derived_columns": [{"name": "d", "copy_from": 9}]}'
    )

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'copy_from' must be a string or null"
    ):
        schema_from_json(text)


def test_object_list_field_not_list_raises() -> None:
    """A non-list value where a list of objects is expected is rejected."""
    # Arrange
    text = '{"name": "x", "version": "1.0", "columns": 3, "key": {"columns": ["x"]}}'

    # Act / Assert
    with pytest.raises(
        SchemaSerializationError, match="field 'columns' must be a list"
    ):
        schema_from_json(text)


def test_object_list_element_not_object_raises() -> None:
    """A non-object element inside an object-list field is rejected."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "columns": [5], ' '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="must be a JSON object"):
        schema_from_json(text)


def test_missing_key_field_raises() -> None:
    """A schema object with no 'key' field is rejected by name."""
    # Arrange
    text = '{"name": "x", "version": "1.0", "columns": []}'

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="missing required field 'key'"):
        schema_from_json(text)


def test_dedup_wrong_type_raises() -> None:
    """A non-object 'dedup' value is rejected as not a JSON object."""
    # Arrange
    text = (
        '{"name": "x", "version": "1.0", "dedup": 1, '
        '"columns": [{"canonical_name": "x", "role": "dimension"}], '
        '"key": {"columns": ["x"]}}'
    )

    # Act / Assert
    with pytest.raises(SchemaSerializationError, match="dedup must be a JSON object"):
        schema_from_json(text)


def test_full_collapse_dedup_round_trips() -> None:
    """A schema with a select_from measure and nested dedup round-trips."""
    # Arrange
    schema = SchemaDefinition(
        name="sel",
        version=SCHEMA_FORMAT_VERSION,
        columns=(
            ColumnSpec(canonical_name="Type", role="discriminator"),
            ColumnSpec(
                canonical_name="Jan",
                role="measure",
                numeric=True,
                expected_dtype="float",
            ),
        ),
        key=_key("Type"),
        dedup=DedupPolicy(
            mode="collapse",
            discriminator_column="Type",
            measure_aggregations=(
                MeasureAggregation(
                    measure="Jan", mode="select_from", select_values=("YTD",)
                ),
            ),
        ),
    )

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored == schema


# --- New-field and structured-key round-trips (P2-T5) ---


def test_expected_dtype_round_trips() -> None:
    """A column's explicit expected_dtype survives a JSON round-trip."""
    # Arrange
    schema = SchemaDefinition(
        name="dt",
        version=SCHEMA_FORMAT_VERSION,
        columns=(
            ColumnSpec(canonical_name="When", role="dimension", expected_dtype="date"),
            ColumnSpec(canonical_name="Customer", role="dimension"),
        ),
        key=_key("Customer"),
    )

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored.columns[0].expected_dtype == "date"
    assert restored == schema


def test_column_aliases_round_trip_unchanged() -> None:
    """Persisted ColumnSpec aliases (matched source columns) survive round-trip."""
    # Arrange: aliases are the persisted store for matched source->canonical maps.
    schema = SchemaDefinition(
        name="alias",
        version=SCHEMA_FORMAT_VERSION,
        columns=(
            ColumnSpec(
                canonical_name="Customer",
                role="dimension",
                aliases=("src_col_a", "src_col_b"),
            ),
        ),
        key=_key("Customer"),
    )

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored.columns[0].aliases == ("src_col_a", "src_col_b")
    assert restored == schema


def test_structured_key_parts_round_trip_with_order_and_types() -> None:
    """Mixed structured key parts survive serialization preserving order/types."""
    # Arrange
    schema = SchemaDefinition(
        name="k",
        version=SCHEMA_FORMAT_VERSION,
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU", role="dimension"),
        ),
        key=KeySpec(
            parts=(
                column_ref("Customer"),
                literal_text(" / "),
                column_ref("SKU"),
                literal_text("X"),
            )
        ),
    )

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert [(p.kind, p.value) for p in restored.key.parts] == [
        ("column-ref", "Customer"),
        ("literal-text", " / "),
        ("column-ref", "SKU"),
        ("literal-text", "X"),
    ]


def test_aggregate_dedup_mode_round_trips() -> None:
    """A schema using the aggregate dedup mode round-trips with mode preserved."""
    # Arrange
    schema = SchemaDefinition(
        name="agg",
        version=SCHEMA_FORMAT_VERSION,
        columns=(
            ColumnSpec(canonical_name="Type", role="discriminator"),
            ColumnSpec(canonical_name="Customer", role="dimension"),
        ),
        key=_key("Customer"),
        dedup=DedupPolicy(mode="aggregate", discriminator_column="Type"),
    )

    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert
    assert restored.dedup.mode == "aggregate"
    assert restored == schema


def test_serialized_json_carries_current_format_version() -> None:
    """Serialized JSON always emits SCHEMA_FORMAT_VERSION as the version."""
    # Arrange
    schema = _representative_schema()

    # Act
    text = schema_to_json(schema)

    # Assert
    assert f'"version":"{SCHEMA_FORMAT_VERSION}"' in text


# --- Forward migration (P3-T5) ---


def test_legacy_key_columns_migrate_to_column_ref_parts() -> None:
    """Legacy flat key.columns parse into ordered column-ref parts."""
    # Arrange: a pre-bump schema using the flat columns key shape.
    text = (
        '{"name": "legacy", "version": "1.0", '
        '"columns": [{"canonical_name": "Customer", "role": "dimension"}, '
        '{"canonical_name": "Type", "role": "dimension"}], '
        '"key": {"columns": ["Customer", "Type"], "sku_coercion": true}}'
    )

    # Act
    restored = schema_from_json(text)

    # Assert
    assert [(p.kind, p.value) for p in restored.key.parts] == [
        ("column-ref", "Customer"),
        ("column-ref", "Type"),
    ]
    assert restored.key.sku_coercion is True


def test_legacy_numeric_backfills_expected_dtype_float() -> None:
    """A legacy numeric column parses with expected_dtype backfilled to float."""
    # Arrange
    text = (
        '{"name": "legacy", "version": "1.0", '
        '"columns": [{"canonical_name": "Jan", "role": "measure", '
        '"numeric": true}, '
        '{"canonical_name": "Customer", "role": "dimension"}], '
        '"key": {"columns": ["Customer"]}}'
    )

    # Act
    restored = schema_from_json(text)

    # Assert
    assert restored.columns[0].expected_dtype == "float"


def test_migration_sets_bumped_version_on_reserialize() -> None:
    """Parsing legacy JSON sets the bumped version so re-serialize is current."""
    # Arrange
    text = (
        '{"name": "legacy", "version": "1.0", '
        '"columns": [{"canonical_name": "Customer", "role": "dimension"}], '
        '"key": {"columns": ["Customer"]}}'
    )

    # Act
    restored = schema_from_json(text)
    reserialized = schema_to_json(restored)

    # Assert
    assert restored.version == SCHEMA_FORMAT_VERSION
    assert f'"version":"{SCHEMA_FORMAT_VERSION}"' in reserialized


def test_current_format_json_is_idempotent() -> None:
    """Parsing current-format JSON twice yields an identical schema (idempotent)."""
    # Arrange
    schema = _representative_schema()
    once = schema_from_json(schema_to_json(schema))

    # Act
    twice = schema_from_json(schema_to_json(once))

    # Assert
    assert once == twice == schema


# --- Property-based round-trip (T2 requirement) ---


# Bound generated names to a small ASCII alphabet and modest length so the
# strategy stays satisfiable and column-name references remain easy to keep
# consistent; the round-trip property is independent of name content.
_NAME = st.text(alphabet="abcdefghijklmnop", min_size=1, max_size=6)


def _draw_column(draw: st.DrawFn, name: str) -> ColumnSpec:
    """Draw a single ``ColumnSpec`` whose dtype survives the forward migration.

    The serialization forward-migration backfills ``expected_dtype="float"`` for
    a numeric column that declares no explicit dtype. To keep the round-trip
    equality stable, this helper assigns numeric columns an explicit dtype and
    leaves non-numeric columns with an explicit dtype or ``None``.

    Args:
        draw: The hypothesis draw callable.
        name: The canonical column name.

    Returns:
        A ``ColumnSpec`` whose ``expected_dtype`` is round-trip stable.
    """
    numeric = draw(st.booleans())
    # Numeric columns must carry an explicit dtype so the migration backfill does
    # not change the value on parse; non-numeric columns may be None or explicit.
    if numeric:
        expected_dtype = draw(st.sampled_from(["float", "integer"]))
    else:
        expected_dtype = draw(
            st.sampled_from([None, "string", "date", "bool", "float", "integer"])
        )
    return ColumnSpec(
        canonical_name=name,
        role=draw(st.sampled_from(["dimension", "measure", "discriminator"])),
        required=draw(st.booleans()),
        aliases=tuple(draw(st.lists(_NAME, max_size=2))),
        numeric=numeric,
        expected_dtype=expected_dtype,
        sentinel_clean=draw(st.booleans()),
    )


@st.composite
def _valid_schemas(draw: st.DrawFn) -> SchemaDefinition:
    """Generate a structurally valid ``SchemaDefinition``.

    The strategy guarantees ``__post_init__`` invariants hold by deriving every
    cross-reference (key columns, dedup discriminator/measures, derived
    ``copy_from``, fill-rule total/components) from the generated declared column
    names, so generation never raises ``SchemaValidationError``.

    Args:
        draw: The hypothesis draw callable.

    Returns:
        A valid ``SchemaDefinition`` instance.
    """
    # Draw a unique, ordered set of declared column names to reference from the
    # key, dedup, derived, and fill-rule sections.
    names = draw(st.lists(_NAME, min_size=1, max_size=5, unique=True))
    columns = tuple(_draw_column(draw, name) for name in names)

    # Key references at least one declared column, in declaration order. The key
    # is built from structured parts: each chosen column becomes a column-ref
    # part; an optional literal-text part may be interleaved.
    key_columns = tuple(
        draw(
            st.lists(
                st.sampled_from(names), min_size=1, max_size=len(names), unique=True
            )
        )
    )
    key_parts: list[KeyPart] = [column_ref(name) for name in key_columns]
    # Optionally append a literal-text part to exercise mixed-part serialization;
    # the key still contains at least one column-ref so it stays valid.
    if draw(st.booleans()):
        key_parts.append(literal_text(draw(st.text(max_size=4))))
    key = KeySpec(parts=tuple(key_parts), sku_coercion=draw(st.booleans()))

    # Dedup: either no collapse, or a collapsing mode (collapse or aggregate)
    # with a declared discriminator and additive aggregations over declared
    # measures.
    collapse_mode = draw(st.sampled_from([None, "collapse", "aggregate"]))
    if collapse_mode is not None:
        discriminator = draw(st.sampled_from(names))
        measures = draw(
            st.lists(st.sampled_from(names), max_size=len(names), unique=True)
        )
        dedup = DedupPolicy(
            mode=collapse_mode,
            discriminator_column=discriminator,
            measure_aggregations=tuple(
                MeasureAggregation(measure=measure, mode="additive")
                for measure in measures
            ),
        )
    else:
        dedup = DedupPolicy()

    # Derived columns whose copy_from (when present) references a declared column.
    derived = tuple(
        DerivedColumnSpec(
            name=draw(_NAME),
            expression=draw(st.text(max_size=8)),
            copy_from=draw(st.one_of(st.none(), st.sampled_from(names))),
        )
        for _ in range(draw(st.integers(min_value=0, max_value=2)))
    )

    # Fill rules whose total and components reference declared columns.
    fill_rules = tuple(
        FillRule(
            total=draw(st.sampled_from(names)),
            components=tuple(
                draw(st.lists(st.sampled_from(names), min_size=1, max_size=len(names)))
            ),
        )
        for _ in range(draw(st.integers(min_value=0, max_value=2)))
    )

    return SchemaDefinition(
        name=draw(_NAME),
        # Use the current format version so the always-emit-current serialization
        # round-trips to an equal object.
        version=SCHEMA_FORMAT_VERSION,
        description=draw(st.text(max_size=8)),
        source_sheet_hints=tuple(draw(st.lists(_NAME, max_size=2))),
        header_row=draw(st.integers(min_value=0, max_value=10)),
        columns=columns,
        key=key,
        dedup=dedup,
        derived_columns=derived,
        fill_rules=fill_rules,
        drop_columns=tuple(draw(st.lists(st.sampled_from(names), max_size=len(names)))),
    )


@given(schema=_valid_schemas())
def test_round_trip_property(schema: SchemaDefinition) -> None:
    """For every generated valid schema, the JSON round-trip is lossless."""
    # Act
    restored = schema_from_json(schema_to_json(schema))

    # Assert (hypothesis prints the failing example on failure)
    assert restored == schema
