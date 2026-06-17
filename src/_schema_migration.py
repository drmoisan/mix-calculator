"""Column-level JSON reconstruction and forward-migration logic.

Purpose:
    House the ``ColumnSpec`` reconstruction from typed JSON together with the
    forward migrations that upgrade pre-3.0 persisted schemas on load. This logic
    is factored out of :mod:`src.schema_serialization` so that module stays under
    the repository 500-line file cap while keeping the migration rules in one
    cohesive place.

Responsibilities:
    - Define the canonical column key set (:data:`COLUMN_KEYS`) that drives both
      unknown-key rejection on parse and emit ordering on write.
    - Reconstruct a :class:`ColumnSpec` from a typed JSON object, applying the
      ``expected_dtype`` backfill, the required-output recomputation, and the
      ``located_by_name`` seeding migrations.

Constraints:
    The key set declared here is the single source of truth for column key order;
    :mod:`src.schema_serialization` imports it for the emit side so the parse and
    write directions stay in lock-step.
"""

from __future__ import annotations

from src._schema_json_helpers import (
    JsonObject,
    optional_bool,
    optional_nullable_str,
    optional_str_tuple,
    reject_unknown_keys,
    require_str,
)
from src.schema_model import ColumnSpec, derive_expected_dtype

# Declared column key set. This is the single source of truth for column key
# order; serialization imports it for emit ordering so parse and write stay in
# lock-step on the accepted/emitted keys.
COLUMN_KEYS: tuple[str, ...] = (
    "canonical_name",
    "role",
    "required",
    "in_output",
    "located_by_name",
    "aliases",
    "numeric",
    "expected_dtype",
    "sentinel_clean",
)


def object_to_column(obj: JsonObject, *, migrate_required: bool) -> ColumnSpec:
    """Reconstruct a ``ColumnSpec`` from a typed JSON object.

    Applies the forward migration for the ``expected_dtype`` field: when the JSON
    omits ``expected_dtype`` (pre-bump column) but declares ``numeric: true``, the
    column is backfilled with ``expected_dtype="float"`` so legacy numeric columns
    carry an explicit dtype after migration.

    The ``in_output`` field is additive with a safe default of ``True``: JSON that
    predates the field (no ``in_output`` key) parses as ``in_output=True``, so the
    column's output-membership is unchanged unless the schema declares otherwise.

    Required-output migration (2.0 -> 3.0): when ``migrate_required`` is True (the
    source schema predates 3.0), the column's ``required`` flag is recomputed as
    ``required(3.0) = required(2.0) AND in_output(2.0)``. A column that was a
    source-presence requirement but is not emitted (``required=True,
    in_output=False``) is no longer a required-output column; ``in_output`` is
    left unchanged, so the emitted-output set is preserved. This generic mapping
    upgrades older persisted *user* schemas on load. It is NOT the source of the
    bundled file's flag values: the bundled ``default_le`` file is hand-authored
    directly at version 3.0 and authors the loader-produced ``Super Category``
    column (``copy_from: "PPG"``) as ``required: false`` by hand because it is
    emitted by the derived-column phase, not by source resolution. When
    ``migrate_required`` is False (a 3.0-or-later source) the parsed ``required``
    value passes through unchanged.

    Located-by-name seeding (2.0 -> 3.0): the ``located_by_name`` field carries the
    load-time "find-by-name, tolerate-absent" signal that the pre-3.0 loader
    inferred from ``not required``. For pre-3.0 sources that omit the key
    (``migrate_required`` True and no ``located_by_name`` in the JSON), the field
    is seeded as ``located_by_name = not required(2.0)`` so the old located-by-name
    set (the columns that were ``required=False`` under the old loader, such as
    ``KEY`` and the AOP ``YTG``) is reproduced. An explicit key in the source (any
    version) passes through unchanged; 3.0-or-later sources default to ``False``.

    Args:
        obj: The typed JSON object for one column.
        migrate_required: Whether to apply the required-output recomputation
            because the source schema version predates 3.0.

    Returns:
        The reconstructed ``ColumnSpec`` with migrated fields applied.
    """
    reject_unknown_keys(obj, COLUMN_KEYS, "column")
    numeric = optional_bool(obj, "numeric", "column", default=False)
    explicit_dtype = optional_nullable_str(obj, "expected_dtype", "column")
    # Backfill the expected dtype from the legacy numeric flag when the JSON did
    # not declare an explicit dtype; this upgrades pre-bump columns in place.
    migrated_dtype = derive_expected_dtype(
        numeric=numeric, expected_dtype=explicit_dtype
    )
    parsed_required = optional_bool(obj, "required", "column", default=True)
    # in_output is additive: absent in older JSON means the column is in the
    # output (default True), so legacy schemas keep their full output set.
    in_output = optional_bool(obj, "in_output", "column", default=True)
    # Apply the required-output mapping only for pre-3.0 sources: a 2.0 column
    # keeps required only when it was also emitted, so non-emitted source-presence
    # requirements stop being required-output columns while output is unchanged.
    migrated_required = (
        parsed_required and in_output if migrate_required else parsed_required
    )
    # Seed located_by_name for pre-3.0 sources that omit the key: the old loader
    # treated required=False columns as located-by-name, so reproduce that set from
    # the source's own (pre-migration) required flag. An explicit key always wins.
    parsed_located = optional_bool(obj, "located_by_name", "column", default=False)
    located_by_name = (
        not parsed_required
        if migrate_required and "located_by_name" not in obj
        else parsed_located
    )
    return ColumnSpec(
        canonical_name=require_str(obj, "canonical_name", "column"),
        role=require_str(obj, "role", "column"),
        required=migrated_required,
        in_output=in_output,
        located_by_name=located_by_name,
        aliases=optional_str_tuple(obj, "aliases", "column"),
        numeric=numeric,
        expected_dtype=migrated_dtype,
        sentinel_clean=optional_bool(obj, "sentinel_clean", "column", default=False),
    )
