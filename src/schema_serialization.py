"""Typed JSON serialization adapter for :class:`SchemaDefinition`.

This module provides a lossless, deterministic JSON round-trip for the schema
model defined in :mod:`src.schema_model`, isolating the untyped ``json`` boundary
behind a small typed adapter in the same spirit as :mod:`src.pandas_io`. The
public functions never leak an untyped ``dict[str, Any]`` into callers:
``schema_to_json`` walks the frozen dataclass tree explicitly into JSON-ready
primitives, and ``schema_from_json`` validates the parsed structure key-by-key
before reconstructing the dataclasses.

Responsibilities:
    - ``schema_to_json``: serialize a ``SchemaDefinition`` to deterministic,
      key-ordered JSON text.
    - ``schema_from_json``: parse JSON text back into a ``SchemaDefinition``,
      raising :class:`SchemaSerializationError` for malformed JSON, missing
      required fields, or unknown/extra keys (naming the offending key), and
      allowing :class:`SchemaValidationError` from the model's ``__post_init__``
      to propagate unchanged.

Scope boundaries:
    - Pure, side-effect-free string transforms. No file or network I/O; the
      registry (:mod:`src.schema_registry`) owns persistence.
    - Standard library only (``json``, ``typing``).

Determinism:
    - ``schema_to_json`` emits object keys in a fixed declaration order and uses
      ``json.dumps`` with stable separators and ``sort_keys=False`` so that the
      same schema always serializes to the same text.
"""

from __future__ import annotations

import json
from typing import Any

from src._schema_json_helpers import (
    JsonObject,
    SchemaSerializationError,
    optional_bool,
    optional_int,
    optional_nullable_str,
    optional_object_list,
    optional_str,
    optional_str_tuple,
    reject_unknown_keys,
    require_object,
    require_str,
)
from src._schema_migration import object_to_column as _object_to_column
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
)

# Declared key sets per object shape. These drive both serialization ordering and
# the unknown-key rejection in parsing so the two directions stay in lock-step.
# The column key set is owned by :mod:`src._schema_migration` (where
# ``object_to_column`` performs the parse-side rejection) so the parse-side
# migration and the emit-side ``_column_to_object`` order share one definition.
_MEASURE_AGG_KEYS: tuple[str, ...] = ("measure", "mode", "select_values")
_DEDUP_KEYS: tuple[str, ...] = (
    "mode",
    "discriminator_column",
    "measure_aggregations",
)
_DERIVED_KEYS: tuple[str, ...] = ("name", "expression", "copy_from")
# The current key shape uses structured "parts"; the legacy pre-bump shape used a
# flat "columns" list. Both are accepted on parse (the legacy shape triggers the
# forward migration) but only "parts" is emitted on write.
_KEY_KEYS: tuple[str, ...] = ("parts", "columns", "sku_coercion")
_KEY_PART_KEYS: tuple[str, ...] = ("kind", "value")
_FILL_RULE_KEYS: tuple[str, ...] = ("total", "components")
_SCHEMA_KEYS: tuple[str, ...] = (
    "name",
    "version",
    "description",
    "source_sheet_hints",
    "header_row",
    "columns",
    "key",
    "dedup",
    "derived_columns",
    "fill_rules",
    "drop_columns",
)

# Re-export the serialization error so existing callers and tests can import it
# from this module; the definition lives in the typed-helpers module.
__all__ = [
    "SchemaSerializationError",
    "schema_from_json",
    "schema_to_json",
]


def schema_to_json(schema: SchemaDefinition) -> str:
    """Serialize a schema to deterministic, key-ordered JSON text.

    Args:
        schema: The ``SchemaDefinition`` to serialize.

    Returns:
        A JSON string whose object keys appear in a fixed declaration order, so
        the same schema always produces identical text.

    Side effects:
        None. Pure string transform.
    """
    payload = _schema_to_object(schema)
    # Fixed separators and sort_keys=False (keys are already in declaration
    # order) give deterministic output independent of dict insertion quirks.
    return json.dumps(payload, separators=(",", ":"), sort_keys=False)


def schema_from_json(text: str) -> SchemaDefinition:
    """Parse JSON text into a ``SchemaDefinition``.

    Args:
        text: JSON text previously produced by ``schema_to_json`` (or an
            equivalent hand-authored schema file).

    Returns:
        The reconstructed ``SchemaDefinition``.

    Raises:
        SchemaSerializationError: If ``text`` is not valid JSON, is not a JSON
            object, is missing a required field, contains an unknown key, or has
            a value of the wrong JSON type.
        SchemaValidationError: Propagated from ``SchemaDefinition.__post_init__``
            when the structurally well-formed schema violates a model invariant.
    """
    # Contain the untyped json.loads boundary: parse into Any, then immediately
    # narrow to a typed JSON object before any field access occurs.
    try:
        parsed: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaSerializationError(f"schema JSON is malformed: {exc}") from exc
    root = require_object(parsed, "<root>")
    return _object_to_schema(root)


def _schema_to_object(schema: SchemaDefinition) -> JsonObject:
    """Convert a ``SchemaDefinition`` into a JSON-ready ordered object.

    Args:
        schema: The schema to convert.

    Returns:
        An ordered ``JsonObject`` with keys in ``_SCHEMA_KEYS`` order.
    """
    return {
        "name": schema.name,
        # Always emit the current write-format version so re-serialized schemas
        # carry SCHEMA_FORMAT_VERSION regardless of the in-memory version string.
        "version": SCHEMA_FORMAT_VERSION,
        "description": schema.description,
        "source_sheet_hints": list(schema.source_sheet_hints),
        "header_row": schema.header_row,
        "columns": [_column_to_object(column) for column in schema.columns],
        "key": _key_to_object(schema.key),
        "dedup": _dedup_to_object(schema.dedup),
        "derived_columns": [
            _derived_to_object(derived) for derived in schema.derived_columns
        ],
        "fill_rules": [_fill_rule_to_object(rule) for rule in schema.fill_rules],
        "drop_columns": list(schema.drop_columns),
    }


def _column_to_object(column: ColumnSpec) -> JsonObject:
    """Convert a ``ColumnSpec`` into a JSON-ready ordered object."""
    return {
        "canonical_name": column.canonical_name,
        "role": column.role,
        "required": column.required,
        "in_output": column.in_output,
        "located_by_name": column.located_by_name,
        "aliases": list(column.aliases),
        "numeric": column.numeric,
        "expected_dtype": column.expected_dtype,
        "sentinel_clean": column.sentinel_clean,
    }


def _measure_agg_to_object(aggregation: MeasureAggregation) -> JsonObject:
    """Convert a ``MeasureAggregation`` into a JSON-ready ordered object."""
    return {
        "measure": aggregation.measure,
        "mode": aggregation.mode,
        "select_values": list(aggregation.select_values),
    }


def _dedup_to_object(dedup: DedupPolicy) -> JsonObject:
    """Convert a ``DedupPolicy`` into a JSON-ready ordered object."""
    return {
        "mode": dedup.mode,
        "discriminator_column": dedup.discriminator_column,
        "measure_aggregations": [
            _measure_agg_to_object(aggregation)
            for aggregation in dedup.measure_aggregations
        ],
    }


def _derived_to_object(derived: DerivedColumnSpec) -> JsonObject:
    """Convert a ``DerivedColumnSpec`` into a JSON-ready ordered object."""
    return {
        "name": derived.name,
        "expression": derived.expression,
        "copy_from": derived.copy_from,
    }


def _key_part_to_object(part: KeyPart) -> JsonObject:
    """Convert a ``KeyPart`` into a JSON-ready ordered object."""
    return {
        "kind": part.kind,
        "value": part.value,
    }


def _key_to_object(key: KeySpec) -> JsonObject:
    """Convert a ``KeySpec`` into a JSON-ready ordered object.

    Emits the current structured ``parts`` shape (the legacy flat ``columns``
    shape is never written; it is only accepted on parse for forward migration).
    """
    return {
        "parts": [_key_part_to_object(part) for part in key.parts],
        "sku_coercion": key.sku_coercion,
    }


def _fill_rule_to_object(rule: FillRule) -> JsonObject:
    """Convert a ``FillRule`` into a JSON-ready ordered object."""
    return {
        "total": rule.total,
        "components": list(rule.components),
    }


def _version_predates_required_output(version: str) -> bool:
    """Return whether a source schema version predates the 3.0 required-output bump.

    Purpose:
        Decide whether the forward ``required`` migration must run for a parsed
        schema. The 3.0 format redefines ``required`` as "required OUTPUT column";
        any source schema written at a version below 3.0 carries the old
        source-presence meaning and must be recomputed on load.

    Args:
        version: The raw ``version`` string read from the source JSON (for
            example ``"1.0"``, ``"2.0"``, ``"3.0"``).

    Returns:
        ``True`` when the parsed major version is below 3 (the migration must
        run); ``False`` for a 3.0-or-later source (``required`` passes through
        unchanged). A version string that cannot be parsed as an integer major
        component is treated as pre-3.0 so legacy/hand-authored inputs are
        upgraded conservatively rather than silently skipped.
    """
    # Compare on the leading dotted component only; the format version uses a
    # "<major>.<minor>" shape and the required-output change is a major bump.
    major_text = version.split(".", 1)[0].strip()
    try:
        major = int(major_text)
    except ValueError:
        # An unparseable major component is treated as legacy so its required
        # flags are recomputed rather than trusted as already-3.0 values.
        return True
    return major < 3


def _object_to_schema(obj: JsonObject) -> SchemaDefinition:
    """Reconstruct a ``SchemaDefinition`` from a typed JSON object.

    Args:
        obj: The parsed root JSON object.

    Returns:
        The reconstructed ``SchemaDefinition``.

    Raises:
        SchemaSerializationError: On unknown keys, missing required fields, or
            wrong value types.
    """
    reject_unknown_keys(obj, _SCHEMA_KEYS, "schema")
    # The version field is required in the JSON, but the forward-only migration
    # sets the in-memory version to SCHEMA_FORMAT_VERSION so a re-serialize always
    # emits the current format. require_str enforces presence/type of the source
    # field before it is superseded.
    source_version = require_str(obj, "version", "schema")
    # Decide once whether the required-output migration applies to this source so
    # every column reconstruction uses the same gate.
    migrate_required = _version_predates_required_output(source_version)
    return SchemaDefinition(
        name=require_str(obj, "name", "schema"),
        version=SCHEMA_FORMAT_VERSION,
        description=optional_str(obj, "description", "schema", default=""),
        source_sheet_hints=optional_str_tuple(obj, "source_sheet_hints", "schema"),
        header_row=optional_int(obj, "header_row", "schema", default=0),
        columns=tuple(
            _object_to_column(item, migrate_required=migrate_required)
            for item in optional_object_list(obj, "columns", "schema")
        ),
        key=_object_to_key(obj),
        dedup=_object_to_dedup(obj),
        derived_columns=tuple(
            _object_to_derived(item)
            for item in optional_object_list(obj, "derived_columns", "schema")
        ),
        fill_rules=tuple(
            _object_to_fill_rule(item)
            for item in optional_object_list(obj, "fill_rules", "schema")
        ),
        drop_columns=optional_str_tuple(obj, "drop_columns", "schema"),
    )


def _object_to_measure_agg(obj: JsonObject) -> MeasureAggregation:
    """Reconstruct a ``MeasureAggregation`` from a typed JSON object."""
    reject_unknown_keys(obj, _MEASURE_AGG_KEYS, "measure_aggregation")
    return MeasureAggregation(
        measure=require_str(obj, "measure", "measure_aggregation"),
        mode=optional_str(obj, "mode", "measure_aggregation", default="additive"),
        select_values=optional_str_tuple(obj, "select_values", "measure_aggregation"),
    )


def _object_to_dedup(parent: JsonObject) -> DedupPolicy:
    """Reconstruct the ``DedupPolicy`` from the parent schema object."""
    raw = parent.get("dedup")
    # dedup is optional; an absent value yields the default no-collapse policy.
    if raw is None:
        return DedupPolicy()
    obj = require_object(raw, "dedup")
    reject_unknown_keys(obj, _DEDUP_KEYS, "dedup")
    return DedupPolicy(
        mode=optional_str(obj, "mode", "dedup", default="none"),
        discriminator_column=optional_nullable_str(
            obj, "discriminator_column", "dedup"
        ),
        measure_aggregations=tuple(
            _object_to_measure_agg(item)
            for item in optional_object_list(obj, "measure_aggregations", "dedup")
        ),
    )


def _object_to_derived(obj: JsonObject) -> DerivedColumnSpec:
    """Reconstruct a ``DerivedColumnSpec`` from a typed JSON object."""
    reject_unknown_keys(obj, _DERIVED_KEYS, "derived_column")
    return DerivedColumnSpec(
        name=require_str(obj, "name", "derived_column"),
        expression=optional_str(obj, "expression", "derived_column", default=""),
        copy_from=optional_nullable_str(obj, "copy_from", "derived_column"),
    )


def _object_to_key_part(obj: JsonObject) -> KeyPart:
    """Reconstruct a single ``KeyPart`` from a typed JSON object."""
    reject_unknown_keys(obj, _KEY_PART_KEYS, "key_part")
    return KeyPart(
        kind=require_str(obj, "kind", "key_part"),
        value=require_str(obj, "value", "key_part"),
    )


def _object_to_key(parent: JsonObject) -> KeySpec:
    """Reconstruct the ``KeySpec`` from the parent schema object.

    Accepts both the current structured ``parts`` shape and the legacy flat
    ``columns`` shape. A legacy ``columns`` list is migrated forward into an
    ordered tuple of ``column-ref`` parts, preserving order. When both shapes are
    absent the schema is malformed.

    Args:
        parent: The parent schema JSON object.

    Returns:
        The reconstructed ``KeySpec`` with structured parts.

    Raises:
        SchemaSerializationError: If the ``key`` field is absent, or neither a
            ``parts`` nor a ``columns`` entry is present.
    """
    raw = parent.get("key")
    if raw is None:
        raise SchemaSerializationError("schema is missing required field 'key'")
    obj = require_object(raw, "key")
    reject_unknown_keys(obj, _KEY_KEYS, "key")
    sku_coercion = optional_bool(obj, "sku_coercion", "key", default=False)
    # Prefer the current structured shape; fall back to the legacy flat columns
    # list and migrate it forward into column-ref parts in the same order.
    if "parts" in obj:
        parts = tuple(
            _object_to_key_part(item)
            for item in optional_object_list(obj, "parts", "key")
        )
        return KeySpec(parts=parts, sku_coercion=sku_coercion)
    if "columns" in obj:
        legacy_columns = optional_str_tuple(obj, "columns", "key")
        # Each legacy column name becomes an ordered column-ref part.
        migrated = tuple(
            KeyPart(kind="column-ref", value=name) for name in legacy_columns
        )
        return KeySpec(parts=migrated, sku_coercion=sku_coercion)
    raise SchemaSerializationError(
        "key object must contain 'parts' (current) or 'columns' (legacy)"
    )


def _object_to_fill_rule(obj: JsonObject) -> FillRule:
    """Reconstruct a ``FillRule`` from a typed JSON object."""
    reject_unknown_keys(obj, _FILL_RULE_KEYS, "fill_rule")
    return FillRule(
        total=require_str(obj, "total", "fill_rule"),
        components=optional_str_tuple(obj, "components", "fill_rule"),
    )
