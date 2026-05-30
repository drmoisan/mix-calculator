"""Rate-impact decomposition transform for the gross-to-net model.

This module holds the single pure transform ``build_rate_impacts`` (research
§4.9), the most complex step in the decomposition. It filters the comparison to
``normal`` customer-SKU lines, reshapes the AOP/LE/Diff scenarios into wide
``"Attribute - Scenario"`` columns via :func:`src.mix_transforms.stack_pivot`,
computes the six derived price/rate-impact columns from those wide columns, and
enriches the result with the SKU lookup. It performs no I/O; the SQLite/Excel
boundaries live in :mod:`src.pandas_io` and the orchestration in
:mod:`src.mix_pipeline`.

All column names here are schema, not secret; only the source data values are
confidential and never appear in this module.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.mix_transforms import stack_pivot

__all__ = ["RATE_IMPACT_COLUMNS", "build_rate_impacts"]

# The six derived impact columns produced by ``build_rate_impacts``, in the
# order the M source computes them (research §4.9 step 5).
RATE_IMPACT_COLUMNS: list[str] = [
    "Calc Gross Price Impact on Gross",
    "Calc Gross Price Impact on Net",
    "OI Rate Impact",
    "Trade Rate Impact",
    "Non-Trade Rate Impact",
    "Calc Net Price Impact",
]


def _guarded_div(num: pd.Series, den: pd.Series) -> pd.Series:
    """Divide two series element-wise, returning 0 where the denominator <= 0.

    Local copy of the ``_mix_transforms_helpers._safe_div`` guard so the per-Lb
    and %GS metrics can be recomputed here without importing a private symbol
    across modules or modifying ``calc_ratios``/``_safe_div``. The semantics are
    identical: a ratio is produced only when its denominator is strictly
    positive (``den > 0``); a zero or negative denominator yields ``0.0`` rather
    than ``inf``/``NaN``, matching the Power Query ``CalcRatios`` guard.

    Args:
        num: The numerator series.
        den: The denominator series, aligned to ``num``.

    Returns:
        A float ``pd.Series`` aligned to ``num.index`` holding ``num / den``
        where ``den > 0`` and ``0.0`` elsewhere.
    """
    # numpy.where evaluates both branches, so the division is wrapped in an
    # errstate that silences the harmless divide-by-zero warning the masked-out
    # quotient would otherwise emit.
    numerator = num.to_numpy()
    denominator = den.to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = np.where(denominator > 0, numerator / denominator, 0.0)
    return pd.Series(quotient, index=num.index, dtype="float64")


def build_rate_impacts(
    aop_vs_le: pd.DataFrame,
    sku_lu: pd.DataFrame,
) -> pd.DataFrame:
    """Compute the rate-impact decomposition for normal lines (research §4.9).

    Filters ``aop_vs_le`` to ``Classification == "normal"``, melts the ``AOP``,
    ``LE``, and ``Diff`` scenarios into a long Scenario/Value shape, and stacks
    ``{Attribute, Scenario}`` into wide ``"Attribute - Scenario"`` columns.

    The per-unit (``Net Rev Per Lb``, ``Gross Sales Per Lb``) and %GS
    (``OI %GS``, ``Trade %GS``, ``Non-Trade %GS``) AOP/LE/Diff metrics are
    recomputed at the ``{Customer, SKU #}`` grain from the additive
    dollar/volume wide columns (``Net-Revenue $``, ``Lbs``, ``Gross Sales``,
    ``Off Invoice $``, ``Trade Spend $``, ``Non-Trade $`` per scenario) rather
    than read from the carried/summed ratio columns. ``stack_pivot`` aggregates
    with ``aggfunc="sum"``, and summing a ratio across split sub-rows is
    mathematically invalid: when a SKU's gross-to-net line items split across
    more than one fine-grain group (for example a deduction sub-row carrying
    dollars with zero volume) the carried summed ratio can collapse to zero
    while the dollar-derived ratio is non-zero. Recomputing from the additive
    dollars/volume keeps the rate side consistent with the mix side. The guard
    uses :func:`_guarded_div` (``den > 0`` => quotient, else ``0.0``), matching
    ``calc_ratios``/``_safe_div``.

    From the recomputed metrics it computes the six derived impact columns:

    - ``Calc Gross Price Impact on Gross`` =
      ``[Gross Sales Per Lb - Diff] * [Lbs - LE]``
    - ``Calc Gross Price Impact on Net`` =
      ``[Calc Gross Price Impact on Gross] * (1 + [OI %GS - AOP] +
      [Trade %GS - AOP] + [Non-Trade %GS - AOP])``
    - ``OI Rate Impact`` = ``[OI %GS - Diff] * [Gross Sales - LE]``
    - ``Trade Rate Impact`` = ``[Trade %GS - Diff] * [Gross Sales - LE]``
    - ``Non-Trade Rate Impact`` = ``[Non-Trade %GS - Diff] * [Gross Sales - LE]``
    - ``Calc Net Price Impact`` = ``[Net Rev Per Lb - Diff] * [Lbs - LE]``

    The result is left-joined to ``sku_lu`` on ``SKU #`` to expand the
    ``SKU Description``, ``Category``, and ``Country`` columns.

    Args:
        aop_vs_le: The classified comparison frame (``Customer``, ``SKU #``,
            ``Attribute``, ``AOP``, ``LE``, ``Diff``, ``Classification``)
            including ratio attributes for both scenarios.
        sku_lu: The SKU lookup frame ``{SKU, SKU Description, Category, Country}``.

    Returns:
        A DataFrame with one row per normal ``{Customer, SKU #}`` pair carrying
        the wide stacked columns, the six derived impact columns
        (:data:`RATE_IMPACT_COLUMNS`), and the SKU lookup enrichment columns.
    """
    # Keep only the normal lines; eliminated/new/lost lines have no meaningful
    # rate decomposition and are handled at the mix level instead.
    normal = aop_vs_le[aop_vs_le["Classification"] == "normal"].copy()

    # Melt the three scenario columns into long Scenario/Value rows so they can
    # be stacked with Attribute into the "Attribute - Scenario" header columns.
    melted = normal.melt(
        id_vars=["Customer", "SKU #", "Attribute", "Classification"],
        value_vars=["AOP", "LE", "Diff"],
        var_name="Scenario",
        value_name="Value",
    )

    # Stack {Attribute, Scenario} into wide columns named "<Attribute> -
    # <Scenario>"; the Classification id column is dropped before the stack so it
    # does not split the index (every row here is "normal").
    melted = melted.drop(columns=["Classification"])
    wide = stack_pivot(melted, ["Attribute", "Scenario"], "Value")

    # Recompute the per-Lb and %GS metrics at this {Customer, SKU #} grain from
    # the additive dollar/volume columns instead of trusting the carried summed
    # ratio columns. stack_pivot summed the long rows with aggfunc="sum", and a
    # summed ratio is invalid when a SKU's lines split across fine-grain groups
    # (a deduction sub-row with dollars but zero volume can drive the carried
    # Net Rev Per Lb / %GS diffs to zero). Deriving each ratio from summed
    # dollars over summed volume keeps the rate side consistent with the mix
    # side; the _guarded_div guard returns 0 for a non-positive denominator,
    # matching calc_ratios/_safe_div.
    net_rev_per_lb_aop = _guarded_div(wide["Net-Revenue $ - AOP"], wide["Lbs - AOP"])
    net_rev_per_lb_le = _guarded_div(wide["Net-Revenue $ - LE"], wide["Lbs - LE"])
    net_rev_per_lb_diff = net_rev_per_lb_le - net_rev_per_lb_aop

    gross_per_lb_aop = _guarded_div(wide["Gross Sales - AOP"], wide["Lbs - AOP"])
    gross_per_lb_le = _guarded_div(wide["Gross Sales - LE"], wide["Lbs - LE"])
    gross_per_lb_diff = gross_per_lb_le - gross_per_lb_aop

    oi_pct_aop = _guarded_div(wide["Off Invoice $ - AOP"], wide["Gross Sales - AOP"])
    oi_pct_le = _guarded_div(wide["Off Invoice $ - LE"], wide["Gross Sales - LE"])
    oi_pct_diff = oi_pct_le - oi_pct_aop

    trade_pct_aop = _guarded_div(wide["Trade Spend $ - AOP"], wide["Gross Sales - AOP"])
    trade_pct_le = _guarded_div(wide["Trade Spend $ - LE"], wide["Gross Sales - LE"])
    trade_pct_diff = trade_pct_le - trade_pct_aop

    non_trade_pct_aop = _guarded_div(
        wide["Non-Trade $ - AOP"], wide["Gross Sales - AOP"]
    )
    non_trade_pct_le = _guarded_div(wide["Non-Trade $ - LE"], wide["Gross Sales - LE"])
    non_trade_pct_diff = non_trade_pct_le - non_trade_pct_aop

    # Compute the six derived impact columns from the recomputed metrics. The six
    # formula expressions are unchanged; only their ratio inputs now come from
    # the dollar/volume recomputation above rather than the carried columns.
    # Gross price impact on gross is the per-Lb price gap applied to LE volume.
    wide["Calc Gross Price Impact on Gross"] = gross_per_lb_diff * wide["Lbs - LE"]
    # Gross price impact on net scales the gross impact by the AOP deduction
    # rates so the price move is expressed on a net-revenue basis.
    wide["Calc Gross Price Impact on Net"] = wide[
        "Calc Gross Price Impact on Gross"
    ] * (1 + oi_pct_aop + trade_pct_aop + non_trade_pct_aop)
    # Each deduction rate impact applies the rate gap to LE gross sales.
    wide["OI Rate Impact"] = oi_pct_diff * wide["Gross Sales - LE"]
    wide["Trade Rate Impact"] = trade_pct_diff * wide["Gross Sales - LE"]
    wide["Non-Trade Rate Impact"] = non_trade_pct_diff * wide["Gross Sales - LE"]
    # Net price impact is the net per-Lb gap applied to LE volume.
    wide["Calc Net Price Impact"] = net_rev_per_lb_diff * wide["Lbs - LE"]

    # Enrich with the SKU lookup on the text SKU key, expanding the descriptive
    # columns the downstream rollups group by (Category, Country).
    lookup = sku_lu.copy()
    lookup["SKU"] = lookup["SKU"].astype(str)
    wide["SKU #"] = wide["SKU #"].astype(str)
    enriched = wide.merge(lookup, how="left", left_on="SKU #", right_on="SKU")

    # The merge carries the lookup's SKU key alongside SKU #; drop it so SKU # is
    # the single key column in the result.
    return enriched.drop(columns=["SKU"])
