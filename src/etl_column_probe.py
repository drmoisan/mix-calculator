"""Non-raising column probe for schema matching and discovery.

This module provides a tolerant, non-raising counterpart to
:func:`src.etl_columns.resolve_columns`. Where the resolver binds every required
column and raises :class:`ValueError` on the first unmatched required column,
``probe_columns`` performs the same position + fuzzy resolution but returns a
partial :class:`ProbeResult` instead of raising. Schema matching needs to inspect
how completely a candidate schema's expected columns map onto an arbitrary set of
actual headers, including the columns that did not match, so it requires the
partial result rather than a hard failure.

The probe reuses only the PUBLIC resolver helpers ``normalize_name`` and
``DEFAULT_THRESHOLD`` from :mod:`src.etl_columns` and reimplements the
fuzzy-selection step locally (``_best_fuzzy_index``) so the matching behavior —
position pass, then normalized-equality, then ``difflib`` ratio above the
threshold — stays identical to the production resolver. The fuzzy helper is
reimplemented here rather than imported because the resolver's helper is a
private ``_``-prefixed symbol: importing it across module boundaries fails
``pyright`` strict mode under ``reportPrivateUsage``, the resolver file is
protected (AC1 requires it byte-for-byte unchanged) so no public alias may be
added there, and no ``reportPrivateUsage`` suppression is pre-authorized. The
local helper reproduces the resolver's exact selection logic so the
:func:`probe_columns` bindings equal those of
:func:`src.etl_columns.resolve_columns` on a resolvable input (verified by the
parity test). This module is additive: it does not modify
:mod:`src.etl_columns`, and ``resolve_columns`` retains its raising contract
unchanged.

Scope boundaries:
    - Pure logic only. No I/O, no logging, no wall-clock, no randomness.
    - Depends only on the standard library and the public resolver helpers.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.etl_columns import DEFAULT_THRESHOLD, normalize_name

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class ProbeResult:
    """The partial outcome of probing actual headers against expected columns.

    Purpose:
        Capture how completely a set of expected (canonical) columns resolves
        against a set of actual headers, without raising when some expected
        columns cannot be bound. Schema matching reads these fields to score a
        candidate schema and to explain why headers did not match.

    Responsibilities:
        - Report each expected column that bound, and to which actual header.
        - Report the expected columns that did not bind.
        - Report the actual headers that no expected column claimed.

    Usage:
        Returned by :func:`probe_columns`. Treated as an immutable value object;
        callers do not mutate it. Construct it only through ``probe_columns``.

    Attributes:
        matched: Mapping from each matched expected canonical label to the actual
            header that resolved to it. Mirrors the ``mapping`` returned by
            :func:`src.etl_columns.resolve_columns` for the bound subset.
        unmatched_expected: Expected canonical labels that could not be bound to
            any actual header, in expected (canonical) order.
        unmatched_actual: Actual headers that no expected column claimed, in
            source order (the "extra"/unrecognized columns).
    """

    matched: dict[str, str]
    unmatched_expected: list[str]
    unmatched_actual: list[str]


def _best_fuzzy_index(
    expected_norm: str,
    actual_norms: list[str],
    available: list[int],
    threshold: float,
) -> int | None:
    """Pick the best remaining actual-column index for one expected column.

    Reproduces the exact selection logic of the resolver's private helper
    :func:`src.etl_columns._best_fuzzy_index` so the probe's fuzzy pass binds the
    identical actual header the resolver would. The helper is reimplemented here
    rather than imported because importing the resolver's private symbol fails
    ``pyright`` strict mode (``reportPrivateUsage``) and the resolver file is
    protected from edits (AC1).

    Selection proceeds in two stages: an exact normalized-equality match among
    the available indices is preferred and returned immediately; otherwise the
    available index with the highest ``difflib.SequenceMatcher`` ratio that meets
    ``threshold`` is returned, using a strict greater-than comparison so ties
    resolve to the earliest candidate.

    Args:
        expected_norm: The normalized expected column name.
        actual_norms: Normalized actual names, index-aligned to the source.
        available: Indices of actual columns still unbound.
        threshold: Minimum similarity ratio required to bind via fuzzy match.

    Returns:
        The chosen actual-column index, or ``None`` when nothing qualifies.
    """
    # Normalized-equality first: an exact normalized hit is unambiguous and is
    # preferred over any approximate ratio, matching the resolver's ordering.
    for index in available:
        if actual_norms[index] == expected_norm:
            return index

    # Otherwise score every remaining candidate and keep the best that clears the
    # threshold; the strict ">" comparison leaves ties bound to the earliest
    # candidate, exactly as the resolver does.
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


def probe_columns(
    actual: Sequence[str],
    expected: Sequence[str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> ProbeResult:
    """Probe actual headers against expected columns without raising.

    Performs the same two-pass resolution as
    :func:`src.etl_columns.resolve_columns` — a position pass that binds an
    expected column when the actual header at the same index normalizes equally,
    then a fuzzy pass that binds each remaining expected column to the best
    unclaimed actual header by normalized equality and then by
    ``difflib.SequenceMatcher`` ratio meeting ``threshold`` — but returns the
    partial result instead of raising on an unmatched required column.

    This function is pure: it performs no I/O and never raises on a mismatch. A
    fully unresolvable input simply yields empty ``matched`` with every expected
    label in ``unmatched_expected`` and every actual header in
    ``unmatched_actual``.

    Args:
        actual: The actual header labels read from a source, in source order.
        expected: The expected (canonical) column labels, in canonical order.
        threshold: Minimum normalized similarity ratio for the fuzzy pass
            (default :data:`src.etl_columns.DEFAULT_THRESHOLD`).

    Returns:
        A :class:`ProbeResult` whose ``matched`` maps each bound expected label
        to its actual header, ``unmatched_expected`` lists the expected labels
        that did not bind (in canonical order), and ``unmatched_actual`` lists
        the actual headers no expected column claimed (in source order).
    """
    actual_list = list(actual)
    actual_norms = [normalize_name(name) for name in actual_list]

    mapping: dict[str, str] = {}
    bound_indices: set[int] = set()

    # Position pass: bind each expected column whose normalized name matches the
    # actual header sitting at the same index, mirroring the resolver. An
    # expected index beyond the actual headers cannot match here and is deferred
    # to the fuzzy pass.
    for index, expected_name in enumerate(expected):
        if index >= len(actual_list):
            continue
        if actual_norms[index] == normalize_name(expected_name):
            mapping[expected_name] = actual_list[index]
            bound_indices.add(index)

    # Fuzzy pass: resolve every still-unbound expected column against the best
    # remaining actual header. Unlike the resolver, an expected column that finds
    # no candidate is collected into unmatched_expected rather than triggering a
    # raise, so the probe always returns a partial result.
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

    # Unmatched actual headers are the source columns no expected column claimed,
    # kept in source order for a stable, readable report.
    unmatched_actual = [
        name for index, name in enumerate(actual_list) if index not in bound_indices
    ]

    return ProbeResult(
        matched=mapping,
        unmatched_expected=unmatched_expected,
        unmatched_actual=unmatched_actual,
    )
