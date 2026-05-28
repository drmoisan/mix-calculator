"""Pure-transform builders for the three BottomsUp mix tables.

Reproduces the Excel ``2-SKU-Mix-BottomsUp``, ``3-Category-Mix-BottomsUp``, and
``4-Customer-Mix-BottomsUp`` tabs as pure pandas transforms over tables the
mix-decomposition pipeline already produces (``mix_0_detail``, ``mix_base``,
``mix_1_sku``, ``mix_2_category``, ``mix_3_customer``). Each BottomsUp table
decomposes the gross-to-net mix shift at its grain into Share, Share Shift, Mix
Rate, three classification-conditional contributions, and a ``SKU Mix`` total.

Responsibilities and boundaries:
    - This module is pure: no disk, network, or database access. All reads and
      writes remain in :mod:`src.pandas_io`, owned by the orchestrator.
    - The shared derived arithmetic (Share..SKU Mix) lives in
      :mod:`src._mix_bottomsup_helpers.build_contribution_columns`; this module
      assembles each table's pass-through, join, group-aggregate, and merge inputs
      and then delegates the contribution math to that helper.

High-level flow per builder:
    1. Establish the row set (detail rows for the SKU table; a groupby-sum for the
       category and customer tables).
    2. Source ``Classification`` (joined from ``mix_base`` for the SKU table;
       re-derived from aggregated Lbs for the category and customer tables).
    3. Merge the rollup-sourced Blended Rate / Lbs Subtotal pair and ``fillna(0)``
       the unmatched groups (the rollup tables exclude zero-Lbs groups).
    4. Append the derived contribution columns and project the exact spec column
       order.

All column names, classification labels, and table names here are schema, not
secret; only the source data values are confidential and never appear here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src._mix_bottomsup_helpers import build_contribution_columns, classify_from_lbs

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "build_mix_2_sku_bottomsup",
    "build_mix_3_category_bottomsup",
    "build_mix_4_customer_bottomsup",
]

# The Blended Rate / Lbs Subtotal pair sourced from a rollup table is built by
# summing the rollup's per-Lb rate (-> Blended Rate) and Lbs (-> Lbs Subtotal)
# columns, then renaming to the BottomsUp output names. These maps drive the
# aggregate-and-rename for all three tables (the source rollup column on the left,
# the BottomsUp output column on the right).
_BLENDED_RATE_SOURCES: dict[str, str] = {
    "Net Rev Per Lb - AOP": "Blended Rate - AOP",
    "Net Rev Per Lb - LE": "Blended Rate - LE",
}
_LBS_SUBTOTAL_SOURCES: dict[str, str] = {
    "Lbs - AOP": "Lbs Subtotal - AOP",
    "Lbs - LE": "Lbs Subtotal - LE",
}

# The four rollup-sourced columns that must be fillna(0) after a left-merge, since
# the rollup tables exclude zero-Lbs groups (so new-/lost-distribution rows have no
# match and would otherwise be NaN). Excel's SUMIFS returns 0 for a no-match.
_ROLLUP_MERGE_COLUMNS: list[str] = [
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
]

# Output column orders, verbatim from the spec Data & State section. Each builder
# projects its result to one of these lists so the persisted table matches the
# Excel tab column order exactly.
_SKU_COLUMNS: list[str] = [
    "Customer",
    "SKU #",
    "SKU Description",
    "Category",
    "Country",
    "Classification",
    "Lbs - AOP",
    "Lbs - LE",
    "Net Rev Per Lb - AOP",
    "Net Rev Per Lb - LE",
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
    "Share - AOP",
    "Share - LE",
    "Share Shift",
    "Mix Rate",
    "New Contribution",
    "Disco Contribution",
    "Normal Contribution",
    "SKU Mix",
]
_CATEGORY_COLUMNS: list[str] = [
    "CustCatCountry",
    "Customer",
    "Category",
    "Country",
    "Lbs - AOP",
    "Lbs - LE",
    "Net-Revenue $ - AOP",
    "Net-Revenue $ - LE",
    "Net Rev Per Lb - AOP",
    "Net Rev Per Lb - LE",
    "Classification",
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
    "Share - AOP",
    "Share - LE",
    "Share Shift",
    "Mix Rate",
    "New Contribution",
    "Disco Contribution",
    "Normal Contribution",
    "SKU Mix",
]
_CUSTOMER_COLUMNS: list[str] = [
    "CustCountry",
    "Customer",
    "Country",
    "Lbs - AOP",
    "Lbs - LE",
    "Net-Revenue $ - AOP",
    "Net-Revenue $ - LE",
    "Net Rev Per Lb - AOP",
    "Net Rev Per Lb - LE",
    "Classification",
    "Blended Rate - AOP",
    "Blended Rate - LE",
    "Lbs Subtotal - AOP",
    "Lbs Subtotal - LE",
    "Share - AOP",
    "Share - LE",
    "Share Shift",
    "Mix Rate",
    "New Contribution",
    "Disco Contribution",
    "Normal Contribution",
    "SKU Mix",
]


def _aggregate_rollup_pair(
    rollup: pd.DataFrame,
    group_keys: list[str],
) -> pd.DataFrame:
    """Aggregate a rollup table's rate/Lbs columns into the BottomsUp merge pair.

    Sums the rollup's ``Net Rev Per Lb - AOP/LE`` (-> Blended Rate) and
    ``Lbs - AOP/LE`` (-> Lbs Subtotal) over ``group_keys`` and renames them to the
    four BottomsUp output column names. Reproduces the Excel SUMIFS over the same
    criteria columns; when the data is well-formed (one row per group, see the
    builder docstrings), the sum reduces to a single-row lookup.

    Args:
        rollup: The source rollup table (``mix_1_sku``, ``mix_2_category``, or
            ``mix_3_customer``) carrying the rate and Lbs columns.
        group_keys: The SUMIFS criteria columns to group by.

    Returns:
        A DataFrame with one row per distinct ``group_keys`` combination carrying
        the four columns ``Blended Rate - AOP/LE`` and ``Lbs Subtotal - AOP/LE``.
    """
    # Sum the source rate and Lbs columns over the SUMIFS criteria, then rename to
    # the BottomsUp output names so the merge produces the four target columns.
    value_columns = list(_BLENDED_RATE_SOURCES) + list(_LBS_SUBTOTAL_SOURCES)
    aggregated = rollup.groupby(group_keys, as_index=False)[value_columns].sum()
    return aggregated.rename(columns={**_BLENDED_RATE_SOURCES, **_LBS_SUBTOTAL_SOURCES})


def _merge_rollup_pair(
    frame: pd.DataFrame,
    rollup_pair: pd.DataFrame,
    join_keys: list[str],
) -> pd.DataFrame:
    """Left-merge the aggregated rollup pair and zero-fill the unmatched groups.

    Args:
        frame: The BottomsUp row set carrying the ``join_keys``.
        rollup_pair: The aggregated Blended Rate / Lbs Subtotal pair from
            :func:`_aggregate_rollup_pair`.
        join_keys: The merge keys (a subset of the SUMIFS criteria columns).

    Returns:
        A new DataFrame equal to ``frame`` with the four rollup columns merged on
        ``join_keys`` and ``fillna(0)`` applied so unmatched groups are ``0``, not
        ``NaN`` (Excel SUMIFS no-match parity).
    """
    merged = frame.merge(rollup_pair, on=join_keys, how="left")
    # Zero-fill the four rollup columns: new-/lost-distribution groups are excluded
    # from the rollup tables, so their left-merge produces NaN that must become 0.
    merged[_ROLLUP_MERGE_COLUMNS] = merged[_ROLLUP_MERGE_COLUMNS].fillna(0)
    return merged


def _derive_net_rev_per_lb(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive ``Net Rev Per Lb - AOP/LE`` from aggregated Net-Revenue and Lbs.

    Used by the category and customer builders, whose per-Lb rate is computed from
    the group-summed measures rather than carried from ``mix_0_detail``. Each
    division is guarded to ``0.0`` when the group's Lbs is ``0`` (Excel ``#DIV/0!``
    guard parity).

    Args:
        frame: A grouped frame carrying ``Net-Revenue $ - AOP/LE`` and
            ``Lbs - AOP/LE``. Mutated in place (the caller owns a fresh groupby
            result).

    Returns:
        The same frame with ``Net Rev Per Lb - AOP`` and ``Net Rev Per Lb - LE``
        assigned.
    """
    # Derive the per-Lb rate for both scenarios; a zero-Lbs group yields 0.0 so the
    # value is never NaN/inf (those rows are new/eliminated and the rate is unused).
    for scenario in ("AOP", "LE"):
        net_rev = frame[f"Net-Revenue $ - {scenario}"]
        lbs = frame[f"Lbs - {scenario}"]
        frame[f"Net Rev Per Lb - {scenario}"] = (
            (net_rev / lbs).where(lbs != 0, 0.0).astype("float64")
        )
    return frame


def _classify_frame_from_lbs(frame: pd.DataFrame) -> list[str]:
    """Re-derive the ``Classification`` token list from a frame's aggregated Lbs.

    Applies :func:`src._mix_bottomsup_helpers.classify_from_lbs` to the aggregated
    ``Lbs - AOP`` / ``Lbs - LE`` pair, for the category and customer builders whose
    Classification is not sourced upstream. The per-element helper keeps the
    four-branch decision logic in one place rather than duplicating the masks here.

    Args:
        frame: A grouped frame carrying ``Lbs - AOP`` and ``Lbs - LE``.

    Returns:
        A ``list[str]`` of lowercase Classification tokens in row order, suitable
        for direct assignment to a frame column.
    """
    # Extract the two Lbs columns as typed float lists so the per-element call is
    # fully typed (a DataFrame.apply lambda would be Unknown-typed under strict
    # Pyright). zip pairs the AOP/LE values row by row.
    lbs_aop: list[float] = [float(value) for value in frame["Lbs - AOP"].tolist()]
    lbs_le: list[float] = [float(value) for value in frame["Lbs - LE"].tolist()]
    # Re-derive the token for each (AOP, LE) Lbs pair via the shared zero-test.
    # strict=True asserts the two columns have equal length (they share a frame).
    return [classify_from_lbs(aop, le) for aop, le in zip(lbs_aop, lbs_le, strict=True)]


def build_mix_2_sku_bottomsup(
    mix_0_detail: pd.DataFrame,
    mix_base: pd.DataFrame,
    mix_1_sku: pd.DataFrame,
) -> pd.DataFrame:
    """Build the ``mix_2_sku_bottomsup`` table (one row per ``mix_0_detail`` row).

    Reproduces the Excel ``2-SKU-Mix-BottomsUp`` tab. Pass-through identity and
    measure columns come directly from ``mix_0_detail``. ``Classification`` is
    joined from ``mix_base`` on ``(Customer, SKU #)`` because it is dropped from
    ``mix_0_detail`` upstream. The Blended Rate / Lbs Subtotal pair is aggregated
    from ``mix_1_sku`` over the SUMIFS criteria ``(Customer, Category)`` and
    left-merged onto each detail row, then ``fillna(0)``. The derived columns are
    produced by :func:`build_contribution_columns`.

    The ``(Customer, Category)`` join omits ``Country`` to match the Excel SUMIFS
    formula. This is a single-row lookup only when each ``(Customer, Category)``
    maps to a single ``Country`` in the data; if a customer-category spans multiple
    countries the aggregation would sum rates across country rows, which is not a
    meaningful blended rate. This single-country expectation must be validated
    against production data; it is not enforced here to preserve operational
    flexibility and to avoid emitting any confidential value.

    Args:
        mix_0_detail: The row-level detail table; the BottomsUp row set and the
            source of the pass-through identity and measure columns. Not mutated.
        mix_base: The enriched mix base; source of ``Classification`` at
            ``(Customer, SKU #)`` grain. Not mutated.
        mix_1_sku: The SKU rollup; source of the Blended Rate / Lbs Subtotal pair
            aggregated over ``(Customer, Category)``. Not mutated.

    Returns:
        A DataFrame with the 22 ``mix_2_sku_bottomsup`` columns in spec order, one
        row per ``mix_0_detail`` row.
    """
    # Start from the detail pass-through columns (identity + Lbs + per-Lb rates).
    passthrough = [
        "Customer",
        "SKU #",
        "SKU Description",
        "Category",
        "Country",
        "Lbs - AOP",
        "Lbs - LE",
        "Net Rev Per Lb - AOP",
        "Net Rev Per Lb - LE",
    ]
    frame = mix_0_detail[passthrough].copy()

    # Join Classification from mix_base on (Customer, SKU #): one classification per
    # pair, recovered by dropping the duplicate attribute rows mix_base carries.
    classification_lookup = mix_base[
        ["Customer", "SKU #", "Classification"]
    ].drop_duplicates(["Customer", "SKU #", "Classification"])
    frame = frame.merge(classification_lookup, on=["Customer", "SKU #"], how="left")

    # Aggregate and merge the Blended Rate / Lbs Subtotal pair on (Customer,
    # Category), matching the Excel SUMIFS criteria, then zero-fill no-match groups.
    rollup_pair = _aggregate_rollup_pair(mix_1_sku, ["Customer", "Category"])
    frame = _merge_rollup_pair(frame, rollup_pair, ["Customer", "Category"])

    # Append the shared derived arithmetic and project the exact spec column order.
    frame = build_contribution_columns(frame)
    return frame[_SKU_COLUMNS].copy()


def build_mix_3_category_bottomsup(
    mix_0_detail: pd.DataFrame,
    mix_2_category: pd.DataFrame,
) -> pd.DataFrame:
    """Build the ``mix_3_category_bottomsup`` table (one row per ``CustCatCountry``).

    Reproduces the Excel ``3-Category-Mix-BottomsUp`` tab. The row set and the
    aggregated measures (``Lbs - AOP/LE``, ``Net-Revenue $ - AOP/LE``) are produced
    by a single groupby-sum of ``mix_0_detail`` over
    ``(CustCatCountry, Customer, Category, Country)``. ``Net Rev Per Lb - AOP/LE``
    is derived as ``Net-Revenue $ / Lbs`` (guarded to ``0``). ``Classification`` is
    re-derived from the aggregated ``Lbs - AOP/LE`` via the zero-test. The Blended
    Rate / Lbs Subtotal pair is aggregated from ``mix_2_category`` over
    ``(Customer, Country)`` (a grain match, so a single-row lookup), left-merged,
    and ``fillna(0)``. The derived columns are produced by
    :func:`build_contribution_columns`.

    Args:
        mix_0_detail: The row-level detail table; source of the group row set and
            the summed measures. Not mutated.
        mix_2_category: The category rollup; source of the Blended Rate / Lbs
            Subtotal pair aggregated over ``(Customer, Country)``. Not mutated.

    Returns:
        A DataFrame with the ``mix_3_category_bottomsup`` columns in spec order, one
        row per distinct ``CustCatCountry`` present in ``mix_0_detail``.
    """
    # Group the detail rows to the category grain, summing the four base measures.
    group_keys = ["CustCatCountry", "Customer", "Category", "Country"]
    measures = ["Lbs - AOP", "Lbs - LE", "Net-Revenue $ - AOP", "Net-Revenue $ - LE"]
    frame = mix_0_detail.groupby(group_keys, as_index=False)[measures].sum()

    # Derive the per-Lb rate and re-derive Classification from the aggregated Lbs.
    frame = _derive_net_rev_per_lb(frame)
    frame["Classification"] = _classify_frame_from_lbs(frame)

    # Aggregate and merge the Blended Rate / Lbs Subtotal pair on (Customer,
    # Country), then zero-fill no-match groups, and append the derived arithmetic.
    rollup_pair = _aggregate_rollup_pair(mix_2_category, ["Customer", "Country"])
    frame = _merge_rollup_pair(frame, rollup_pair, ["Customer", "Country"])
    frame = build_contribution_columns(frame)
    return frame[_CATEGORY_COLUMNS].copy()


def build_mix_4_customer_bottomsup(
    mix_0_detail: pd.DataFrame,
    mix_3_customer: pd.DataFrame,
) -> pd.DataFrame:
    """Build the ``mix_4_customer_bottomsup`` table (one row per ``CustCountry``).

    Reproduces the Excel ``4-Customer-Mix-BottomsUp`` tab. Same structure as the
    category builder, grouped over ``(CustCountry, Customer, Country)``. The Blended
    Rate / Lbs Subtotal pair is aggregated from ``mix_3_customer`` over ``(Country)``
    (a grain match, so a single-row lookup), left-merged on ``Country``, and
    ``fillna(0)``. ``Classification`` is re-derived from the aggregated
    ``Lbs - AOP/LE``. The derived columns are produced by
    :func:`build_contribution_columns`.

    Args:
        mix_0_detail: The row-level detail table; source of the group row set and
            the summed measures. Not mutated.
        mix_3_customer: The customer rollup; source of the Blended Rate / Lbs
            Subtotal pair aggregated over ``(Country)``. Not mutated.

    Returns:
        A DataFrame with the ``mix_4_customer_bottomsup`` columns in spec order, one
        row per distinct ``CustCountry`` present in ``mix_0_detail``.
    """
    # Group the detail rows to the customer grain, summing the four base measures.
    group_keys = ["CustCountry", "Customer", "Country"]
    measures = ["Lbs - AOP", "Lbs - LE", "Net-Revenue $ - AOP", "Net-Revenue $ - LE"]
    frame = mix_0_detail.groupby(group_keys, as_index=False)[measures].sum()

    # Derive the per-Lb rate and re-derive Classification from the aggregated Lbs.
    frame = _derive_net_rev_per_lb(frame)
    frame["Classification"] = _classify_frame_from_lbs(frame)

    # Aggregate and merge the Blended Rate / Lbs Subtotal pair on (Country), then
    # zero-fill no-match groups, and append the shared derived arithmetic.
    rollup_pair = _aggregate_rollup_pair(mix_3_customer, ["Country"])
    frame = _merge_rollup_pair(frame, rollup_pair, ["Country"])
    frame = build_contribution_columns(frame)
    return frame[_CUSTOMER_COLUMNS].copy()
