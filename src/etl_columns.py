"""Position-independent column resolution for the ETL read boundary.

ETL source workbooks are authored by hand, so their columns may be reordered or
carry minor typographic variants relative to the documented schema. This module
resolves a set of actual column labels to a set of expected (canonical) labels
without requiring exact positions, so the downstream transform can always work
against canonical names. It is consumed by both the LE and AOP loaders.

Resolution proceeds in two passes:

    - Position pass: for each expected column at index ``i``, bind it when the
      actual column at the same index normalizes to the same value.
    - Fuzzy pass: for each still-unbound expected column, prefer a remaining
      unbound actual column whose normalized name is exactly equal, then fall
      back to the best ``difflib.SequenceMatcher`` ratio on normalized names
      that meets the similarity threshold.

The module is intentionally self-contained: it depends only on ``re``,
``difflib``, and typing so it can be imported by the ETL loaders without
creating an import cycle. It contains no I/O and no logging; the caller is
responsible for emitting any warning about extra columns.
"""

from __future__ import annotations

import difflib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# Default similarity threshold for the fuzzy pass. A typo/variant must score at
# or above this on normalized names to bind; the position and normalized-equality
# passes run first so well-formed inputs never reach the similarity step.
DEFAULT_THRESHOLD: float = 0.85

# Characters retained when normalizing a column name. Everything outside lower
# case ASCII letters and digits is stripped so spacing, casing, and punctuation
# differences (for example "SKU #" vs "sku") do not block a match.
_NON_ALNUM = re.compile(r"[^a-z0-9]")


def normalize_name(name: str) -> str:
    """Normalize a column label for tolerant comparison.

    Case-folds the label and removes all non-alphanumeric characters so that
    differences in casing, whitespace, and punctuation do not prevent a match
    (for example ``"SKU #"`` and ``"sku"`` both normalize to ``"sku"``).

    Args:
        name: The raw column label.

    Returns:
        The lower-cased label with every character outside ``[a-z0-9]`` removed.
    """
    return _NON_ALNUM.sub("", name.lower())


def _position_pass(
    actual: Sequence[str],
    expected: Sequence[str],
    actual_norms: list[str],
) -> tuple[dict[str, str], set[int]]:
    """Bind expected columns whose normalized name matches at the same index.

    Args:
        actual: The actual column labels, in source order.
        expected: The expected (canonical) column labels, in canonical order.
        actual_norms: Precomputed normalized forms of ``actual``, index-aligned.

    Returns:
        A tuple of (mapping, bound_indices) where ``mapping`` maps each matched
        expected label to its actual label and ``bound_indices`` is the set of
        actual-column indices already consumed.
    """
    mapping: dict[str, str] = {}
    bound_indices: set[int] = set()

    # Walk expected columns positionally; an expected index beyond the actual
    # columns simply cannot match here and is left for the fuzzy pass.
    for index, expected_name in enumerate(expected):
        if index >= len(actual):
            continue
        if actual_norms[index] == normalize_name(expected_name):
            mapping[expected_name] = actual[index]
            bound_indices.add(index)

    return mapping, bound_indices


def _best_fuzzy_index(
    expected_norm: str,
    actual_norms: list[str],
    available: list[int],
    threshold: float,
) -> int | None:
    """Pick the best remaining actual-column index for one expected column.

    Prefers an exact normalized-equality match among the available indices; if
    none exists, returns the available index with the highest
    ``SequenceMatcher`` ratio that meets ``threshold``.

    Args:
        expected_norm: The normalized expected column name.
        actual_norms: Normalized actual names, index-aligned to the source.
        available: Indices of actual columns still unbound.
        threshold: Minimum similarity ratio required to bind via fuzzy match.

    Returns:
        The chosen actual-column index, or ``None`` when nothing qualifies.
    """
    # Normalized-equality first: an exact normalized hit is unambiguous and is
    # preferred over any approximate ratio.
    for index in available:
        if actual_norms[index] == expected_norm:
            return index

    # Otherwise score every remaining candidate and keep the best that clears
    # the threshold; ties resolve to the earliest candidate (strict ">").
    best_index: int | None = None
    best_ratio = 0.0
    for index in available:
        ratio = difflib.SequenceMatcher(
            None, expected_norm, actual_norms[index]
        ).ratio()
        if ratio >= threshold and ratio > best_ratio:
            best_index = index
            best_ratio = ratio
    return best_index


def resolve_columns(
    actual: Sequence[str],
    expected: Sequence[str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> tuple[dict[str, str], list[str]]:
    """Resolve actual columns to expected columns, position then fuzzy.

    Binds every required expected column to an actual column. The position pass
    binds expected columns whose normalized name matches the actual column at
    the same index; the fuzzy pass binds each remaining expected column to the
    best unbound actual column by normalized equality, then by
    ``difflib.SequenceMatcher`` ratio meeting ``threshold``.

    This function is pure: it raises on an unmatched required column and returns
    the list of extra (unmatched) actual columns, but it does not log. The
    caller is responsible for emitting any warning about extras.

    Args:
        actual: The actual column labels read from the source, in source order.
        expected: The required expected (canonical) column labels.
        threshold: Minimum normalized similarity ratio for the fuzzy pass
            (default :data:`DEFAULT_THRESHOLD`). Must be in ``(0, 1]``.

    Returns:
        A tuple ``(mapping, extras)``. ``mapping`` maps each expected canonical
        label to the actual label that resolved to it. ``extras`` lists the
        actual labels that were not bound to any expected column, in source
        order.

    Raises:
        ValueError: When any required expected column cannot be bound after the
            position and fuzzy passes. The message names the unmatched expected
            column(s).
    """
    actual_list = list(actual)
    actual_norms = [normalize_name(name) for name in actual_list]

    # Position pass binds the well-formed, in-order columns up front.
    mapping, bound_indices = _position_pass(actual_list, expected, actual_norms)

    # Fuzzy pass resolves whatever the position pass left unbound. Each expected
    # column claims the best remaining actual column, so already-claimed indices
    # are removed from the candidate pool as we go.
    unmatched_expected: list[str] = []
    for expected_name in expected:
        if expected_name in mapping:
            continue
        available = [i for i in range(len(actual_list)) if i not in bound_indices]
        chosen = _best_fuzzy_index(
            normalize_name(expected_name), actual_norms, available, threshold
        )
        if chosen is None:
            unmatched_expected.append(expected_name)
        else:
            mapping[expected_name] = actual_list[chosen]
            bound_indices.add(chosen)

    # A required column that never bound is a hard schema failure; name them all
    # so the operator can correct the source in one pass.
    if unmatched_expected:
        raise ValueError(
            "Source schema mismatch: could not resolve required column(s): "
            f"{unmatched_expected}. Actual columns: {actual_list}."
        )

    # Extras are actual columns that no expected column claimed, kept in source
    # order for a stable, readable warning message.
    extras = [
        name for index, name in enumerate(actual_list) if index not in bound_indices
    ]
    return mapping, extras
