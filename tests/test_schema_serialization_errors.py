"""Error-handling tests for :mod:`src.schema_serialization`.

Covers descriptive error handling for malformed JSON, missing required fields,
unknown top-level and nested keys, and wrong field types (string, optional string,
boolean, integer, string-list, nullable string, object-list, and nested key/dedup
objects). Split from ``test_schema_serialization.py`` to keep both files under the
500-line cap; the round-trip and property tests remain there. All tests are pure
string transforms; no temp files, network, or filesystem access is used.
"""

from __future__ import annotations

import pytest

from src.schema_serialization import SchemaSerializationError, schema_from_json


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
