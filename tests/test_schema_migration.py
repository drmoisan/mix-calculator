"""Forward-migration tests for :mod:`src.schema_serialization`.

Covers parsing legacy (pre-bump) schema JSON: the flat ``key.columns`` shape
migrating to ordered ``column-ref`` key parts, a legacy numeric column backfilling
``expected_dtype="float"``, and the parsed schema carrying the bumped format
version so a re-serialize emits the current format. Split from
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
