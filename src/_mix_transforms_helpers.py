"""Pure ratio/classification/stack primitives for :mod:`src.mix_transforms`.

This module holds the lower-level, side-effect-free pandas primitives that
reproduce the Power Query helper functions, so that :mod:`src.mix_transforms`
stays under the 500-line file limit. It depends only on ``numpy`` and ``pandas``
and imports nothing from :mod:`src.mix_transforms`, so the higher-level pivot
functions can import these primitives without an import cycle. The pivot
functions and the public re-exports live in :mod:`src.mix_transforms`.

Primitives provided:
    - ``negate_column``: multiply one column by ``-1`` (the M ``NegateColumn``).
    - ``calc_ratios``: append the eight per-Lb and %GS ratio columns with
      divide-by-zero guards (the M ``CalcRatios``).
    - ``classify_table``: two-level SKU and customer-SKU classification with
      exact zero tests (the M ``ClassifyTable``).
    - ``stack_pivot``: join columns into a header and pivot it (the M
      ``StackPivot``).
    - ``add_ratios``: append per-scenario ratio rows without duplicating
      originals (the M ``AddRatios``).
    - ``fill_zero_with_avg``: replace zero ``Net Rev Per Lb`` with the cross-row
      average rate (the M ``FillZeroWithAvg``).

All column names, classification labels, and measure names here are schema, not
secret; only the source data values are confidential and never appear here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# The eight ratio columns appended by ``calc_ratios``, mapped to their
# (numerator, denominator) source columns. The first five divide by ``Lbs``;
# the last three divide by ``Gross Sales``. Each ratio is guarded to return 0
# when its denominator is not strictly positive (the M ``CalcRatios`` semantics).
RATIO_SPECS: list[tuple[str, str, str]] = [
    ("Gross Sales Per Lb", "Gross Sales", "Lbs"),
    ("OI Per Lb", "Off Invoice $", "Lbs"),
    ("Trade Per Lb", "Trade Spend $", "Lbs"),
    ("Non-Trade Per Lb", "Non-Trade $", "Lbs"),
    ("Net Rev Per Lb", "Net-Revenue $", "Lbs"),
    ("OI %GS", "Off Invoice $", "Gross Sales"),
    ("Trade %GS", "Trade Spend $", "Gross Sales"),
    ("Non-Trade %GS", "Non-Trade $", "Gross Sales"),
]

# Deduction columns negated after pivot so downstream sums add them to Gross
# Sales (the source records deductions as positive values).
NEGATED_COLUMNS: list[str] = ["Off Invoice $", "Trade Spend $", "Non-Trade $"]


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    """Divide two series element-wise, returning 0 where the denominator <= 0.

    Reproduces the Power Query ``CalcRatios`` guard: a ratio is computed only
    when its denominator is strictly positive; otherwise it is 0. ``numpy.where``
    keeps the operation vectorized and avoids divide-by-zero warnings.

    Args:
        num: The numerator series.
        den: The denominator series, aligned to ``num``.

    Returns:
        A float ``pd.Series`` aligned to ``num.index`` holding ``num / den``
        where ``den > 0`` and ``0.0`` elsewhere.
    """
    # Compute the quotient under a positive-denominator mask so a zero or
    # negative denominator yields 0.0 rather than inf/NaN, matching the M guard.
    # numpy.where evaluates both branches, so the division is wrapped in an
    # errstate that silences the harmless divide-by-zero warning the masked-out
    # quotient would otherwise emit.
    numerator = num.to_numpy()
    denominator = den.to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = np.where(denominator > 0, numerator / denominator, 0.0)
    return pd.Series(quotient, index=num.index, dtype="float64")


def negate_column(table: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """Return a copy of ``table`` with ``column_name`` multiplied by ``-1``.

    Reproduces the Power Query ``NegateColumn`` helper. The input is not mutated;
    a copy is returned so callers can chain negations without side effects.

    Args:
        table: The source frame containing ``column_name``.
        column_name: The numeric column to negate.

    Returns:
        A new DataFrame identical to ``table`` except that ``column_name`` is
        negated.
    """
    result = table.copy()
    result[column_name] = result[column_name] * -1
    return result


def calc_ratios(input_table: pd.DataFrame) -> pd.DataFrame:
    """Append the eight per-Lb and %GS ratio columns with zero-denominator guards.

    Reproduces the Power Query ``CalcRatios`` helper. Each ratio divides a named
    measure by either ``Lbs`` or ``Gross Sales`` and returns 0 when that
    denominator is not strictly positive. A measure column absent from the input
    is treated as all-zero (so the dependent ratio is 0), matching the M behavior
    where a missing measure contributes nothing; the later rollup stages carry
    only ``Lbs``, ``Net Rev Per Lb``, and ``Net-Revenue $``, so the per-Lb and
    %GS ratios for the absent measures resolve to 0 while ``Net Rev Per Lb``
    stays exact.

    Args:
        input_table: A wide frame with at least the ``Lbs`` and ``Net-Revenue $``
            measure columns present; any other measure column may be absent.

    Returns:
        A new DataFrame equal to ``input_table`` with the eight ratio columns
        appended in their canonical order.
    """
    result = input_table.copy()

    # Append each guarded ratio in canonical order; the spec table pairs every
    # output ratio with its numerator and denominator measure columns. A measure
    # column absent from the frame is read as an all-zero series so the dependent
    # ratio resolves to 0 rather than raising on the missing column.
    zero_series = pd.Series(0.0, index=result.index, dtype="float64")
    for output_name, numerator, denominator in RATIO_SPECS:
        num = result[numerator] if numerator in result.columns else zero_series
        den = result[denominator] if denominator in result.columns else zero_series
        result[output_name] = _safe_div(num, den)
    return result


def _sku_level_label(aop_total: float, le_total: float) -> str:
    """Classify a SKU from its summed AOP and LE Lbs totals (exact zero tests).

    Implements the level-1 branch of the Power Query ``ClassifyTable`` logic.
    Zero is tested exactly (no float tolerance) to match the M ``= 0`` / ``<> 0``
    comparisons.

    Args:
        aop_total: Sum of AOP ``Lbs`` across all customers for the SKU.
        le_total: Sum of LE ``Lbs`` across all customers for the SKU.

    Returns:
        One of ``"inactive"`` (both zero), ``"eliminated"`` (AOP nonzero, LE
        zero), ``"new"`` (AOP zero, LE nonzero), or ``"exists"`` (both nonzero).
    """
    # Branch on the zero/nonzero state of each scenario total. The order is
    # exhaustive over the four combinations; "exists" is the only state that
    # defers to the customer-SKU level below.
    if aop_total == 0 and le_total == 0:
        return "inactive"
    if aop_total != 0 and le_total == 0:
        return "eliminated"
    if aop_total == 0 and le_total != 0:
        return "new"
    return "exists"


def _cust_sku_label(aop_val: float, le_val: float) -> str:
    """Classify a customer-SKU pair from its single AOP and LE Lbs values.

    Implements the level-2 branch of the Power Query ``ClassifyTable`` logic for
    SKUs whose level-1 classification is ``"exists"``. Zero is tested exactly.

    Args:
        aop_val: The AOP ``Lbs`` value for this customer-SKU pair.
        le_val: The LE ``Lbs`` value for this customer-SKU pair.

    Returns:
        One of ``"inactive"``, ``"normal"``, ``"lost distribution"``, or
        ``"new distribution"``.
    """
    # Branch on the zero/nonzero state of each scenario value; the four cases are
    # exhaustive and mirror the M customer-SKU classification table.
    if aop_val == 0 and le_val == 0:
        return "inactive"
    if aop_val != 0 and le_val != 0:
        return "normal"
    if aop_val != 0 and le_val == 0:
        return "lost distribution"
    return "new distribution"


def classify_table(input_table: pd.DataFrame) -> pd.DataFrame:
    """Append a two-level ``Classification`` column using exact zero tests.

    Reproduces the Power Query ``ClassifyTable`` helper over an ``AopVsLe`` frame
    (columns ``Customer``, ``SKU #``, ``Attribute``, ``AOP``, ``LE``, ``Diff``).
    Level 1 classifies each SKU from its summed ``Lbs`` totals across customers;
    level 2 refines ``"exists"`` SKUs from the single ``Lbs`` value of each
    customer-SKU pair. All zero tests are exact (no tolerance) to match the M
    source.

    Args:
        input_table: An ``AopVsLe`` frame with ``Customer``, ``SKU #``,
            ``Attribute``, ``AOP``, and ``LE`` columns.

    Returns:
        A new DataFrame equal to ``input_table`` with a ``Classification`` column
        appended for every row (every Attribute row of a customer-SKU pair shares
        the pair's classification).
    """
    result = input_table.copy()

    # Level 1: per-SKU totals over the Lbs rows only, summed across customers.
    lbs_rows = result[result["Attribute"] == "Lbs"]
    sku_aop_total = lbs_rows.groupby("SKU #")["AOP"].sum()
    sku_le_total = lbs_rows.groupby("SKU #")["LE"].sum()
    sku_label: dict[object, str] = {}
    # Walk every SKU present in the Lbs rows and assign its level-1 label.
    for sku in sku_aop_total.index:
        sku_label[sku] = _sku_level_label(
            float(sku_aop_total.loc[sku]), float(sku_le_total.loc[sku])
        )

    # Level 2: per customer-SKU Lbs value, used only when level 1 is "exists".
    # Extract the four aligned columns as plain lists so the per-pair loop works
    # on typed values rather than an untyped iterrows() unpacking.
    pair_customers: list[object] = lbs_rows["Customer"].tolist()
    pair_skus: list[object] = lbs_rows["SKU #"].tolist()
    pair_aops: list[float] = [float(value) for value in lbs_rows["AOP"].tolist()]
    pair_les: list[float] = [float(value) for value in lbs_rows["LE"].tolist()]
    pair_label: dict[tuple[object, object], str] = {}
    # Walk every customer-SKU Lbs row; "exists" SKUs are refined, all other SKU
    # labels pass straight through as the pair classification.
    for index, customer in enumerate(pair_customers):
        sku = pair_skus[index]
        level1 = sku_label.get(sku, "inactive")
        if level1 != "exists":
            pair_label[customer, sku] = level1
        else:
            pair_label[customer, sku] = _cust_sku_label(
                pair_aops[index], pair_les[index]
            )

    # Broadcast each pair's classification to every Attribute row of that pair by
    # mapping the row-aligned (Customer, SKU #) keys; a missing pair is inactive.
    row_customers: list[object] = result["Customer"].tolist()
    row_skus: list[object] = result["SKU #"].tolist()
    classifications = [
        pair_label.get((row_customers[index], row_skus[index]), "inactive")
        for index in range(len(result))
    ]
    result["Classification"] = classifications
    return result


def stack_pivot(
    input_table: pd.DataFrame,
    columns_to_stack: list[str],
    value_column: str,
) -> pd.DataFrame:
    """Join ``columns_to_stack`` into a header and pivot it against ``value_column``.

    Reproduces the Power Query ``StackPivot`` helper. For each row a header
    string is built by joining the stacked column values with ``" - "`` (for
    example ``"Lbs - AOP"``); the stacked columns are dropped, and the header is
    pivoted against ``value_column`` with sum aggregation. The remaining columns
    form the pivot index. Missing cells are filled with 0.

    Args:
        input_table: The long-format source frame.
        columns_to_stack: The columns whose values are joined into the header
            (for example ``["Attribute", "Scenario"]``).
        value_column: The column whose values populate the pivot cells.

    Returns:
        A wide DataFrame indexed by the non-stacked, non-value columns with one
        column per distinct header string, each filled with the summed value.
    """
    working = input_table.copy()

    # Build the header by joining the stacked column values with " - "; this is
    # the new pivot column name source (for example "Lbs - AOP"). Each stacked
    # column is read as a plain list of strings so the per-row join is typed.
    stacked_lists: list[list[str]] = [
        [str(value) for value in working[column].tolist()]
        for column in columns_to_stack
    ]
    headers = [" - ".join(parts) for parts in zip(*stacked_lists, strict=True)]
    working["_header"] = headers

    # Identity columns are everything that is neither stacked, the value, nor the
    # synthetic header; they become the pivot index.
    id_cols = [
        column
        for column in working.columns
        if column not in [*columns_to_stack, value_column, "_header"]
    ]
    result = working.pivot_table(
        index=id_cols,
        columns="_header",
        values=value_column,
        aggfunc="sum",
    ).reset_index()
    result.columns.name = None
    return result.fillna(0)


def add_ratios(
    input_table: pd.DataFrame,
    scenarios_to_process: list[str],
) -> pd.DataFrame:
    """Append per-scenario ratio rows to a long table without duplicating originals.

    Reproduces the Power Query ``AddRatios`` helper. For each scenario the long
    rows are pivoted ``Attribute`` -> ``Value``, ``calc_ratios`` adds the eight
    ratio columns, and the frame is melted back to long form keeping only the
    newly added ratio attributes. The per-scenario ratio rows are concatenated
    onto the original input; original rows are never duplicated.

    Args:
        input_table: A long frame with ``Attribute``, ``Value``, and ``Scenario``
            columns plus any number of identity columns.
        scenarios_to_process: The scenario labels to compute ratios for (for
            example ``["AOP", "LE"]``).

    Returns:
        A new DataFrame equal to ``input_table`` with the computed ratio rows
        appended for each requested scenario.
    """
    original_attributes = set(input_table["Attribute"].unique())
    id_cols = [
        column for column in input_table.columns if column not in ("Attribute", "Value")
    ]
    ratio_frames: list[pd.DataFrame] = []

    # Compute ratio rows scenario by scenario so each scenario's wide pivot only
    # mixes attributes from a single scenario before calc_ratios runs.
    for scenario in scenarios_to_process:
        scenario_rows = input_table[input_table["Scenario"] == scenario]
        if scenario_rows.empty:
            continue
        wide = scenario_rows.pivot_table(
            index=id_cols,
            columns="Attribute",
            values="Value",
            aggfunc="sum",
        ).reset_index()
        wide.columns.name = None
        wide = calc_ratios(wide)

        # Melt back to long form; keep only the attributes that did not exist in
        # the input so the result is purely the appended ratio rows.
        melted = wide.melt(id_vars=id_cols, var_name="Attribute", value_name="Value")
        new_rows = melted[~melted["Attribute"].isin(original_attributes)].copy()
        ratio_frames.append(new_rows)

    if not ratio_frames:
        return input_table.copy()

    appended = pd.concat([input_table, *ratio_frames], ignore_index=True)
    return appended


def fill_zero_with_avg(
    input_table: pd.DataFrame,
    lbs_col: str,
    net_rev_col: str,
    net_rev_per_lb_col: str,
) -> pd.DataFrame:
    """Replace zero ``Net Rev Per Lb`` values with the cross-row average rate.

    Reproduces the Power Query ``FillZeroWithAvg`` helper. The cross-row average
    rate is ``sum(net_rev_col) / sum(lbs_col)`` (0 when the Lbs sum is not
    positive); every zero in ``net_rev_per_lb_col`` is replaced with that
    average. Used in the customer and country rollups so zero rates on new or
    lost-distribution lines do not distort the decomposition.

    Args:
        input_table: The frame containing the three named columns.
        lbs_col: The Lbs column whose sum is the average denominator.
        net_rev_col: The net-revenue column whose sum is the average numerator.
        net_rev_per_lb_col: The per-Lb rate column whose zeros are replaced.

    Returns:
        A new DataFrame equal to ``input_table`` with zeros in
        ``net_rev_per_lb_col`` replaced by the computed average rate.
    """
    result = input_table.copy()
    lbs_sum = float(result[lbs_col].sum())
    net_rev_sum = float(result[net_rev_col].sum())

    # Guard the average against a non-positive Lbs sum so an empty or all-zero
    # group yields 0 rather than a divide-by-zero, matching the M guard.
    average = net_rev_sum / lbs_sum if lbs_sum > 0 else 0.0
    result[net_rev_per_lb_col] = result[net_rev_per_lb_col].replace(0, average)
    return result
