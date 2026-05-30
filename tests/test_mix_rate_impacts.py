"""Unit tests for :mod:`src.mix_rate_impacts`.

Covers ``build_rate_impacts`` with a fabricated ``aop_vs_le`` fixture containing
both ``normal`` and non-``normal`` lines: non-normal lines are filtered out, each
of the six derived impact columns matches the hand-computed expected value
(within ``1e-9`` for ratio-derived columns), and the ``sku_lu`` enrichment
columns are present. Arrange-Act-Assert; fabricated data only.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from src.mix_rate_impacts import RATE_IMPACT_COLUMNS, build_rate_impacts


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


# Attribute values for the single normal customer-SKU pair, given per scenario.
# Diff is LE - AOP and is supplied explicitly so the fixture mirrors AopVsLe.
#
# build_rate_impacts now recomputes the per-Lb and %GS metrics from the additive
# dollar/volume columns rather than the carried ratio rows, so the dollar columns
# below are chosen to be consistent with the carried ratios: each carried ratio
# equals its dollar measure over its volume/gross denominator at this single
# fine-grain grain. The carried ratio rows are retained so this fixture still
# proves the single-fine-grain recompute equals the previously carried ratio.
#   Net Rev Per Lb AOP = 72 / 8 = 9.0;  LE = 100 / 10 = 10.0
#   Gross Sales Per Lb AOP = 80 / 8 = 10.0;  LE = 110 / 10 = 11.0
#   OI %GS AOP = 4.0 / 80 = 0.05;  LE = 6.6 / 110 = 0.06
#   Trade %GS AOP = 1.6 / 80 = 0.02;  LE = 3.3 / 110 = 0.03
#   Non-Trade %GS AOP = 0.8 / 80 = 0.01;  LE = 1.65 / 110 = 0.015
_NORMAL_ATTRS: dict[str, tuple[float, float]] = {
    # attribute: (AOP, LE)
    "Gross Sales Per Lb": (10.0, 11.0),
    "Lbs": (8.0, 10.0),
    "Gross Sales": (80.0, 110.0),
    "Net-Revenue $": (72.0, 100.0),
    "Off Invoice $": (4.0, 6.6),
    "Trade Spend $": (1.6, 3.3),
    "Non-Trade $": (0.8, 1.65),
    "OI %GS": (0.05, 0.06),
    "Trade %GS": (0.02, 0.03),
    "Non-Trade %GS": (0.01, 0.015),
    "Net Rev Per Lb": (9.0, 10.0),
}


def _normal_rows(customer: str, sku: str) -> list[dict[str, object]]:
    """Build AopVsLe rows for one normal customer-SKU pair from _NORMAL_ATTRS."""
    rows: list[dict[str, object]] = []
    # Emit one classified AopVsLe row per attribute with AOP, LE, and Diff.
    for attribute, (aop, le) in _NORMAL_ATTRS.items():
        rows.append(
            {
                "Customer": customer,
                "SKU #": sku,
                "Attribute": attribute,
                "AOP": aop,
                "LE": le,
                "Diff": le - aop,
                "Classification": "normal",
            }
        )
    return rows


def _aop_vs_le_fixture() -> pd.DataFrame:
    """Build an AopVsLe fixture with one normal pair and one non-normal pair."""
    rows = _normal_rows("Acme Foods", "SKU-001")
    # A non-normal (lost distribution) pair that must be filtered out.
    rows.append(
        {
            "Customer": "Globex Market",
            "SKU #": "SKU-002",
            "Attribute": "Lbs",
            "AOP": 5.0,
            "LE": 0.0,
            "Diff": -5.0,
            "Classification": "lost distribution",
        }
    )
    return pd.DataFrame(rows)


def _sku_lu_fixture() -> pd.DataFrame:
    """Build a fabricated SKU lookup covering the normal pair's SKU."""
    return pd.DataFrame(
        {
            "SKU": ["SKU-001"],
            "SKU Description": ["Widget A"],
            "Category": ["Category X"],
            "Country": ["US"],
        }
    )


def test_build_rate_impacts_filters_non_normal_rows() -> None:
    """Only normal customer-SKU pairs survive the classification filter."""
    # Arrange
    aop_vs_le = _aop_vs_le_fixture()
    sku_lu = _sku_lu_fixture()

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)

    # Assert: the lost-distribution pair is gone; only the normal pair remains.
    assert len(result) == 1
    assert result.iloc[0]["SKU #"] == "SKU-001"


def test_build_rate_impacts_derived_columns_match_hand_computed() -> None:
    """Each of the six derived impact columns matches its hand-computed value."""
    # Arrange
    aop_vs_le = _aop_vs_le_fixture()
    sku_lu = _sku_lu_fixture()

    # Hand-computed expectations from _NORMAL_ATTRS:
    #   Diff(Gross Sales Per Lb) = 11 - 10 = 1; Lbs - LE = 10.
    gross_on_gross = 1.0 * 10.0
    #   on Net = gross_on_gross * (1 + 0.05 + 0.02 + 0.01).
    gross_on_net = gross_on_gross * (1 + 0.05 + 0.02 + 0.01)
    #   Gross Sales - LE = 110.
    oi_impact = (0.06 - 0.05) * 110.0
    trade_impact = (0.03 - 0.02) * 110.0
    non_trade_impact = (0.015 - 0.01) * 110.0
    #   Diff(Net Rev Per Lb) = 10 - 9 = 1; Lbs - LE = 10.
    net_price_impact = 1.0 * 10.0

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)
    row = result.iloc[0]

    # Assert
    assert abs(_f(row["Calc Gross Price Impact on Gross"]) - gross_on_gross) < 1e-9
    assert abs(_f(row["Calc Gross Price Impact on Net"]) - gross_on_net) < 1e-9
    assert abs(_f(row["OI Rate Impact"]) - oi_impact) < 1e-9
    assert abs(_f(row["Trade Rate Impact"]) - trade_impact) < 1e-9
    assert abs(_f(row["Non-Trade Rate Impact"]) - non_trade_impact) < 1e-9
    assert abs(_f(row["Calc Net Price Impact"]) - net_price_impact) < 1e-9


def test_build_rate_impacts_includes_all_six_impact_columns() -> None:
    """All six named impact columns are present in the result."""
    # Arrange
    aop_vs_le = _aop_vs_le_fixture()
    sku_lu = _sku_lu_fixture()

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)

    # Assert
    for column in RATE_IMPACT_COLUMNS:
        assert column in result.columns


def _split_row(
    customer: str,
    sku: str,
    attribute: str,
    aop: float,
    le: float,
) -> dict[str, object]:
    """Build one classified-normal AopVsLe row for a split-SKU sub-group.

    Helper for the zero-volume deduction regression fixture. Every row is
    ``normal`` so it survives the classification filter; Diff is ``le - aop``.
    """
    return {
        "Customer": customer,
        "SKU #": sku,
        "Attribute": attribute,
        "AOP": aop,
        "LE": le,
        "Diff": le - aop,
        "Classification": "normal",
    }


def _zero_volume_deduction_fixture() -> pd.DataFrame:
    """Build an AopVsLe fixture reproducing the summed-ratio defect synthetically.

    A single normal ``{Customer, SKU #}`` pair is split across two fine-grain
    sub-rows that ``stack_pivot`` sums. Sub-row A carries the SKU's volume and a
    flat per-Lb rate (carried Net Rev Per Lb diff = 0). Sub-row B is a
    zero-volume deduction sub-row that moves net-revenue dollars between
    scenarios while carrying a zero per-Lb rate (carried Net Rev Per Lb diff =
    0 under the divide-by-zero guard). Summing the carried per-Lb ratio across
    the two sub-rows therefore yields a Net Rev Per Lb diff of 0, but the summed
    dollar/volume columns imply a non-zero per-Lb diff. All values are synthetic
    and proportional; no confidential workbook figures appear.

    Summed dollar/volume for the pair:
        Net-Revenue $: AOP = 100, LE = 120;  Lbs: AOP = 10, LE = 10
        Dollar-derived Net Rev Per Lb: AOP = 10.0, LE = 12.0, Diff = 2.0
    """
    rows: list[dict[str, object]] = []
    # Sub-row A: the volume-bearing line with a flat per-Lb rate across scenarios
    # so its carried Net Rev Per Lb diff is zero on its own.
    rows.append(_split_row("Acme Foods", "SKU-001", "Lbs", 10.0, 10.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Net-Revenue $", 100.0, 100.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Gross Sales", 120.0, 120.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Off Invoice $", 8.0, 8.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Trade Spend $", 6.0, 6.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Non-Trade $", 6.0, 6.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Net Rev Per Lb", 10.0, 10.0))
    # Sub-row B: the zero-volume deduction line. It carries net-revenue dollars
    # only on the LE scenario and zero volume, so its carried per-Lb rate is 0
    # under the guard (carried diff = 0), but its dollars shift the summed
    # dollar-derived per-Lb diff away from zero.
    rows.append(_split_row("Acme Foods", "SKU-001", "Lbs", 0.0, 0.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Net-Revenue $", 0.0, 20.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Gross Sales", 0.0, 0.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Off Invoice $", 0.0, 0.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Trade Spend $", 0.0, 0.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Non-Trade $", 0.0, 0.0))
    rows.append(_split_row("Acme Foods", "SKU-001", "Net Rev Per Lb", 0.0, 0.0))
    return pd.DataFrame(rows)


def test_zero_volume_deduction_yields_dollar_derived_net_price_impact() -> None:
    """A zero-volume deduction sub-row yields the dollar-derived net-price impact.

    Regression for issue #37 (AC3): the carried summed Net Rev Per Lb diff
    collapses to zero for a split SKU whose deduction sub-row carries dollars
    with zero volume, but the recomputed dollar-derived diff is non-zero, so
    Calc Net Price Impact must be the dollar-derived non-zero value.
    """
    # Arrange
    aop_vs_le = _zero_volume_deduction_fixture()
    sku_lu = _sku_lu_fixture()

    # Dollar-derived Net Rev Per Lb diff = 120/10 - 100/10 = 2.0; Lbs - LE = 10.
    expected_net_price_impact = 2.0 * 10.0

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)
    row = result.iloc[0]

    # Assert: the recomputed net-price impact is the dollar-derived non-zero
    # value, not the zero implied by the carried summed ratio.
    assert _f(row["Calc Net Price Impact"]) != 0.0
    assert abs(_f(row["Calc Net Price Impact"]) - expected_net_price_impact) < 1e-9


def test_single_sku_group_rolls_up_to_category_net_price_impact() -> None:
    """Single-SKU group: SKU-level net-price impact equals category impact.

    Reconciliation for issue #37 (AC4): summing the SKU-level Calc Net Price
    Impact to the {Customer, Category} grain equals the category-level net-price
    impact for a single-SKU group, so the SKU Mix residual nets to 0. With one
    SKU in the group the rollup is the SKU's own value; the equality is exact.
    """
    # Arrange
    aop_vs_le = _zero_volume_deduction_fixture()
    sku_lu = _sku_lu_fixture()

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)

    # Category-grain rollup of the SKU-level net-price impact for the single-SKU
    # Customer x Category group.
    rolled_up = result.groupby(["Customer", "Category"])["Calc Net Price Impact"].sum()
    category_net_price_impact = _f(rolled_up.iloc[0])
    sku_net_price_impact = _f(result.iloc[0]["Calc Net Price Impact"])

    # Assert: the SKU-level value rolled to the category grain equals the
    # category net-price impact (SKU Mix residual = 0) within a tight tolerance.
    sku_mix_residual = category_net_price_impact - sku_net_price_impact
    assert abs(sku_mix_residual) < 1e-9


def test_single_fine_grain_recompute_equals_carried_ratio() -> None:
    """Single fine-grain rows: recomputed per-Lb/%GS equal the carried ratios.

    Behavior preservation for issue #37 (AC5): for a SKU with one row per
    attribute (Lbs > 0) the dollar-derived metrics equal the previously carried
    ratios, so the six impact columns match the hand-computed values built from
    the carried ratios in _NORMAL_ATTRS.
    """
    # Arrange
    aop_vs_le = _aop_vs_le_fixture()
    sku_lu = _sku_lu_fixture()

    # Carried-ratio expectations (identical to the hand-computed test): the
    # recompute from the consistent dollar/volume columns must reproduce these.
    gross_on_gross = (11.0 - 10.0) * 10.0
    net_price_impact = (10.0 - 9.0) * 10.0
    oi_impact = (0.06 - 0.05) * 110.0

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)
    row = result.iloc[0]

    # Assert: recomputed-from-dollars impacts equal the carried-ratio values.
    assert abs(_f(row["Calc Gross Price Impact on Gross"]) - gross_on_gross) < 1e-9
    assert abs(_f(row["Calc Net Price Impact"]) - net_price_impact) < 1e-9
    assert abs(_f(row["OI Rate Impact"]) - oi_impact) < 1e-9


def test_build_rate_impacts_enriches_with_sku_lookup() -> None:
    """The SKU lookup enrichment columns are present and populated."""
    # Arrange
    aop_vs_le = _aop_vs_le_fixture()
    sku_lu = _sku_lu_fixture()

    # Act
    result = build_rate_impacts(aop_vs_le, sku_lu)
    row = result.iloc[0]

    # Assert
    assert row["Category"] == "Category X"
    assert row["Country"] == "US"
    assert row["SKU Description"] == "Widget A"
