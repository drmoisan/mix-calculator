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

from typing import TYPE_CHECKING

from src.mix_transforms import stack_pivot

if TYPE_CHECKING:
    import pandas as pd

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


def build_rate_impacts(
    aop_vs_le: pd.DataFrame,
    sku_lu: pd.DataFrame,
) -> pd.DataFrame:
    """Compute the rate-impact decomposition for normal lines (research §4.9).

    Filters ``aop_vs_le`` to ``Classification == "normal"``, melts the ``AOP``,
    ``LE``, and ``Diff`` scenarios into a long Scenario/Value shape, stacks
    ``{Attribute, Scenario}`` into wide ``"Attribute - Scenario"`` columns, and
    computes the six derived impact columns:

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

    # Compute the six derived impact columns from the wide ratio/measure columns.
    # Gross price impact on gross is the per-Lb price gap applied to LE volume.
    wide["Calc Gross Price Impact on Gross"] = (
        wide["Gross Sales Per Lb - Diff"] * wide["Lbs - LE"]
    )
    # Gross price impact on net scales the gross impact by the AOP deduction
    # rates so the price move is expressed on a net-revenue basis.
    wide["Calc Gross Price Impact on Net"] = wide[
        "Calc Gross Price Impact on Gross"
    ] * (
        1 + wide["OI %GS - AOP"] + wide["Trade %GS - AOP"] + wide["Non-Trade %GS - AOP"]
    )
    # Each deduction rate impact applies the rate gap to LE gross sales.
    wide["OI Rate Impact"] = wide["OI %GS - Diff"] * wide["Gross Sales - LE"]
    wide["Trade Rate Impact"] = wide["Trade %GS - Diff"] * wide["Gross Sales - LE"]
    wide["Non-Trade Rate Impact"] = (
        wide["Non-Trade %GS - Diff"] * wide["Gross Sales - LE"]
    )
    # Net price impact is the net per-Lb gap applied to LE volume.
    wide["Calc Net Price Impact"] = wide["Net Rev Per Lb - Diff"] * wide["Lbs - LE"]

    # Enrich with the SKU lookup on the text SKU key, expanding the descriptive
    # columns the downstream rollups group by (Category, Country).
    lookup = sku_lu.copy()
    lookup["SKU"] = lookup["SKU"].astype(str)
    wide["SKU #"] = wide["SKU #"].astype(str)
    enriched = wide.merge(lookup, how="left", left_on="SKU #", right_on="SKU")

    # The merge carries the lookup's SKU key alongside SKU #; drop it so SKU # is
    # the single key column in the result.
    return enriched.drop(columns=["SKU"])
