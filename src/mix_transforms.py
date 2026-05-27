"""Pure transform primitives for the LE-versus-AOP gross-to-net decomposition.

This module exposes the side-effect-free pandas primitives that reproduce the
Power Query helper functions used by the mix/rate decomposition model, plus the
two long-to-wide source-shaping pivots. Every function takes and returns a
``pandas.DataFrame`` (or a ``pandas.Series``); none performs I/O, logging, or any
mutation visible outside the returned frame. The SQLite/Excel boundaries live in
:mod:`src.pandas_io` and the orchestration in :mod:`src.mix_pipeline`.

The lower-level primitives (``negate_column``, ``calc_ratios``,
``classify_table``, ``stack_pivot``, ``add_ratios``, ``fill_zero_with_avg``) live
in :mod:`src._mix_transforms_helpers` so this file stays under the 500-line
limit; they are re-exported here so callers and tests can import them from
``src.mix_transforms``. The pivots ``pivot_le`` and ``pivot_aop`` are defined
here because they compose those primitives.

The ratio column names, the classification labels, and the measure column names
are schema, not secret; only the source data values are confidential and never
appear here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src._mix_transforms_helpers import (
    NEGATED_COLUMNS,
    RATIO_SPECS,
    add_ratios,
    calc_ratios,
    classify_table,
    fill_zero_with_avg,
    negate_column,
    stack_pivot,
)

if TYPE_CHECKING:
    import pandas as pd

# Re-export the lower-level primitives so callers and tests can import them from
# this module as well as from ``src._mix_transforms_helpers``. The primitives
# live in the helper module so this file stays under the 500-line limit.
__all__ = [
    "RATIO_SPECS",
    "YTG_MONTHS",
    "add_ratios",
    "calc_ratios",
    "classify_table",
    "fill_zero_with_avg",
    "negate_column",
    "pivot_aop",
    "pivot_le",
    "stack_pivot",
]

# Months contributing to the year-to-go measure under the 8+4 convention
# (May..Dec). Used by ``pivot_aop`` when the source ``aop`` table predates the
# explicit ``YTG`` column and the measure must be derived.
YTG_MONTHS: list[str] = [
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# Index columns shared by the LE/AOP long-to-wide pivots before the measure
# columns are added. AOP additionally carries "Customer Master".
_LE_INDEX: list[str] = [
    "Customer",
    "Super Category",
    "PPG",
    "SKU Descripiton",
    "SKU #",
]
_AOP_INDEX: list[str] = ["Customer Master", *_LE_INDEX]

# Rename applied after the LE pivot so the deduction columns carry their "$"
# names before negation and net-revenue derivation.
_LE_RENAMES: dict[str, str] = {
    "Off Invoice": "Off Invoice $",
    "Non-Trade": "Non-Trade $",
    "Trade": "Trade Spend $",
}

# AOP percent line-item types dropped before the wide frame is shaped.
_AOP_DROP_TYPES: list[str] = ["Trade Spend %", "Non-Trade %", "Off Invoice %"]


def _finish_wide(wide: pd.DataFrame, index_cols: list[str]) -> pd.DataFrame:
    """Negate deductions, add net revenue and ratios, then melt to long form.

    Shared tail of ``pivot_le`` and ``pivot_aop``: it negates the three deduction
    columns, derives ``Net-Revenue $`` as their sum with ``Gross Sales``, appends
    the eight ratio columns, and melts the wide frame back to long
    ``Attribute``/``Value`` form keyed by ``index_cols``.

    Args:
        wide: The pivoted wide frame with measure columns present and filled.
        index_cols: The identity columns retained as melt ``id_vars``.

    Returns:
        A long-format DataFrame with ``index_cols`` plus ``Attribute`` and
        ``Value`` columns.
    """
    # Negate the deductions so the net-revenue sum can add them to Gross Sales.
    for column in NEGATED_COLUMNS:
        wide = negate_column(wide, column)

    # Net revenue is gross plus the (now-negative) deductions.
    wide["Net-Revenue $"] = (
        wide["Gross Sales"]
        + wide["Off Invoice $"]
        + wide["Trade Spend $"]
        + wide["Non-Trade $"]
    )
    wide = calc_ratios(wide)

    # Melt every non-index column into the long Attribute/Value pair shape.
    melted = wide.melt(id_vars=index_cols, var_name="Attribute", value_name="Value")
    return melted


def pivot_le(le_raw: pd.DataFrame) -> pd.DataFrame:
    """Pivot the raw long ``LE`` table to wide, add measures, melt back to long.

    Reproduces the Power Query ``LE`` query (research §4.1): group by the LE index
    columns plus ``GtN Mapping`` summing ``YTG``, pivot ``GtN Mapping`` on
    ``YTG``, fill missing with 0, rename the deduction labels to their ``$``
    names, then negate, add net revenue, apply ratios, and melt back to long
    Attribute/Value form.

    Args:
        le_raw: The raw long ``LE`` frame with ``Customer``, ``Super Category``,
            ``PPG``, ``SKU Descripiton``, ``SKU #``, ``GtN Mapping``, and ``YTG``.

    Returns:
        A long-format DataFrame with the LE index columns plus ``Attribute`` and
        ``Value``.
    """
    selected = le_raw[[*_LE_INDEX, "GtN Mapping", "YTG"]].copy()
    grouped = selected.groupby([*_LE_INDEX, "GtN Mapping"], as_index=False)["YTG"].sum()
    wide = grouped.pivot_table(
        index=_LE_INDEX,
        columns="GtN Mapping",
        values="YTG",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    wide = wide.fillna(0)

    # Rename the LE deduction labels to their "$" names; missing measure columns
    # are created as 0 so the downstream negation/sum always has them present.
    wide = wide.rename(columns=_LE_RENAMES)
    for column in ["Gross Sales", "Lbs", *NEGATED_COLUMNS]:
        if column not in wide.columns:
            wide[column] = 0.0
    return _finish_wide(wide, _LE_INDEX)


def pivot_aop(aop_raw: pd.DataFrame) -> pd.DataFrame:
    """Pivot the raw long ``aop`` table to wide, add measures, melt back to long.

    Reproduces the Power Query ``AOP`` query (research §4.2): pivot ``Type`` on
    ``YTG``, drop the percent line-item types, rename ``LBs`` -> ``Lbs``, then
    negate the deductions, add net revenue, apply ratios, and melt back to long.
    When the source ``aop`` table predates the ``YTG`` column, the measure is
    derived by summing ``May..Dec`` (the :data:`YTG_MONTHS` fallback) before the
    pivot, matching the LE loader's 8+4 derivation.

    Args:
        aop_raw: The raw long ``aop`` frame with the AOP index columns, ``Type``,
            and either ``YTG`` or the monthly ``May..Dec`` columns.

    Returns:
        A long-format DataFrame with the AOP index columns plus ``Attribute`` and
        ``Value``.
    """
    working = aop_raw.copy()

    # YTG fallback: older AOP sheets lack the YTG column, so derive it from the
    # May..Dec months exactly as the LE loader does under the 8+4 convention.
    if "YTG" not in working.columns:
        working["YTG"] = working[YTG_MONTHS].sum(axis=1)

    selected = working[[*_AOP_INDEX, "Type", "YTG"]].copy()
    wide = selected.pivot_table(
        index=_AOP_INDEX,
        columns="Type",
        values="YTG",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    wide = wide.fillna(0)

    # Drop the percent line-item types the AOP query discards before shaping.
    drop_present = [column for column in _AOP_DROP_TYPES if column in wide.columns]
    wide = wide.drop(columns=drop_present)

    # Rename the LBs label to Lbs when present; ensure every measure column the
    # downstream steps require exists (created as 0 when the pivot omitted it).
    if "LBs" in wide.columns:
        wide = wide.rename(columns={"LBs": "Lbs"})
    for column in ["Gross Sales", "Lbs", *NEGATED_COLUMNS]:
        if column not in wide.columns:
            wide[column] = 0.0
    return _finish_wide(wide, _AOP_INDEX)
