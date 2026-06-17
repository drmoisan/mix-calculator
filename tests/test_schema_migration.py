"""Forward-migration tests for :mod:`src.schema_serialization`.

Covers parsing legacy (pre-bump) schema JSON: the flat ``key.columns`` shape
migrating to ordered ``column-ref`` key parts, a legacy numeric column backfilling
``expected_dtype="float"``, the parsed schema carrying the bumped format
version so a re-serialize emits the current format, and the ``located_by_name``
seeding that reproduces the pre-3.0 located-by-name set (required=False columns).
Split from
``test_schema_serialization.py`` to keep both files under the 500-line cap; the
round-trip and error-handling tests remain there. All tests are pure string
transforms; no temp files, network, or filesystem access is used.
"""

from __future__ import annotations

from src.schema_model import SCHEMA_FORMAT_VERSION
from src.schema_serialization import schema_from_json, schema_to_json


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


def _synthetic_two_column_schema(*, version: str, a_in_output: bool) -> str:
    """Build synthetic schema JSON with two required columns for migration tests.

    Args:
        version: The source schema ``version`` string to embed.
        a_in_output: Whether column ``A`` declares ``in_output: true``. Column
            ``B`` is always required and emitted; ``A`` is always required at the
            source so the required-output mapping is observable through ``A``.

    Returns:
        JSON text for a schema whose columns ``A`` and ``B`` both declare
        ``required: true`` and whose key references ``B``.
    """
    a_flags = "true" if a_in_output else "false"
    return (
        f'{{"name": "syn", "version": "{version}", '
        '"columns": ['
        '{"canonical_name": "A", "role": "dimension", "required": true, '
        f'"in_output": {a_flags}}}, '
        '{"canonical_name": "B", "role": "dimension", "required": true, '
        '"in_output": true}], '
        '"key": {"parts": [{"kind": "column-ref", "value": "B"}]}}'
    )


def test_pre_3_0_required_drops_when_not_emitted() -> None:
    """A 2.0 column required but not emitted becomes required=False under 3.0."""
    # Arrange: column A is required at the source but not in the output.
    text = _synthetic_two_column_schema(version="2.0", a_in_output=False)

    # Act
    restored = schema_from_json(text)
    by_name = {column.canonical_name: column for column in restored.columns}

    # Assert: required(3.0) = required(2.0) AND in_output(2.0); A drops, B stays.
    assert by_name["A"].required is False
    assert by_name["A"].in_output is False
    assert by_name["B"].required is True


def test_pre_3_0_required_stays_when_emitted() -> None:
    """A 2.0 column required and emitted stays required=True under 3.0."""
    # Arrange: column A is required at the source and in the output.
    text = _synthetic_two_column_schema(version="2.0", a_in_output=True)

    # Act
    restored = schema_from_json(text)
    by_name = {column.canonical_name: column for column in restored.columns}

    # Assert: emitted required columns remain required-output columns.
    assert by_name["A"].required is True
    assert by_name["A"].in_output is True


def test_3_0_required_passes_through_unchanged() -> None:
    """A 3.0 column keeps required=True even when in_output=False (no migration)."""
    # Arrange: a 3.0 source whose column A is required but not emitted; the
    # generic mapping must NOT run because the source already uses 3.0 semantics.
    text = _synthetic_two_column_schema(version="3.0", a_in_output=False)

    # Act
    restored = schema_from_json(text)
    by_name = {column.canonical_name: column for column in restored.columns}

    # Assert: a 3.0 input's required flag is preserved verbatim.
    assert by_name["A"].required is True
    assert by_name["A"].in_output is False


def test_3_0_round_trip_is_stable() -> None:
    """Serializing a parsed 3.0 schema and re-parsing yields an equal schema."""
    # Arrange: a 3.0 source with a non-emitted required column to confirm the
    # round-trip preserves required without re-applying the migration.
    text = _synthetic_two_column_schema(version="3.0", a_in_output=False)

    # Act
    first = schema_from_json(text)
    second = schema_from_json(schema_to_json(first))

    # Assert: the round-trip is idempotent for a 3.0 schema.
    assert second == first


def test_unparseable_version_is_treated_as_legacy() -> None:
    """A non-numeric major version is treated as pre-3.0 and migrates required.

    A version whose major component cannot be parsed as an integer is upgraded
    conservatively: the required-output mapping runs, so a column required but
    not emitted becomes required=False rather than being trusted as 3.0.
    """
    # Arrange: a version string with an unparseable major component; column A is
    # required but not emitted.
    text = _synthetic_two_column_schema(version="draft", a_in_output=False)

    # Act
    restored = schema_from_json(text)
    by_name = {column.canonical_name: column for column in restored.columns}

    # Assert: the legacy mapping ran, dropping A's required flag.
    assert by_name["A"].required is False


def _single_column_schema(
    *, version: str, required: bool, located_key: str | None = None
) -> str:
    """Build single-column schema JSON for located-by-name migration tests.

    Args:
        version: The source schema ``version`` string to embed.
        required: The column's source ``required`` flag.
        located_key: When ``None`` the JSON omits the ``located_by_name`` key
            entirely (exercising the seeding path); otherwise it injects the
            literal ``"located_by_name": <located_key>`` so an explicit value is
            present in the source.

    Returns:
        JSON text for a one-column schema whose key references that column.
    """
    required_flag = "true" if required else "false"
    located_clause = (
        "" if located_key is None else f', "located_by_name": {located_key}'
    )
    return (
        f'{{"name": "syn", "version": "{version}", '
        '"columns": ['
        '{"canonical_name": "A", "role": "dimension", '
        f'"required": {required_flag}{located_clause}}}], '
        '"key": {"parts": [{"kind": "column-ref", "value": "A"}]}}'
    )


def test_pre_3_0_required_false_seeds_located_by_name_true() -> None:
    """A 2.0 column required=false without the key seeds located_by_name=True.

    The pre-3.0 loader treated required=False columns as located-by-name; the
    migration must reproduce that set when the source omits the explicit field.
    """
    # Arrange: a 2.0 source column with required=false and no located_by_name key.
    text = _single_column_schema(version="2.0", required=False)

    # Act
    restored = schema_from_json(text)

    # Assert: the seeding rule located_by_name = not required(2.0) yields True.
    assert restored.columns[0].located_by_name is True


def test_pre_3_0_required_true_seeds_located_by_name_false() -> None:
    """A 2.0 column required=true without the key seeds located_by_name=False."""
    # Arrange: a 2.0 source column with required=true and no located_by_name key.
    text = _single_column_schema(version="2.0", required=True)

    # Act
    restored = schema_from_json(text)

    # Assert: a column that was required under the old loader was not located-by-name.
    assert restored.columns[0].located_by_name is False


def test_3_0_absent_located_by_name_defaults_false() -> None:
    """A 3.0 column without the key defaults to located_by_name=False (no seeding)."""
    # Arrange: a 3.0 source omits the field; the 2.0 seeding path must NOT run.
    text = _single_column_schema(version="3.0", required=False)

    # Act
    restored = schema_from_json(text)

    # Assert: 3.0 sources use the additive default rather than the seeding rule.
    assert restored.columns[0].located_by_name is False


def test_3_0_explicit_located_by_name_round_trips_idempotently() -> None:
    """A 3.0 column with explicit located_by_name=true round-trips stably."""
    # Arrange: a 3.0 source that declares located_by_name=true explicitly.
    text = _single_column_schema(version="3.0", required=False, located_key="true")

    # Act: parse, re-serialize, and parse again to confirm idempotence.
    first = schema_from_json(text)
    second = schema_from_json(schema_to_json(first))

    # Assert: the explicit value is preserved and the second round-trip is equal.
    assert first.columns[0].located_by_name is True
    assert second == first
