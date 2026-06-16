"""Auto dedup mode for the schema loader (D-3, Option B).

This module holds the ``auto`` dedup code path extracted from
:mod:`src._schema_loader_helpers` so that file stays under the repository's
500-line cap. The ``auto`` mode derives the groupby key from the column roles
rather than an explicit discriminator: it groups by all ``dimension``-role
columns and sums all ``measure``-role columns. The existing
``collapse``/``aggregate``/``select_from`` path is untouched (D-3 preserves the
LE explicit dedup behavior).

Responsibilities:
    - ``apply_auto_dedup``: group a keyed frame by its dimension-role columns and
      sum its measure-role columns.

Scope boundaries:
    - Pure pandas transform driven by the schema's column roles. No I/O.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from src.schema_model import SchemaDefinition

__all__ = ["apply_auto_dedup"]


def apply_auto_dedup(frame: pd.DataFrame, schema: SchemaDefinition) -> pd.DataFrame:
    """Group by dimension-role columns and sum measure-role columns (D-3, auto).

    The ``auto`` dedup mode derives the groupby key from the column roles rather
    than an explicit discriminator: every ``dimension``-role column present in the
    frame forms the groupby key, and every ``measure``-role column present is summed
    per group. ``sort=False`` preserves first-appearance group order; the default
    ``min_count=0`` fills all-NaN sums as 0, matching the additive collapse path.
    The output index is reset to a default RangeIndex.

    Args:
        frame: The keyed working frame.
        schema: The active schema whose column roles drive the groupby and sum.

    Returns:
        A frame with one row per unique dimension combination, measure columns
        summed. When no dimension columns are present the frame is returned with a
        reset index (no grouping is possible).

    Raises:
        ValueError: If the schema declares no measure-role columns to sum, since an
            auto dedup with nothing to aggregate is a misconfiguration.
    """
    # Collect dimension and measure columns present in the frame, in schema order,
    # so the groupby key and the summed columns reflect the declared roles.
    dimensions = [
        c.canonical_name
        for c in schema.columns
        if c.role == "dimension" and c.canonical_name in frame.columns
    ]
    measures = [
        c.canonical_name
        for c in schema.columns
        if c.role == "measure" and c.canonical_name in frame.columns
    ]
    # Auto dedup with no measures has nothing to aggregate; fail fast rather than
    # silently dropping rows or returning an unexpected shape.
    if not measures:
        raise ValueError("auto dedup requires at least one measure column to sum")
    # Without any dimension columns there is no groupby key, so the rows cannot be
    # collapsed; return the frame with a fresh index to match the other branches.
    if not dimensions:
        return frame.reset_index(drop=True)
    grouped = frame.groupby(dimensions, sort=False)[measures].sum()
    return grouped.reset_index()
