"""Q1 results-by-SKU transform for the gross-to-net decomposition.

This module holds the single pure transform ``build_q1_results_by_sku``
(research §4.18). Unlike the main ``LE`` pivot, which consumes only the
year-to-go measure, this transform reads the raw monthly ``Jan``/``Feb``/``Mar``
columns the main pivot discards and produces a first-quarter view of each SKU's
gross-to-net measures and ratios. It performs no I/O; the SQLite boundary lives
in :mod:`src.pandas_io` and the orchestration in :mod:`src.mix_pipeline`.

All column names here are schema, not secret; only the source data values are
confidential and never appear in this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mix_transforms import calc_ratios

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["build_q1_results_by_sku"]

# Dimension columns that survive into the Q1 pivot index. The ``SKU Descripiton``
# typo is intentional and matches the persisted LE table header.
_Q1_INDEX: list[str] = ["Customer", "SKU Descripiton", "SKU #"]

# Rename applied after the pivot so the deduction measures carry their "$" names.
_Q1_RENAMES: dict[str, str] = {
    "Off Invoice": "Off Invoice $",
    "Non-Trade": "Non-Trade $",
    "Trade": "Trade Spend $",
}


def build_q1_results_by_sku(le_raw: pd.DataFrame) -> pd.DataFrame:
    """Build the first-quarter results-by-SKU table (research §4.18).

    Selects the dimension columns plus the monthly ``Jan``/``Feb``/``Mar``
    columns and the ``GtN Mapping`` label, derives ``Q1 = Jan + Feb + Mar``,
    groups and pivots ``GtN Mapping`` on ``Q1``, fills missing with 0, derives
    ``Net Rev = Gross Sales - Off Invoice - Non-Trade - Trade`` (the signs here
    are pre-negation, so the deductions are subtracted), renames the deduction
    measures to their ``$`` names, and applies
    :func:`src.mix_transforms.calc_ratios`.

    Args:
        le_raw: The raw ``LE`` frame including the monthly ``Jan``/``Feb``/``Mar``
            columns, ``Customer``, ``SKU Descripiton``, ``SKU #``, and
            ``GtN Mapping``.

    Returns:
        A wide DataFrame with one row per ``{Customer, SKU Descripiton, SKU #}``
        carrying the Q1 gross-to-net measures (``$`` names), ``Net Rev``, and the
        eight ratio columns.
    """
    selected = le_raw[[*_Q1_INDEX, "GtN Mapping", "Jan", "Feb", "Mar"]].copy()

    # Q1 is the sum of the three first-quarter months for each source row.
    selected["Q1"] = selected["Jan"] + selected["Feb"] + selected["Mar"]

    # Collapse to one Q1 value per (dimensions, GtN label) then pivot the label
    # into wide measure columns.
    grouped = selected.groupby([*_Q1_INDEX, "GtN Mapping"], as_index=False)["Q1"].sum()
    wide = grouped.pivot_table(
        index=_Q1_INDEX,
        columns="GtN Mapping",
        values="Q1",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    wide = wide.fillna(0)

    # Ensure every measure column the net-revenue derivation needs is present
    # (created as 0 when a GtN label is absent from the source quarter).
    for column in ["Gross Sales", "Lbs", "Off Invoice", "Non-Trade", "Trade"]:
        if column not in wide.columns:
            wide[column] = 0.0

    # Net revenue here subtracts the deductions because the Q1 source values are
    # pre-negation (positive), unlike the main pivot which negates first.
    wide["Net Rev"] = (
        wide["Gross Sales"] - wide["Off Invoice"] - wide["Non-Trade"] - wide["Trade"]
    )

    # Rename the deductions to their "$" names and add the net-revenue "$" alias
    # so calc_ratios finds its expected measure columns.
    wide = wide.rename(columns=_Q1_RENAMES)
    wide["Net-Revenue $"] = wide["Net Rev"]
    return calc_ratios(wide)
