"""NRR-summary builder for the gross-to-net decomposition (issue #15).

This module holds the single pure transform :func:`build_nrr_summary`, which
replicates the confidential workbook's ``NRR_Summary`` tab. ``NRR_Summary`` is
the headline summary that ties the Net-Revenue change between AOP and LE back to
its drivers (volume, net pricing, and mix) and carries an internal
reconciliation ``Check``. It is derived entirely from frames the pipeline
already produces, so it is appended as a final pure summary step. The function
performs no I/O; the SQLite/Excel boundaries live in :mod:`src.pandas_io` and
the orchestration in :mod:`src.mix_pipeline` / :mod:`src.mix_pipeline_run`. The
small scalar/row helpers live in :mod:`src._mix_nrr_summary_helpers` so each
file stays under the 500-line limit.

The output is a tidy long table with one row per source-tab label, in source
order, with columns:

    - ``section`` (str): one of ``attribute_summary``,
      ``net_revenue_realization``, ``net_pricing_breakdown``, ``mix_breakdown``,
      ``reconciliation``.
    - ``metric`` (str): the row label exactly as on the tab.
    - ``aop`` (float | None): column-C value where the row defines it.
    - ``le`` (float | None): column-D value where the row defines it.
    - ``value`` (float | None): column-E value (``Abs`` change in the attribute
      block, ``NR $`` in the lower blocks).
    - ``pct`` (float | None): column-F value (``%`` change in the attribute
      block, ``%NR`` in the lower blocks).
    - ``check`` (str | None): ``"CHECK"`` / ``"ERROR"`` for the reconciliation
      ``Check`` row; ``None`` for every other row.

Chosen ``check`` representation (single-field): the ``Check`` row carries its
result only in the ``check`` column. ``check == "CHECK"`` when the NR$ comparison
AND the %NR comparison both reconcile (each ``round(realization - buildup, 0) ==
0``); otherwise ``"ERROR"``. The ``value`` and ``pct`` columns stay ``None`` on
the ``Check`` row so they remain numeric-typed. Tests pin this representation.

All column names, section names, and row labels here are schema, not secret;
only the source data values are confidential and never appear in this module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src._mix_nrr_summary_helpers import (
    Measure,
    all_in_ts,
    attribute_totals,
    column_sum,
    reconciles,
    row,
    safe_ratio,
    sum_optional,
    ts_basis_points,
)

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["NRR_SUMMARY_COLUMNS", "build_nrr_summary"]

# The tidy long-table column set, in output order.
NRR_SUMMARY_COLUMNS: list[str] = [
    "section",
    "metric",
    "aop",
    "le",
    "value",
    "pct",
    "check",
]


def _attribute_summary_rows(
    aop_vs_le: pd.DataFrame,
) -> tuple[list[dict[str, object]], Measure, Measure, Measure]:
    """Build the attribute-summary block and return its three core measures.

    Reproduces the top block of the tab (AC2): the ``Lbs``, ``Gross Sales``, and
    ``Net-Revenue $`` SUMIF measures, the derived ``GS / Lb`` and
    ``Net Rev / Lb`` per-Lb ratios (``Abs = LE - AOP``), and the ``All in TS%``
    row (``AOP = 1 - NetRev/GrossSales``, ``Abs = (LE - AOP) * 10000`` basis
    points, no ``%`` column).

    Args:
        aop_vs_le: The classified comparison frame (``Attribute``, ``AOP``,
            ``LE``, ``Diff``).

    Returns:
        A ``(rows, lbs, gross_sales, net_rev)`` tuple: the block rows plus the
        three core measures the realization block reuses.
    """
    section = "attribute_summary"

    # The three core SUMIF measures feed both this block and the realization
    # block, so compute them once and reuse the totals.
    lbs = Measure(*attribute_totals(aop_vs_le, "Lbs"))
    gross_sales = Measure(*attribute_totals(aop_vs_le, "Gross Sales"))
    net_rev = Measure(*attribute_totals(aop_vs_le, "Net-Revenue $"))

    rows: list[dict[str, object]] = []
    # Emit the three core measures: AOP/LE/Abs sums with % = Abs/AOP.
    for metric, measure in (
        ("Lbs", lbs),
        ("Gross Sales", gross_sales),
        ("Net-Revenue $", net_rev),
    ):
        rows.append(
            row(
                section,
                metric,
                aop=measure.aop,
                le=measure.le,
                value=measure.diff,
                pct=measure.pct,
            )
        )

    # GS / Lb and Net Rev / Lb are per-Lb ratios: AOP = numerator.AOP/Lbs.AOP,
    # LE likewise, Abs = LE - AOP, % = Abs/AOP. Each division guards a zero Lbs
    # total so the empty/fabricated zero path yields None rather than raising.
    rows.append(_per_lb_row(section, "GS / Lb", gross_sales, lbs))
    rows.append(_per_lb_row(section, "Net Rev / Lb", net_rev, lbs))

    # All in TS% = 1 - NetRev/GrossSales per scenario; the Abs delta is scaled
    # to basis points and the row carries no % column.
    ts_aop = all_in_ts(net_rev.aop, gross_sales.aop)
    ts_le = all_in_ts(net_rev.le, gross_sales.le)
    rows.append(
        row(
            section,
            "All in TS%",
            aop=ts_aop,
            le=ts_le,
            value=ts_basis_points(ts_aop, ts_le),
            pct=None,
        )
    )

    return rows, lbs, gross_sales, net_rev


def _per_lb_row(
    section: str,
    metric: str,
    numerator: Measure,
    lbs: Measure,
) -> dict[str, object]:
    """Build one per-Lb ratio row (``GS / Lb`` or ``Net Rev / Lb``).

    Computes ``AOP = numerator.AOP / Lbs.AOP``, ``LE = numerator.LE / Lbs.LE``,
    ``Abs = LE - AOP``, and ``% = Abs / AOP``, guarding each division against a
    zero Lbs (or zero AOP-ratio) denominator.

    Args:
        section: The block name.
        metric: The row label.
        numerator: The Gross-Sales or Net-Revenue measure.
        lbs: The Lbs measure used as the per-Lb denominator.

    Returns:
        A tidy row dict for the per-Lb ratio.
    """
    ratio_aop = safe_ratio(numerator.aop, lbs.aop)
    ratio_le = safe_ratio(numerator.le, lbs.le)

    # Abs and % are only defined when both per-scenario ratios are defined; a
    # zero Lbs total in either scenario leaves the derived cells as None.
    if ratio_aop is None or ratio_le is None:
        return row(section, metric, aop=ratio_aop, le=ratio_le, value=None, pct=None)

    abs_change = ratio_le - ratio_aop
    return row(
        section,
        metric,
        aop=ratio_aop,
        le=ratio_le,
        value=abs_change,
        pct=safe_ratio(abs_change, ratio_aop),
    )


def _realization_rows(
    lbs: Measure,
    net_rev: Measure,
) -> tuple[list[dict[str, object]], float | None, float | None]:
    """Build the Net-Revenue Realization block and return the Price/Mix tie-out.

    Reproduces the realization block (AC3): ``Volume Impact``
    (``NR$ = Lbs.Abs * NetRevPerLb.AOP``) and ``Price/Mix``
    (``NR$ = NetRev.Abs - VolumeImpact.NR$``), each with ``%NR = NR$ /
    NetRev.AOP``. The AOP net-revenue-per-Lb rate guards a zero Lbs.AOP total.

    Args:
        lbs: The Lbs measure (its ``Abs`` and AOP totals drive volume).
        net_rev: The Net-Revenue measure (its ``Abs`` and AOP drive Price/Mix
            and the ``%NR`` denominator).

    Returns:
        A ``(rows, price_mix_value, price_mix_pct)`` tuple: the block rows plus
        the realization Price/Mix ``NR$`` and ``%NR`` (or ``None`` on the zero
        path) for the reconciliation tie-out.
    """
    section = "net_revenue_realization"

    # AOP net revenue per Lb is NetRev.AOP / Lbs.AOP; guard a zero Lbs.AOP total.
    net_rev_per_lb_aop = safe_ratio(net_rev.aop, lbs.aop)

    rows: list[dict[str, object]] = []

    # Volume Impact = Lbs.Abs * NetRevPerLb.AOP; undefined when the rate is None.
    volume_value = None if net_rev_per_lb_aop is None else lbs.diff * net_rev_per_lb_aop
    volume_pct = None if volume_value is None else safe_ratio(volume_value, net_rev.aop)
    rows.append(row(section, "Volume Impact", value=volume_value, pct=volume_pct))

    # Price/Mix = NetRev.Abs - VolumeImpact; undefined when volume is undefined.
    price_mix_value = None if volume_value is None else net_rev.diff - volume_value
    price_mix_pct = (
        None if price_mix_value is None else safe_ratio(price_mix_value, net_rev.aop)
    )
    rows.append(row(section, "Price/Mix", value=price_mix_value, pct=price_mix_pct))

    return rows, price_mix_value, price_mix_pct


def _net_pricing_rows(
    rate_impacts: pd.DataFrame,
    net_rev_aop: float,
) -> tuple[list[dict[str, object]], float, float | None]:
    """Build the Net Pricing Breakdown block and return its totals.

    Reproduces the pricing block (AC4): ``Gross Pricing``, ``OI Rate``,
    ``Promo Rate``, ``Non-trade Rate`` as ``rate_impacts`` column totals, and
    ``Total Net Pricing`` as their sum, each with ``%NR = NR$ / NetRev.AOP``.

    Args:
        rate_impacts: The rate-impact table carrying the four impact columns.
        net_rev_aop: The Net-Revenue AOP total used as the ``%NR`` denominator.

    Returns:
        A ``(rows, total_value, total_pct)`` tuple: the block rows plus the
        ``Total Net Pricing`` ``NR$`` and ``%NR`` for the reconciliation tie-out.
    """
    section = "net_pricing_breakdown"

    # Map each pricing label to its rate_impacts source column. Promo Rate reads
    # the Trade Rate Impact column (the tab labels it "Promo Rate").
    label_to_column: list[tuple[str, str]] = [
        ("Gross Pricing", "Calc Gross Price Impact on Net"),
        ("OI Rate", "OI Rate Impact"),
        ("Promo Rate", "Trade Rate Impact"),
        ("Non-trade Rate", "Non-Trade Rate Impact"),
    ]

    rows: list[dict[str, object]] = []
    total_value = 0.0
    # Sum each pricing column and accumulate the four into Total Net Pricing.
    for metric, column in label_to_column:
        value = column_sum(rate_impacts, column)
        total_value += value
        rows.append(
            row(section, metric, value=value, pct=safe_ratio(value, net_rev_aop))
        )

    total_pct = safe_ratio(total_value, net_rev_aop)
    rows.append(row(section, "Total Net Pricing", value=total_value, pct=total_pct))

    return rows, total_value, total_pct


def _mix_rows(
    mix_1_sku: pd.DataFrame,
    mix_2_category: pd.DataFrame,
    mix_3_customer: pd.DataFrame,
    mix_4_country: pd.DataFrame,
    net_rev_aop: float,
) -> tuple[list[dict[str, object]], float, float | None]:
    """Build the Mix Breakdown block and return its totals.

    Reproduces the mix block (AC5): ``SKU Mix``, ``Category Mix``,
    ``Customer Mix``, ``Country Mix`` as the column total of each level table,
    and ``Total Mix`` as their sum, each with ``%NR = NR$ / NetRev.AOP``.

    Args:
        mix_1_sku: The SKU mix layer carrying the ``SKU Mix`` column.
        mix_2_category: The category mix layer carrying the ``Category Mix``
            column.
        mix_3_customer: The customer mix layer carrying the ``Customer Mix``
            column.
        mix_4_country: The country mix layer carrying the ``Country Mix`` column.
        net_rev_aop: The Net-Revenue AOP total used as the ``%NR`` denominator.

    Returns:
        A ``(rows, total_value, total_pct)`` tuple: the block rows plus the
        ``Total Mix`` ``NR$`` and ``%NR`` for the reconciliation tie-out.
    """
    section = "mix_breakdown"

    sku_value = column_sum(mix_1_sku, "SKU Mix")
    category_value = column_sum(mix_2_category, "Category Mix")
    # The Excel formula references the "Category Mix" column header in the
    # customer table, but the pipeline (build_mix_3_customer) renamed that column
    # to "Customer Mix" as a documented M-source deviation. The replication reads
    # "Customer Mix" to map the Excel Mix_3_Customer[[#Totals],[Category Mix]]
    # reference; this mapping is preserved deliberately (AC5).
    customer_value = column_sum(mix_3_customer, "Customer Mix")
    country_value = column_sum(mix_4_country, "Country Mix")

    total_value = sku_value + category_value + customer_value + country_value

    rows: list[dict[str, object]] = []
    # Emit the four mix levels in source order, each with %NR = value/NetRev.AOP.
    for metric, value in (
        ("SKU Mix", sku_value),
        ("Category Mix", category_value),
        ("Customer Mix", customer_value),
        ("Country Mix", country_value),
    ):
        rows.append(
            row(section, metric, value=value, pct=safe_ratio(value, net_rev_aop))
        )

    total_pct = safe_ratio(total_value, net_rev_aop)
    rows.append(row(section, "Total Mix", value=total_value, pct=total_pct))

    return rows, total_value, total_pct


def _reconciliation_rows(
    realization_price_mix: float | None,
    realization_price_mix_pct: float | None,
    total_mix_value: float,
    total_mix_pct: float | None,
    total_pricing_value: float,
    total_pricing_pct: float | None,
) -> list[dict[str, object]]:
    """Build the reconciliation block: the build-up Price/Mix and the Check.

    Reproduces the reconciliation block (AC6): ``Price / Mix`` build-up
    (``NR$ = Total Mix + Total Net Pricing``; ``%NR = %Total Mix + %Total Net
    Pricing``) and the ``Check`` row, which is ``"CHECK"`` only when both the
    NR$ comparison and the %NR comparison reconcile
    (``round(realization - buildup, 0) == 0`` each) and ``"ERROR"`` otherwise.

    Args:
        realization_price_mix: The realization-derived Price/Mix ``NR$``.
        realization_price_mix_pct: The realization-derived Price/Mix ``%NR``.
        total_mix_value: The ``Total Mix`` ``NR$``.
        total_mix_pct: The ``Total Mix`` ``%NR``.
        total_pricing_value: The ``Total Net Pricing`` ``NR$``.
        total_pricing_pct: The ``Total Net Pricing`` ``%NR``.

    Returns:
        The two reconciliation rows (``Price / Mix`` build-up and ``Check``).
    """
    section = "reconciliation"

    # Build-up NR$ = Total Mix + Total Net Pricing; build-up %NR is the sum of
    # the two %NR totals (None when either %NR is undefined on the zero path).
    buildup_value = total_mix_value + total_pricing_value
    buildup_pct = sum_optional(total_mix_pct, total_pricing_pct)

    rows: list[dict[str, object]] = []
    rows.append(row(section, "Price / Mix", value=buildup_value, pct=buildup_pct))

    # The Check ties the realization Price/Mix to the build-up independently for
    # the NR$ and the %NR comparisons; both must reconcile for "CHECK".
    nr_ok = reconciles(realization_price_mix, buildup_value)
    pct_ok = reconciles(realization_price_mix_pct, buildup_pct)
    check = "CHECK" if (nr_ok and pct_ok) else "ERROR"
    rows.append(row(section, "Check", check=check))

    return rows


def build_nrr_summary(
    aop_vs_le: pd.DataFrame,
    rate_impacts: pd.DataFrame,
    mix_1_sku: pd.DataFrame,
    mix_2_category: pd.DataFrame,
    mix_3_customer: pd.DataFrame,
    mix_4_country: pd.DataFrame,
) -> pd.DataFrame:
    """Build the ``nrr_summary`` tidy long table from the pipeline frames (#15).

    Replicates the workbook's ``NRR_Summary`` tab as a tidy long table with one
    row per source-tab label in source order. Composes the five blocks
    (attribute summary, net-revenue realization, net pricing breakdown, mix
    breakdown, reconciliation) and the internal ``Check`` tie-out. Pure: it
    performs no I/O and reads only the six input frames.

    Args:
        aop_vs_le: The classified comparison frame (``Attribute``, ``AOP``,
            ``LE``, ``Diff``) for the SUMIF-by-attribute totals.
        rate_impacts: The rate-impact table for the net-pricing column totals.
        mix_1_sku: The SKU mix layer (``SKU Mix`` column).
        mix_2_category: The category mix layer (``Category Mix`` column).
        mix_3_customer: The customer mix layer (``Customer Mix`` column).
        mix_4_country: The country mix layer (``Country Mix`` column).

    Returns:
        A DataFrame with columns :data:`NRR_SUMMARY_COLUMNS`, one row per
        labeled tab row, ending with the reconciliation ``Check`` row whose
        ``check`` cell is ``"CHECK"`` when the realization and build-up Price/Mix
        reconcile (NR$ and %NR) and ``"ERROR"`` otherwise.
    """
    import pandas as pd

    # The attribute summary yields the three core measures the realization block
    # reuses (Lbs, Gross Sales, Net-Revenue $), so build it first.
    attribute_rows, lbs, _gross_sales, net_rev = _attribute_summary_rows(aop_vs_le)

    realization_rows, realization_price_mix, realization_price_mix_pct = (
        _realization_rows(lbs, net_rev)
    )

    pricing_rows, total_pricing_value, total_pricing_pct = _net_pricing_rows(
        rate_impacts, net_rev.aop
    )
    mix_block_rows, total_mix_value, total_mix_pct = _mix_rows(
        mix_1_sku, mix_2_category, mix_3_customer, mix_4_country, net_rev.aop
    )
    reconciliation_rows = _reconciliation_rows(
        realization_price_mix,
        realization_price_mix_pct,
        total_mix_value,
        total_mix_pct,
        total_pricing_value,
        total_pricing_pct,
    )

    # Concatenate the five blocks in source order into the tidy long table.
    all_rows = [
        *attribute_rows,
        *realization_rows,
        *pricing_rows,
        *mix_block_rows,
        *reconciliation_rows,
    ]
    return pd.DataFrame(all_rows, columns=NRR_SUMMARY_COLUMNS)
