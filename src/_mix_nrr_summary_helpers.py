"""Scalar and row helpers for the NRR-summary builder (issue #15).

This module factors the small pure helpers used by
:mod:`src.mix_nrr_summary` out of the block-assembly logic so each file stays
under the 500-line limit. It holds the zero-guarded scalar arithmetic
(``_safe_ratio``, ``all_in_ts``, ``ts_basis_points``, ``sum_optional``,
``reconciles``), the SUMIF/column-total readers (``column_sum``,
``attribute_totals``), the :class:`Measure` value object, and the tidy
long-table ``row`` factory. Every function is pure and performs no I/O.

All column names and labels here are schema, not secret; only the source data
values are confidential and never appear in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "BASIS_POINT_SCALE",
    "Measure",
    "all_in_ts",
    "attribute_totals",
    "column_sum",
    "reconciles",
    "row",
    "safe_ratio",
    "sum_optional",
    "ts_basis_points",
]

# Basis-point scaling applied to the All-in-TS% Abs delta on the source tab.
BASIS_POINT_SCALE: float = 10000.0


def safe_ratio(numerator: float, denominator: float) -> float | None:
    """Divide two scalars, guarding the zero-denominator path explicitly.

    The per-Lb ratios and the ``%`` / ``%NR`` derivations divide by a total
    (Lbs total, Gross-Sales total, or the AOP Net-Revenue total) that is
    non-zero for the real data but can be zero in fabricated/empty test inputs.
    Returning ``None`` rather than raising keeps the summary buildable on the
    zero path and lets the tidy table carry a ``None`` cell where the division
    is undefined.

    Args:
        numerator: The dividend.
        denominator: The divisor; a zero divisor yields ``None``.

    Returns:
        ``numerator / denominator`` as a ``float``, or ``None`` when the
        denominator is zero.
    """
    # Treat an exact-zero denominator as undefined; the real totals are never
    # exactly zero, so only the empty/fabricated zero path takes this branch.
    if denominator == 0:
        return None
    return numerator / denominator


def column_sum(frame: pd.DataFrame, column: str) -> float:
    """Return the plain column total of a frame as a built-in ``float``.

    Replicates the Excel ``[[#Totals]]`` references, which are plain column
    sums of the corresponding pandas table.

    Args:
        frame: The source frame.
        column: The column whose values are summed.

    Returns:
        The ``float`` sum of ``frame[column]``.
    """
    return float(frame[column].sum())


def attribute_totals(
    aop_vs_le: pd.DataFrame, attribute: str
) -> tuple[float, float, float]:
    """Compute the SUMIF-by-``Attribute`` AOP/LE/Diff totals for one attribute.

    Replicates the source tab's ``SUMIF(Attribute, label)`` over the
    ``aop_vs_le`` frame: the AOP/LE/Diff totals across every row whose
    ``Attribute`` equals ``attribute``.

    Args:
        aop_vs_le: The classified comparison frame carrying ``Attribute``,
            ``AOP``, ``LE``, and ``Diff`` columns.
        attribute: The attribute label to filter on (for example ``"Lbs"``).

    Returns:
        A ``(aop_total, le_total, diff_total)`` tuple of ``float`` sums.
    """
    selected = aop_vs_le[aop_vs_le["Attribute"] == attribute]
    return (
        float(selected["AOP"].sum()),
        float(selected["LE"].sum()),
        float(selected["Diff"].sum()),
    )


@dataclass(frozen=True)
class Measure:
    """A single AOP/LE measure total and its derived percent cell.

    Holds the SUMIF totals for one attribute (``Lbs``, ``Gross Sales``, or
    ``Net-Revenue $``) so the per-Lb ratios and the realization block can read
    the same numbers without recomputing the SUMIF.

    Attributes:
        aop: The AOP-scenario total.
        le: The LE-scenario total.
        diff: The ``LE - AOP`` change (the source tab's ``Abs`` column).
    """

    aop: float
    le: float
    diff: float

    @property
    def pct(self) -> float | None:
        """Return the ``Abs / AOP`` percent, guarding a zero AOP total."""
        return safe_ratio(self.diff, self.aop)


def row(
    section: str,
    metric: str,
    *,
    aop: float | None = None,
    le: float | None = None,
    value: float | None = None,
    pct: float | None = None,
    check: str | None = None,
) -> dict[str, object]:
    """Build one tidy long-table row as a column-keyed dict.

    Centralizes the row shape so every block emits rows with the same keys and
    so unset cells default to ``None`` (the source tab leaves them blank).

    Args:
        section: The block name.
        metric: The exact row label from the source tab.
        aop: The column-C value, or ``None`` where the row defines none.
        le: The column-D value, or ``None``.
        value: The column-E value (``Abs`` or ``NR $``), or ``None``.
        pct: The column-F value (``%`` or ``%NR``), or ``None``.
        check: The reconciliation result string, or ``None`` for non-Check rows.

    Returns:
        A dict keyed by the seven output columns.
    """
    return {
        "section": section,
        "metric": metric,
        "aop": aop,
        "le": le,
        "value": value,
        "pct": pct,
        "check": check,
    }


def all_in_ts(net_rev: float, gross_sales: float) -> float | None:
    """Compute ``1 - NetRev/GrossSales`` for one scenario, guarding zero GS.

    Args:
        net_rev: The scenario Net-Revenue total.
        gross_sales: The scenario Gross-Sales total (the denominator).

    Returns:
        ``1 - net_rev / gross_sales`` as a ``float``, or ``None`` when the
        Gross-Sales total is zero.
    """
    ratio = safe_ratio(net_rev, gross_sales)
    if ratio is None:
        return None
    return 1 - ratio


def ts_basis_points(ts_aop: float | None, ts_le: float | None) -> float | None:
    """Scale the ``All in TS%`` Abs delta to basis points.

    Args:
        ts_aop: The AOP-scenario TS% (or ``None`` on the zero path).
        ts_le: The LE-scenario TS% (or ``None`` on the zero path).

    Returns:
        ``(ts_le - ts_aop) * 10000`` as a ``float``, or ``None`` when either
        scenario TS% is undefined.
    """
    # The Abs delta is only defined when both scenario TS% values are defined.
    if ts_aop is None or ts_le is None:
        return None
    return (ts_le - ts_aop) * BASIS_POINT_SCALE


def sum_optional(left: float | None, right: float | None) -> float | None:
    """Add two optional scalars, returning ``None`` when either is ``None``.

    Args:
        left: The first addend, or ``None``.
        right: The second addend, or ``None``.

    Returns:
        ``left + right`` when both are defined; otherwise ``None``.
    """
    if left is None or right is None:
        return None
    return left + right


def reconciles(realization: float | None, buildup: float | None) -> bool:
    """Return whether a realization figure reconciles to its build-up.

    Reconciliation means ``round(realization - buildup, 0) == 0`` (a rounded
    zero difference), matching the source tab's CHECK criterion. When either
    operand is ``None`` (the zero/empty path), the comparison cannot reconcile.

    Args:
        realization: The realization-derived figure, or ``None``.
        buildup: The build-up figure, or ``None``.

    Returns:
        ``True`` when both figures are defined and reconcile to a rounded zero
        difference; ``False`` otherwise.
    """
    # A missing operand cannot satisfy the tie-out, so an undefined comparison
    # is treated as a non-reconciling (ERROR) outcome.
    if realization is None or buildup is None:
        return False
    return round(realization - buildup, 0) == 0
