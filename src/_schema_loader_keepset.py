"""Flag-independent keep-set computation for the schema-driven loader.

Purpose:
    Compute which declared columns the loader must locate, resolve, and carry
    through, independent of the ``required`` flag. This logic is factored out of
    :mod:`src._schema_loader_helpers` so that module stays under the repository
    500-line file cap while keeping the keep-set rules in one cohesive place.

Responsibilities:
    - :func:`by_name_optional_columns`: the columns located by normalized name
      only (``KEY`` plus every ``located_by_name`` column), tolerated if absent.
    - :func:`referenced_columns`: the columns named by a key/dedup/fill/derived
      spec that must be carried through even when not emitted or required.
    - :func:`is_kept_non_located`: whether a non-located declared column belongs
      in the resolution keep-set (required, emitted, or referenced).

Key invariant:
    The keep-set and located-by-name selection key off ``located_by_name`` and
    ``in_output``/referenced needs, never off ``required``. Flipping a measure's
    ``required`` flag therefore cannot move it between the located set and the
    resolution set, so the emitted column order is independent of ``required``.

Side effects:
    None. Pure functions over a :class:`SchemaDefinition`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schema_model import ColumnSpec, SchemaDefinition


def by_name_optional_columns(schema: SchemaDefinition) -> list[str]:
    """Return canonical names resolved by name only, KEY first then optionals.

    These are ``KEY`` (always optional/by-name) followed by any declared column
    whose ``located_by_name`` flag is True, in schema order. The rule keys off
    ``located_by_name`` and is independent of ``required``: a column is located by
    name (no fuzzy, no raise on absence) only when it explicitly declares the
    located-by-name signal. This includes the AOP optional ``YTG`` and the LE
    ``KEY``/``YTD/YTG`` (once the bundled schemas set the flag). The order is
    deterministic (KEY first), matching the protected loaders'
    ``if key ... if ytg ...`` append sequence.

    Args:
        schema: The active schema.

    Returns:
        The ordered list of canonical names to locate by normalized name only.
    """
    by_name: list[str] = ["KEY"]
    # Located-by-name declared columns are found by name so an absent one (older
    # AOP sheets predate YTG) is neither required nor reported as extra. Keying off
    # located_by_name (not "not required") decouples location from the required
    # flag so flipping a measure to required=false does not make it located-by-name.
    for column in schema.columns:
        if column.located_by_name and column.canonical_name not in by_name:
            by_name.append(column.canonical_name)
    return by_name


def referenced_columns(schema: SchemaDefinition) -> set[str]:
    """Return canonical names referenced by key, dedup, fill, or derived specs.

    A referenced column must be carried through resolve/rename even when it is not
    itself emitted (``in_output=False``) or required, because a later phase reads
    it: the dedup discriminator and measure aggregations, the fill-rule totals and
    their components, and the derived columns' ``copy_from`` source all name source
    columns the loader needs present.

    Args:
        schema: The active schema.

    Returns:
        The set of canonical column names referenced by any processing spec.
    """
    referenced: set[str] = set()
    # The dedup discriminator and each aggregated measure are read during collapse.
    if schema.dedup.discriminator_column is not None:
        referenced.add(schema.dedup.discriminator_column)
    for aggregation in schema.dedup.measure_aggregations:
        referenced.add(aggregation.measure)
    # Fill rules read both the total column and every component summed into it.
    for rule in schema.fill_rules:
        referenced.add(rule.total)
        referenced.update(rule.components)
    # A copy_from derived column reads its source column verbatim.
    for derived in schema.derived_columns:
        if derived.copy_from is not None:
            referenced.add(derived.copy_from)
    return referenced


def is_kept_non_located(column: ColumnSpec, schema: SchemaDefinition) -> bool:
    """Return whether a non-located column belongs in the resolution keep-set.

    A declared column is kept (independent of its ``required`` flag) when it is
    required, emitted (``in_output``), or referenced by a key/dedup/fill/derived
    spec. Located-by-name columns are handled separately and must not be filtered
    here; callers exclude them before calling this helper.

    Args:
        column: The candidate declared column.
        schema: The active schema (used to compute referenced columns).

    Returns:
        True when the column should be resolved/kept by the non-located keep-set.
    """
    return (
        column.required
        or column.in_output
        or column.canonical_name in referenced_columns(schema)
    )
