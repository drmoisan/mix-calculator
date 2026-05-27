"""Mix rollup chain and detail table for the gross-to-net decomposition.

This module holds the pure (I/O-free) rollup chain that decomposes the net price
impact into SKU, category, customer, and country mix layers, plus the row-level
``Mix-0-Detail`` table. The recurring reshape body lives in
:mod:`src._mix_rollups_helpers` so this file stays under the 500-line limit;
this module supplies each layer's group keys and the layer-specific steps.

Functions provided (research §4.10-§4.17):
    - ``build_mix_rollup_1`` .. ``build_mix_rollup_3``: net-price-impact lookups.
    - ``build_mix_rollup_4``: the scalar ``float`` sum of the customer layer.
    - ``build_mix_1_sku`` .. ``build_mix_4_country``: the mix layers.
    - ``build_mix_0_detail``: the row-level detail with composite keys.

M-source deviations documented in code: ``build_mix_3_customer`` names its
derived column ``Customer Mix`` (the M source reuses "Category Mix", a
copy-paste artifact); ``build_mix_4_country`` subtracts the scalar
``mix_rollup_4`` to produce ``Country Mix``.

All column names here are schema, not secret; only the source data values are
confidential and never appear in this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src._mix_rollups_helpers import (
    build_mix_stage,
    group_net_price_impact,
    join_rollup_mix,
    unstack_to_long,
)
from src.mix_transforms import add_ratios, fill_zero_with_avg, stack_pivot

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "build_mix_0_detail",
    "build_mix_1_sku",
    "build_mix_2_category",
    "build_mix_3_customer",
    "build_mix_4_country",
    "build_mix_rollup_1",
    "build_mix_rollup_2",
    "build_mix_rollup_3",
    "build_mix_rollup_4",
]


def build_mix_rollup_1(rate_impacts: pd.DataFrame) -> pd.DataFrame:
    """Sum the net price impact by ``{Customer, Country, Category}`` (research §4.10).

    Args:
        rate_impacts: The rate-impact table carrying ``Calc Net Price Impact``
            and the ``Customer``, ``Country``, and ``Category`` columns.

    Returns:
        A lookup DataFrame keyed by ``{Customer, Country, Category}`` with the
        summed ``Calc Net Price Impact``.
    """
    return group_net_price_impact(rate_impacts, ["Customer", "Country", "Category"])


def build_mix_1_sku(
    mix_base: pd.DataFrame,
    mix_rollup_1: pd.DataFrame,
) -> pd.DataFrame:
    """Build the SKU mix layer from ``Mix_Base`` and Mix-Rollup-1 (research §4.11).

    Runs the shared Mix-N reshape grouped by ``{Customer, Category, Country}``,
    joins Mix-Rollup-1 on those keys, and computes ``SKU Mix`` as the line's net
    price impact minus the rollup's.

    Args:
        mix_base: The enriched ``Mix_Base`` table.
        mix_rollup_1: The Mix-Rollup-1 lookup from :func:`build_mix_rollup_1`.

    Returns:
        A DataFrame keyed by ``{Customer, Category, Country}`` with the stacked
        columns, ``Calc Net Price Impact``, and ``SKU Mix``.
    """
    stage = build_mix_stage(mix_base, ["Customer", "Category", "Country"])
    return join_rollup_mix(
        stage, mix_rollup_1, ["Customer", "Country", "Category"], "SKU Mix"
    )


def build_mix_rollup_2(mix_1_sku: pd.DataFrame) -> pd.DataFrame:
    """Sum the net price impact by ``{Customer, Country}`` (research §4.12).

    Args:
        mix_1_sku: The SKU mix layer from :func:`build_mix_1_sku`.

    Returns:
        A lookup DataFrame keyed by ``{Customer, Country}`` with the summed
        ``Calc Net Price Impact``.
    """
    return group_net_price_impact(mix_1_sku, ["Customer", "Country"])


def build_mix_2_category(
    mix_1_sku: pd.DataFrame,
    mix_rollup_2: pd.DataFrame,
) -> pd.DataFrame:
    """Build the category mix layer from Mix-1-SKu and Mix-Rollup-2 (research §4.13).

    Args:
        mix_1_sku: The SKU mix layer from :func:`build_mix_1_sku`.
        mix_rollup_2: The Mix-Rollup-2 lookup from :func:`build_mix_rollup_2`.

    Returns:
        A DataFrame keyed by ``{Customer, Country}`` with the stacked columns,
        ``Calc Net Price Impact``, and ``Category Mix``.
    """
    # Mix-1-SKu arrives in wide stacked form; reverse it to long AOP/LE/Diff so
    # the shared stage can regroup it by the coarser {Customer, Country} keys.
    long_form = unstack_to_long(mix_1_sku, ["Customer", "Category", "Country"])
    stage = build_mix_stage(long_form, ["Customer", "Country"])
    return join_rollup_mix(stage, mix_rollup_2, ["Customer", "Country"], "Category Mix")


def build_mix_rollup_3(mix_2_category: pd.DataFrame) -> pd.DataFrame:
    """Sum the net price impact by ``{Country}`` (research §4.14).

    Args:
        mix_2_category: The category mix layer from :func:`build_mix_2_category`.

    Returns:
        A lookup DataFrame keyed by ``{Country}`` with the summed
        ``Calc Net Price Impact``.
    """
    return group_net_price_impact(mix_2_category, ["Country"])


def build_mix_3_customer(
    mix_2_category: pd.DataFrame,
    mix_rollup_3: pd.DataFrame,
) -> pd.DataFrame:
    """Build the customer mix layer from Mix-2-Category and Mix-Rollup-3 (§4.14).

    Runs the shared Mix-N reshape grouped by ``{Country}``, applies
    ``fill_zero_with_avg`` to both scenario ``Net Rev Per Lb`` columns so zero
    rates do not distort the decomposition, recomputes the net price impact, then
    joins Mix-Rollup-3 and computes ``Customer Mix``.

    The derived column is named ``Customer Mix`` rather than the M source's
    "Category Mix"; the M source reuses the "Category Mix" label here, which is a
    copy-paste artifact (research §6.6). ``Category Mix`` is reserved for
    :func:`build_mix_2_category`.

    Args:
        mix_2_category: The category mix layer from :func:`build_mix_2_category`.
        mix_rollup_3: The Mix-Rollup-3 lookup from :func:`build_mix_rollup_3`.

    Returns:
        A DataFrame keyed by ``{Country}`` with the stacked columns, the
        zero-filled rate, ``Calc Net Price Impact``, and ``Customer Mix``.
    """
    # Mix-2-Category arrives in wide stacked form keyed by {Customer, Country};
    # reverse it to long form so the shared stage can regroup it by {Country}.
    long_form = unstack_to_long(mix_2_category, ["Customer", "Country"])
    stage = build_mix_stage(long_form, ["Country"])
    stage = _apply_fill_zero_and_recompute(stage)
    return join_rollup_mix(stage, mix_rollup_3, ["Country"], "Customer Mix")


def build_mix_rollup_4(mix_3_customer: pd.DataFrame) -> float:
    """Return the scalar sum of the customer layer's net price impact (§4.15).

    Args:
        mix_3_customer: The customer mix layer from :func:`build_mix_3_customer`.

    Returns:
        The ``float`` total of ``mix_3_customer["Calc Net Price Impact"]``.
    """
    return float(mix_3_customer["Calc Net Price Impact"].sum())


def build_mix_4_country(
    mix_3_customer: pd.DataFrame,
    mix_rollup_4: float,
) -> pd.DataFrame:
    """Build the country mix layer subtracting the scalar Mix-Rollup-4 (§4.16).

    Runs the shared Mix-N reshape grouped by no dimension (a single all-rows
    group), applies ``fill_zero_with_avg``, recomputes the net price impact, then
    subtracts the broadcast scalar ``mix_rollup_4`` to produce ``Country Mix``.

    Args:
        mix_3_customer: The customer mix layer from :func:`build_mix_3_customer`.
        mix_rollup_4: The scalar from :func:`build_mix_rollup_4`.

    Returns:
        A single-group DataFrame with the stacked columns, the zero-filled rate,
        ``Calc Net Price Impact``, and ``Country Mix``.
    """
    # Mix-3-Customer arrives in wide stacked form keyed by {Country}; reverse it
    # to long form, then group with a constant key so the shared stage collapses
    # every row into one country-level line, dropping the synthetic key after.
    long_form = unstack_to_long(mix_3_customer, ["Country"])
    long_form["_all"] = "all"
    stage = build_mix_stage(long_form, ["_all"])
    stage = _apply_fill_zero_and_recompute(stage)
    stage = stage.drop(columns=["_all"])

    # Subtract the scalar Mix-Rollup-4 as a broadcast to produce the country mix.
    stage["Country Mix"] = stage["Calc Net Price Impact"] - mix_rollup_4
    return stage


def _apply_fill_zero_and_recompute(stage: pd.DataFrame) -> pd.DataFrame:
    """Fill zero net rates with the cross-row average and recompute the impact.

    Applied in the customer and country layers (research §4.14, §4.16): replace
    zero ``Net Rev Per Lb - AOP`` and ``Net Rev Per Lb - LE`` with the cross-row
    average rate so new/lost lines with a zero rate do not distort the mix, then
    recompute the net per-Lb diff and the net price impact.

    Args:
        stage: A stage output from
            :func:`src._mix_rollups_helpers.build_mix_stage`.

    Returns:
        The stage with both scenario rates zero-filled and
        ``Calc Net Price Impact`` recomputed.
    """
    result = stage.copy()
    # Fill the AOP and LE per-Lb rates against their own scenario Lbs/net-revenue
    # totals so each scenario's zero rates use that scenario's average.
    result = fill_zero_with_avg(
        result, "Lbs - AOP", "Net-Revenue $ - AOP", "Net Rev Per Lb - AOP"
    )
    result = fill_zero_with_avg(
        result, "Lbs - LE", "Net-Revenue $ - LE", "Net Rev Per Lb - LE"
    )
    result["Net Rev Per Lb - Diff"] = (
        result["Net Rev Per Lb - LE"] - result["Net Rev Per Lb - AOP"]
    )
    result["Calc Net Price Impact"] = (
        result["Net Rev Per Lb - Diff"] * result["Lbs - LE"]
    )
    return result


def build_mix_0_detail(mix_base: pd.DataFrame) -> pd.DataFrame:
    """Build the row-level detail table with composite keys (research §4.17).

    Melts ``Mix_Base`` to a Scenario shape, drops ``Diff``, appends per-scenario
    ratios, pivots back and recomputes the diff, stacks ``{Attribute, Scenario}``
    into wide columns, and adds three composite key columns. Unlike the rollup
    layers it applies no Lbs filter, so it retains every detail line.

    Composite keys:
        - ``CustSkuCountry`` = ``Customer - SKU # - Country``
        - ``CustCatCountry`` = ``Customer - Category - Country``
        - ``CustCountry`` = ``Customer - Country``

    Args:
        mix_base: The enriched ``Mix_Base`` table.

    Returns:
        A wide detail DataFrame with the stacked ``"Attribute - Scenario"``
        columns and the three composite key columns.
    """
    detail_keys = ["Customer", "SKU #", "SKU Description", "Category", "Country"]

    # Melt to a Scenario shape and drop Diff so add_ratios recomputes the ratios.
    melted = mix_base.melt(
        id_vars=[*detail_keys, "Attribute", "Classification"],
        value_vars=["AOP", "LE", "Diff"],
        var_name="Scenario",
        value_name="Value",
    )
    melted = melted[melted["Scenario"] != "Diff"].copy()
    melted = melted.drop(columns=["Classification"])

    with_ratios = add_ratios(melted, ["AOP", "LE"])
    wide = with_ratios.pivot_table(
        index=[*detail_keys, "Attribute"],
        columns="Scenario",
        values="Value",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    # Both AOP and LE rows are always present after the melt, so the pivot always
    # yields both columns; fill any NaN cells with 0 before recomputing the diff.
    wide["AOP"] = wide["AOP"].fillna(0)
    wide["LE"] = wide["LE"].fillna(0)
    wide["Diff"] = wide["LE"] - wide["AOP"]

    relong = wide.melt(
        id_vars=[*detail_keys, "Attribute"],
        value_vars=["AOP", "LE", "Diff"],
        var_name="Scenario",
        value_name="Value",
    )
    stacked = stack_pivot(relong, ["Attribute", "Scenario"], "Value")

    # Build the three composite drill-through keys by joining the dimension
    # columns with " - " so each detail line carries its own grouping keys.
    customers = [str(value) for value in stacked["Customer"].tolist()]
    skus = [str(value) for value in stacked["SKU #"].tolist()]
    categories = [str(value) for value in stacked["Category"].tolist()]
    countries = [str(value) for value in stacked["Country"].tolist()]
    stacked["CustSkuCountry"] = [
        f"{customers[i]} - {skus[i]} - {countries[i]}" for i in range(len(stacked))
    ]
    stacked["CustCatCountry"] = [
        f"{customers[i]} - {categories[i]} - {countries[i]}"
        for i in range(len(stacked))
    ]
    stacked["CustCountry"] = [
        f"{customers[i]} - {countries[i]}" for i in range(len(stacked))
    ]
    return stacked
