"""Lookup and comparison transforms for the gross-to-net decomposition.

This module holds the pure (I/O-free) transforms that sit between the
long-to-wide source pivots and the rate/mix decomposition: the customer lookup,
the per-scenario normalizations, the AOP-versus-LE comparison with
classification, and the enriched ``Mix_Base`` table. Every function takes and
returns a ``pandas.DataFrame`` and performs no I/O; the SQLite/Excel boundaries
live in :mod:`src.pandas_io` and the orchestration in :mod:`src.mix_pipeline`.

Functions provided (research §4.3, §4.5-§4.8):
    - ``build_customer_lu``: distinct ``{Customer, Customer Master}`` pairs.
    - ``build_aop_norm`` / ``build_le_norm``: reduce the long pivots to
      ``{Customer, SKU #, Attribute, Scenario, Value}``.
    - ``build_aop_vs_le``: concat, pivot Scenario on Value, filter ``Cases``,
      add ``Diff``, and classify (reusing ``classify_table``).
    - ``build_mix_base``: enrich with the SKU lookup and filter to the six
      measure attributes excluding inactive lines.

All column names and classification labels are schema, not secret; only the
source data values are confidential and never appear here.
"""

from __future__ import annotations

import pandas as pd

from src.mix_transforms import classify_table

__all__ = [
    "MIX_BASE_ATTRIBUTES",
    "build_aop_norm",
    "build_aop_vs_le",
    "build_customer_lu",
    "build_le_norm",
    "build_mix_base",
]

# The six measure attributes retained by ``build_mix_base``; ratio attributes
# and the dropped ``Cases`` row are excluded.
MIX_BASE_ATTRIBUTES: list[str] = [
    "Gross Sales",
    "Lbs",
    "Net-Revenue $",
    "Non-Trade $",
    "Off Invoice $",
    "Trade Spend $",
]

# Columns dropped from the long AOP pivot to form the normalized comparison
# shape (AOP additionally carries Customer Master and Super Category).
_AOP_DROP: list[str] = [
    "Customer Master",
    "Super Category",
    "PPG",
    "SKU Descripiton",
]

# Columns dropped from the long LE pivot to form the normalized comparison shape.
_LE_DROP: list[str] = ["Super Category", "PPG", "SKU Descripiton"]


def build_customer_lu(aop_raw: pd.DataFrame) -> pd.DataFrame:
    """Build the distinct ``{Customer, Customer Master}`` lookup (research §4.3).

    Reduces the raw ``aop`` frame to the distinct customer-to-master pairs used
    to enrich LE rows (which carry no ``Customer Master``).

    Args:
        aop_raw: The raw ``aop`` frame containing ``Customer`` and
            ``Customer Master``.

    Returns:
        A two-column DataFrame ``{Customer, Customer Master}`` with one row per
        distinct pair, in first-appearance order.
    """
    distinct = aop_raw[["Customer", "Customer Master"]].drop_duplicates()
    return distinct.reset_index(drop=True)


def build_aop_norm(aop_long: pd.DataFrame) -> pd.DataFrame:
    """Reduce the long AOP pivot to the normalized comparison shape (research §4.5).

    Drops the dimension columns not used by the comparison and adds the constant
    ``Scenario = "AOP"`` literal.

    Args:
        aop_long: The long-format AOP frame from :func:`src.mix_transforms.pivot_aop`
            with ``Customer``, ``SKU #``, ``Attribute``, and ``Value`` columns.

    Returns:
        A DataFrame ``{Customer, SKU #, Attribute, Scenario, Value}`` with
        ``Scenario`` set to ``"AOP"``.
    """
    drop_present = [column for column in _AOP_DROP if column in aop_long.columns]
    reduced = aop_long.drop(columns=drop_present).copy()
    reduced["Scenario"] = "AOP"
    return reduced[["Customer", "SKU #", "Attribute", "Scenario", "Value"]]


def build_le_norm(le_long: pd.DataFrame) -> pd.DataFrame:
    """Reduce the long LE pivot to the normalized comparison shape (research §4.6).

    Drops the dimension columns not used by the comparison and adds the constant
    ``Scenario = "LE"`` literal.

    Args:
        le_long: The long-format LE frame from :func:`src.mix_transforms.pivot_le`
            with ``Customer``, ``SKU #``, ``Attribute``, and ``Value`` columns.

    Returns:
        A DataFrame ``{Customer, SKU #, Attribute, Scenario, Value}`` with
        ``Scenario`` set to ``"LE"``.
    """
    drop_present = [column for column in _LE_DROP if column in le_long.columns]
    reduced = le_long.drop(columns=drop_present).copy()
    reduced["Scenario"] = "LE"
    return reduced[["Customer", "SKU #", "Attribute", "Scenario", "Value"]]


def build_aop_vs_le(
    aop_norm: pd.DataFrame,
    le_norm: pd.DataFrame,
) -> pd.DataFrame:
    """Combine the normalized scenarios, pivot, filter, diff, and classify (§4.7).

    Concatenates ``aop_norm`` and ``le_norm``, pivots ``Scenario`` onto the
    ``Value`` column to produce ``AOP`` and ``LE`` columns, fills missing with 0,
    filters out the ``Cases`` attribute (LE has no ``Cases`` row, so it would be
    0-filled), adds ``Diff = LE - AOP``, and applies the two-level
    :func:`src.mix_transforms.classify_table`.

    Args:
        aop_norm: The normalized AOP frame from :func:`build_aop_norm`.
        le_norm: The normalized LE frame from :func:`build_le_norm`.

    Returns:
        A DataFrame ``{Customer, SKU #, Attribute, AOP, LE, Diff,
        Classification}``.
    """
    combined = pd.concat([aop_norm, le_norm], ignore_index=True)
    wide = combined.pivot_table(
        index=["Customer", "SKU #", "Attribute"],
        columns="Scenario",
        values="Value",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None

    # Ensure both scenario columns exist and are zero-filled before the diff.
    for scenario in ("AOP", "LE"):
        if scenario not in wide.columns:
            wide[scenario] = 0.0
    wide["AOP"] = wide["AOP"].fillna(0)
    wide["LE"] = wide["LE"].fillna(0)

    # The M source drops the Cases attribute because LE carries no Cases row, so
    # the comparison would otherwise show a spurious AOP-only line.
    wide = wide[wide["Attribute"] != "Cases"].copy()

    wide["Diff"] = wide["LE"] - wide["AOP"]
    return classify_table(wide)


def build_mix_base(
    aop_vs_le: pd.DataFrame,
    sku_lu: pd.DataFrame,
) -> pd.DataFrame:
    """Enrich AopVsLe with the SKU lookup and filter to the mix base (research §4.8).

    Casts ``SKU #`` to ``str`` before a left-join to ``sku_lu`` on
    ``SKU # == SKU`` (the M source casts the key to text first), reorders to the
    canonical column order, then filters to the six measure attributes
    (:data:`MIX_BASE_ATTRIBUTES`) and excludes ``Classification == "inactive"``.

    Args:
        aop_vs_le: The classified comparison frame from :func:`build_aop_vs_le`.
        sku_lu: The SKU lookup frame ``{SKU, SKU Description, Category, Country}``
            from :func:`src.load_skulu.load_skulu`.

    Returns:
        A DataFrame ``{Customer, SKU #, SKU Description, Category, Country,
        Attribute, AOP, LE, Diff, Classification}`` filtered to the six measure
        attributes and excluding inactive lines.
    """
    enriched = aop_vs_le.copy()

    # Cast the join key to text so a numeric SKU # matches the text SKU lookup
    # key, matching the M "Changed Type" step before the LeftOuter join.
    enriched["SKU #"] = enriched["SKU #"].astype(str)
    lookup = sku_lu.copy()
    lookup["SKU"] = lookup["SKU"].astype(str)

    merged = enriched.merge(
        lookup,
        how="left",
        left_on="SKU #",
        right_on="SKU",
    )

    # Reorder to the canonical column layout; the join's SKU helper column is
    # dropped because SKU # already carries the key.
    ordered_columns = [
        "Customer",
        "SKU #",
        "SKU Description",
        "Category",
        "Country",
        "Attribute",
        "AOP",
        "LE",
        "Diff",
        "Classification",
    ]
    merged = merged[ordered_columns]

    # Keep only the six measure attributes and drop inactive lines so eliminated
    # and inactive SKUs do not distort the downstream mix decomposition.
    is_measure = merged["Attribute"].isin(MIX_BASE_ATTRIBUTES)
    is_active = merged["Classification"] != "inactive"
    return merged[is_measure & is_active].reset_index(drop=True)
