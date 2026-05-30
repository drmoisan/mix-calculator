"""Coverage-scoring helpers split out of :mod:`src.schema_matching`.

This module holds the alias-aware required-column coverage helpers used by
:func:`src.schema_matching.find_best_match`. They were extracted into this
sibling so :mod:`src.schema_matching` stays under the repository's 500-line file
cap once the registry-integrated entry point was added (issue #42, plan P4-T1).

Scope boundaries:
    - Pure logic only. No I/O, no logging, no wall-clock, no randomness.
    - Depends only on the standard library and the public resolver helper
      :func:`src.etl_columns.normalize_name`.
"""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from src.etl_columns import normalize_name

if TYPE_CHECKING:
    from collections.abc import Sequence


def required_column_matches(
    canonical_name: str,
    aliases: tuple[str, ...],
    actual_norms: Sequence[str],
    threshold: float,
) -> bool:
    """Decide whether one required column resolves to any actual header.

    A required column matches when its canonical name or any declared alias
    resolves to an actual header: either by exact normalized equality, or by a
    ``difflib`` ratio meeting ``threshold`` on normalized names. Alias support is
    what lets a renamed source header still count toward coverage.

    Args:
        canonical_name: The required column's canonical name.
        aliases: The column's declared match aliases.
        actual_norms: Normalized actual headers.
        threshold: Minimum normalized similarity ratio to count as a match.

    Returns:
        ``True`` when any name-form of the column resolves to an actual header,
        otherwise ``False``.
    """
    # Try the canonical name and every alias; any one resolving is enough for the
    # column to count toward coverage. Normalize each form once.
    name_forms = [normalize_name(canonical_name)]
    name_forms.extend(normalize_name(alias) for alias in aliases)

    # A name-form matches on exact normalized equality or a sufficient ratio.
    for form in name_forms:
        for actual_norm in actual_norms:
            if actual_norm == form:
                return True
            if difflib.SequenceMatcher(None, form, actual_norm).ratio() >= threshold:
                return True
    return False


def coverage_score(
    actual_norms: Sequence[str],
    required: Sequence[tuple[str, tuple[str, ...]]],
    threshold: float,
) -> float:
    """Compute the fraction of required columns that resolve to a header.

    Args:
        actual_norms: Normalized actual headers.
        required: The schema's required columns as ``(canonical_name, aliases)``.
        threshold: Minimum normalized similarity ratio to count as a match.

    Returns:
        The coverage fraction in ``[0.0, 1.0]``. A schema with no required
        columns scores ``1.0`` (vacuously fully covered).
    """
    # A schema declaring no required columns is vacuously satisfied; treat it as
    # full coverage so it is not penalized against schemas that do declare some.
    if not required:
        return 1.0

    # Count the required columns that resolve to any actual header (canonical or
    # alias), then divide by the total to get the coverage fraction.
    matched = sum(
        1
        for canonical_name, aliases in required
        if required_column_matches(canonical_name, aliases, actual_norms, threshold)
    )
    return matched / len(required)
