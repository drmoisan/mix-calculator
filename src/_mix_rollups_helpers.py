"""Shared rollup machinery for :mod:`src.mix_rollups`.

This module holds the pure helpers that the Mix-1..4 rollup tables share, so that
:mod:`src.mix_rollups` stays under the 500-line file limit. It depends only on
``pandas`` plus the pure primitives in :mod:`src.mix_transforms`, and imports
nothing from :mod:`src.mix_rollups`, so the rollup builders can compose these
helpers without an import cycle.

The recurring Mix-N pattern (research §4.11, §4.13-§4.14) is: group the source
table by its key columns summing ``AOP``/``LE``/``Diff``; melt to a Scenario
shape and drop ``Diff``; ``add_ratios`` for both scenarios; pivot back to
``AOP``/``LE`` and recompute ``Diff``; melt again and ``stack_pivot`` into wide
``"Attribute - Scenario"`` columns; filter to nonzero Lbs; recompute the net
per-Lb diff and the net price impact. This module factors that shared body into
``build_mix_stage`` so each rollup builder supplies only its group keys. Each
mix layer aggregates the unfiltered ``Mix_Base`` at its own granularity
(issue #20), so the layers do not re-aggregate a prior filtered layer.

All column names here are schema, not secret; only the source data values are
confidential and never appear in this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.mix_transforms import add_ratios, stack_pivot

if TYPE_CHECKING:
    import pandas as pd

# Attributes carried into the StackPivot for the Mix-N stages; the rate
# decomposition only needs volume, the net per-Lb rate, and net revenue.
_STAGE_ATTRIBUTES: list[str] = ["Lbs", "Net Rev Per Lb", "Net-Revenue $"]


def group_net_price_impact(
    source: pd.DataFrame,
    key_cols: list[str],
) -> pd.DataFrame:
    """Sum ``Calc Net Price Impact`` by ``key_cols`` (the recurring rollup lookup).

    Reproduces the ``GroupAndLookUp`` pattern shared by every ``Mix-Rollup-N``
    query (research §3.7): a groupby-sum of the net price impact used as a join
    target by the next ``Mix-N`` table.

    Args:
        source: The prior Mix-N table carrying ``Calc Net Price Impact``.
        key_cols: The grouping key columns (for example ``["Customer",
            "Country", "Category"]``).

    Returns:
        A DataFrame with one row per distinct key combination and the summed
        ``Calc Net Price Impact``.
    """
    grouped = source.groupby(key_cols, as_index=False)[["Calc Net Price Impact"]].sum()
    return grouped


def build_mix_stage(
    source: pd.DataFrame,
    group_keys: list[str],
) -> pd.DataFrame:
    """Run the shared Mix-N reshape and net-price-impact computation.

    Implements the body common to ``Mix-1-SKu``, ``Mix-2-Category``,
    ``Mix-3-Customer``, and ``Mix-4-Country`` (research §4.11): group by
    ``group_keys`` plus ``Attribute`` summing the scenarios, append per-scenario
    ratios, recompute the scenario diff, stack into wide ``"Attribute -
    Scenario"`` columns, keep only rows with nonzero AOP and LE Lbs, recompute
    the net per-Lb diff, and compute ``Calc Net Price Impact``.

    Each mix layer supplies the unfiltered ``Mix_Base`` as ``source`` at its own
    ``group_keys`` granularity (issue #20), so coarser layers retain volume from
    single-scenario lines that the nonzero-Lbs filter would drop at the SKU
    granularity.

    Args:
        source: The unfiltered ``Mix_Base`` table carrying ``Attribute``,
            ``AOP``, ``LE``, and ``Diff`` plus the ``group_keys`` columns.
        group_keys: The dimension columns that survive this stage's grouping.

    Returns:
        A wide DataFrame keyed by ``group_keys`` with the stacked
        ``"Attribute - Scenario"`` columns and a ``Calc Net Price Impact`` column,
        filtered to rows with nonzero AOP and LE Lbs.
    """
    # Group the scenarios by the surviving dimensions plus Attribute, summing the
    # AOP/LE/Diff measures so each (group, attribute) collapses to one row.
    grouped = source.groupby([*group_keys, "Attribute"], as_index=False)[
        ["AOP", "LE", "Diff"]
    ].sum()

    # Melt to a long Scenario shape and drop Diff so add_ratios recomputes ratios
    # from the AOP and LE measures only.
    melted = grouped.melt(
        id_vars=[*group_keys, "Attribute"],
        value_vars=["AOP", "LE", "Diff"],
        var_name="Scenario",
        value_name="Value",
    )
    melted = melted[melted["Scenario"] != "Diff"].copy()

    # Append per-scenario ratio rows, then pivot back to AOP/LE columns so the
    # diff can be recomputed on the regrouped measures.
    with_ratios = add_ratios(melted, ["AOP", "LE"])
    wide = with_ratios.pivot_table(
        index=[*group_keys, "Attribute"],
        columns="Scenario",
        values="Value",
        aggfunc="sum",
    ).reset_index()
    wide.columns.name = None
    # Both AOP and LE rows are always present after the melt, so the pivot always
    # yields both columns; fill any NaN cells (missing attribute/scenario pairs)
    # with 0 before recomputing the diff.
    wide["AOP"] = wide["AOP"].fillna(0)
    wide["LE"] = wide["LE"].fillna(0)
    wide["Diff"] = wide["LE"] - wide["AOP"]

    # Melt back to long and stack {Attribute, Scenario} into wide columns,
    # keeping only the volume / net-rate / net-revenue attributes the impact
    # computation needs.
    relong = wide.melt(
        id_vars=[*group_keys, "Attribute"],
        value_vars=["AOP", "LE", "Diff"],
        var_name="Scenario",
        value_name="Value",
    )
    relong = relong[relong["Attribute"].isin(_STAGE_ATTRIBUTES)].copy()
    stacked = stack_pivot(relong, ["Attribute", "Scenario"], "Value")

    # Keep only rows with nonzero AOP and LE Lbs so empty lines do not divide the
    # decomposition (the M source filters [Lbs - AOP] != 0 and [Lbs - LE] != 0).
    stacked = stacked[(stacked["Lbs - AOP"] != 0) & (stacked["Lbs - LE"] != 0)].copy()

    # Recompute the net per-Lb diff on the regrouped rates and the net price
    # impact as that diff applied to LE volume.
    stacked["Net Rev Per Lb - Diff"] = (
        stacked["Net Rev Per Lb - LE"] - stacked["Net Rev Per Lb - AOP"]
    )
    stacked["Calc Net Price Impact"] = (
        stacked["Net Rev Per Lb - Diff"] * stacked["Lbs - LE"]
    )
    return stacked


def join_rollup_mix(
    stage: pd.DataFrame,
    rollup: pd.DataFrame,
    join_keys: list[str],
    mix_column: str,
) -> pd.DataFrame:
    """Join a rollup's net price impact and compute the named mix column.

    Reproduces the join-and-subtract step shared by the Mix-N tables: left-join
    the rollup's ``Calc Net Price Impact`` (renamed to a rollup-scoped column),
    fill unmatched with 0, then compute ``mix_column`` as the stage's net price
    impact minus the rollup's.

    Args:
        stage: The stage output from :func:`build_mix_stage`.
        rollup: The grouped rollup from :func:`group_net_price_impact`.
        join_keys: The columns to join on.
        mix_column: The name of the derived mix column to add (for example
            ``"SKU Mix"`` or ``"Category Mix"``).

    Returns:
        ``stage`` with the rollup's net price impact joined (as
        ``"Rollup Calc Net Price Impact"``) and the ``mix_column`` computed.
    """
    rollup_renamed = rollup.rename(
        columns={"Calc Net Price Impact": "Rollup Calc Net Price Impact"}
    )
    joined = stage.merge(rollup_renamed, how="left", on=join_keys)
    joined["Rollup Calc Net Price Impact"] = joined[
        "Rollup Calc Net Price Impact"
    ].fillna(0)
    joined[mix_column] = (
        joined["Calc Net Price Impact"] - joined["Rollup Calc Net Price Impact"]
    )
    return joined
