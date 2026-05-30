"""Typed JSON-boundary accessors shared by the schema serialization adapter.

This module holds the typed primitives that contain the untyped ``json.loads``
boundary for :mod:`src.schema_serialization`: the JSON value type aliases, the
:class:`SchemaSerializationError` exception, and the small ``_require_*`` /
``_optional_*`` accessors that narrow a parsed value to a concrete type and raise
a descriptive error on a wrong type, a missing required field, or an unknown key.

The accessors live here (rather than in ``schema_serialization``) so the adapter
module stays under the 500-line file limit while keeping the per-shape builders
and public functions together. These helpers are pure, side-effect-free, and
depend only on the standard library.

Responsibilities:
    - Define ``JsonValue``/``JsonObject`` and ``SchemaSerializationError``.
    - Provide typed accessors that validate and narrow parsed JSON values.

Scope boundaries:
    - No dataclass construction and no domain knowledge of the schema shape; the
      per-shape reconstruction lives in :mod:`src.schema_serialization`.
"""

from __future__ import annotations

from typing import Any, cast

# JSON-encodable primitive values produced/consumed by the serialization adapter.
# Used to keep the accessors fully typed without leaking ``Any`` into callers.
JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]


class SchemaSerializationError(Exception):
    """Raised when schema JSON cannot be parsed into a ``SchemaDefinition``.

    Purpose:
        Signal a serialization-boundary failure: malformed JSON text, a missing
        required field, an unknown/extra key, or a value of the wrong JSON type.
        The message names the offending location (key or field) so the caller can
        locate the defect, rather than surfacing a bare ``KeyError``/``ValueError``.

    Usage:
        Raised by the accessors here and by ``schema_from_json`` in
        :mod:`src.schema_serialization`. Structural model invariants are enforced
        separately by ``SchemaValidationError`` from :mod:`src.schema_model`.
    """


def reject_unknown_keys(
    obj: JsonObject, allowed: tuple[str, ...], context: str
) -> None:
    """Reject any object key not in ``allowed``, naming the offenders.

    Args:
        obj: The JSON object to check.
        allowed: The permitted key names for this object shape.
        context: A short label for the object shape used in the error message.

    Raises:
        SchemaSerializationError: If any key is not in ``allowed``; the message
            names the offending key(s).
    """
    allowed_set = frozenset(allowed)
    # Collect every extra key so the message can name all offenders at once.
    unknown = [key for key in obj if key not in allowed_set]
    if unknown:
        raise SchemaSerializationError(
            f"{context} object has unknown key(s): {sorted(unknown)}"
        )


def require_object(value: Any, context: str) -> JsonObject:
    """Narrow an untyped parsed value to a typed JSON object.

    Args:
        value: The untyped value from ``json.loads`` (typed ``Any`` at the
            boundary).
        context: A short label for the value used in the error message.

    Returns:
        The value as a typed ``JsonObject``.

    Raises:
        SchemaSerializationError: If ``value`` is not a JSON object.
    """
    if not isinstance(value, dict):
        raise SchemaSerializationError(
            f"{context} must be a JSON object, got {type(value).__name__}"
        )
    # The dict came from json.loads, whose keys are always str; cast narrows the
    # boundary value to the typed alias so downstream access is fully typed.
    return cast("JsonObject", value)


def require_str(obj: JsonObject, key: str, context: str) -> str:
    """Return a required string field, or raise a descriptive error.

    Args:
        obj: The parent JSON object.
        key: The field name to read.
        context: A short label for the parent used in error messages.

    Returns:
        The string value of ``obj[key]``.

    Raises:
        SchemaSerializationError: If the field is absent or not a string.
    """
    if key not in obj:
        raise SchemaSerializationError(f"{context} is missing required field '{key}'")
    value = obj[key]
    if not isinstance(value, str):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be a string, got {type(value).__name__}"
        )
    return value


def optional_str(obj: JsonObject, key: str, context: str, *, default: str) -> str:
    """Return an optional string field, or ``default`` when absent.

    Args:
        obj: The parent JSON object.
        key: The field name to read.
        context: A short label for the parent used in error messages.
        default: The value returned when the field is absent.

    Returns:
        The string value of ``obj[key]``, or ``default``.

    Raises:
        SchemaSerializationError: If the field is present but not a string.
    """
    if key not in obj:
        return default
    value = obj[key]
    if not isinstance(value, str):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be a string, got {type(value).__name__}"
        )
    return value


def optional_nullable_str(obj: JsonObject, key: str, context: str) -> str | None:
    """Return an optional string field that may be JSON ``null``.

    Args:
        obj: The parent JSON object.
        key: The field name to read.
        context: A short label for the parent used in error messages.

    Returns:
        The string value, or ``None`` when the field is absent or JSON ``null``.

    Raises:
        SchemaSerializationError: If the field is present, non-null, and not a
            string.
    """
    if key not in obj:
        return None
    value = obj[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be a string or null, "
            f"got {type(value).__name__}"
        )
    return value


def optional_bool(obj: JsonObject, key: str, context: str, *, default: bool) -> bool:
    """Return an optional boolean field, or ``default`` when absent.

    Args:
        obj: The parent JSON object.
        key: The field name to read.
        context: A short label for the parent used in error messages.
        default: The value returned when the field is absent.

    Returns:
        The boolean value of ``obj[key]``, or ``default``.

    Raises:
        SchemaSerializationError: If the field is present but not a boolean.
    """
    if key not in obj:
        return default
    value = obj[key]
    # bool is a subclass of int; check bool explicitly so an int is not accepted.
    if not isinstance(value, bool):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be a boolean, got {type(value).__name__}"
        )
    return value


def optional_int(obj: JsonObject, key: str, context: str, *, default: int) -> int:
    """Return an optional integer field, or ``default`` when absent.

    Args:
        obj: The parent JSON object.
        key: The field name to read.
        context: A short label for the parent used in error messages.
        default: The value returned when the field is absent.

    Returns:
        The integer value of ``obj[key]``, or ``default``.

    Raises:
        SchemaSerializationError: If the field is present but not an integer (a
            boolean is explicitly rejected even though it subclasses ``int``).
    """
    if key not in obj:
        return default
    value = obj[key]
    # Reject bool explicitly even though it is an int subclass; header_row is not
    # a boolean and accepting True/False would mask a malformed schema.
    if isinstance(value, bool) or not isinstance(value, int):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be an integer, got {type(value).__name__}"
        )
    return value


def optional_str_tuple(obj: JsonObject, key: str, context: str) -> tuple[str, ...]:
    """Return an optional list-of-strings field as a tuple (empty when absent).

    Args:
        obj: The parent JSON object.
        key: The field name to read.
        context: A short label for the parent used in error messages.

    Returns:
        A tuple of the string elements, empty when the field is absent.

    Raises:
        SchemaSerializationError: If the field is present but not a list, or any
            element is not a string.
    """
    if key not in obj:
        return ()
    value = obj[key]
    if not isinstance(value, list):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be a list of strings, "
            f"got {type(value).__name__}"
        )
    # Validate each element is a string so a malformed entry fails fast and names
    # its container field rather than surfacing later as a dataclass error.
    items: list[str] = []
    for element in cast("list[JsonValue]", value):
        if not isinstance(element, str):
            raise SchemaSerializationError(
                f"{context} field '{key}' must contain only strings, "
                f"got a {type(element).__name__} element"
            )
        items.append(element)
    return tuple(items)


def optional_object_list(obj: JsonObject, key: str, context: str) -> list[JsonObject]:
    """Return an optional list-of-objects field (empty when absent).

    Args:
        obj: The parent JSON object.
        key: The field name holding the list.
        context: A short label for the parent used in error messages.

    Returns:
        A list of typed ``JsonObject`` elements, empty when the field is absent.

    Raises:
        SchemaSerializationError: If the field is present but is not a list, or
            any element is not a JSON object.
    """
    if key not in obj:
        return []
    value = obj[key]
    if not isinstance(value, list):
        raise SchemaSerializationError(
            f"{context} field '{key}' must be a list, got {type(value).__name__}"
        )
    # Narrow each element to a typed object so the per-shape parsers stay typed.
    return [
        require_object(element, f"{context}.{key} element")
        for element in cast("list[JsonValue]", value)
    ]
