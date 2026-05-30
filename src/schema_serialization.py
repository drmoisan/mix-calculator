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
from src.schema_model import (
    ColumnSpec,
    DedupPolicy,
    DerivedColumnSpec,
    FillRule,
    KeySpec,
    MeasureAggregation,
    SchemaDefinition,
)

# Declared key sets per object shape. These drive both serialization ordering and
# the unknown-key rejection in parsing so the two directions stay in lock-step.
_COLUMN_KEYS: tuple[str, ...] = (
    "canonical_name",
    "role",
    "required",
    "aliases",
    "numeric",
    "sentinel_clean",
)
_MEASURE_AGG_KEYS: tuple[str, ...] = ("measure", "mode", "select_values")
_DEDUP_KEYS: tuple[str, ...] = (
    "mode",
    "discriminator_column",
    "measure_aggregations",
)
_DERIVED_KEYS: tuple[str, ...] = ("name", "expression", "copy_from")
_KEY_KEYS: tuple[str, ...] = ("columns", "sku_coercion")
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
        "version": schema.version,
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
        "aliases": list(column.aliases),
        "numeric": column.numeric,
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


def _key_to_object(key: KeySpec) -> JsonObject:
    """Convert a ``KeySpec`` into a JSON-ready ordered object."""
    return {
        "columns": list(key.columns),
        "sku_coercion": key.sku_coercion,
    }


def _fill_rule_to_object(rule: FillRule) -> JsonObject:
    """Convert a ``FillRule`` into a JSON-ready ordered object."""
    return {
        "total": rule.total,
        "components": list(rule.components),
    }


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
    return SchemaDefinition(
        name=require_str(obj, "name", "schema"),
        version=require_str(obj, "version", "schema"),
        description=optional_str(obj, "description", "schema", default=""),
        source_sheet_hints=optional_str_tuple(obj, "source_sheet_hints", "schema"),
        header_row=optional_int(obj, "header_row", "schema", default=0),
        columns=tuple(
            _object_to_column(item)
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


def _object_to_column(obj: JsonObject) -> ColumnSpec:
    """Reconstruct a ``ColumnSpec`` from a typed JSON object."""
    reject_unknown_keys(obj, _COLUMN_KEYS, "column")
    return ColumnSpec(
        canonical_name=require_str(obj, "canonical_name", "column"),
        role=require_str(obj, "role", "column"),
        required=optional_bool(obj, "required", "column", default=True),
        aliases=optional_str_tuple(obj, "aliases", "column"),
        numeric=optional_bool(obj, "numeric", "column", default=False),
        sentinel_clean=optional_bool(obj, "sentinel_clean", "column", default=False),
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


def _object_to_key(parent: JsonObject) -> KeySpec:
    """Reconstruct the ``KeySpec`` from the parent schema object."""
    raw = parent.get("key")
    if raw is None:
        raise SchemaSerializationError("schema is missing required field 'key'")
    obj = require_object(raw, "key")
    reject_unknown_keys(obj, _KEY_KEYS, "key")
    return KeySpec(
        columns=optional_str_tuple(obj, "columns", "key"),
        sku_coercion=optional_bool(obj, "sku_coercion", "key", default=False),
    )


def _object_to_fill_rule(obj: JsonObject) -> FillRule:
    """Reconstruct a ``FillRule`` from a typed JSON object."""
    reject_unknown_keys(obj, _FILL_RULE_KEYS, "fill_rule")
    return FillRule(
        total=require_str(obj, "total", "fill_rule"),
        components=optional_str_tuple(obj, "components", "fill_rule"),
    )
