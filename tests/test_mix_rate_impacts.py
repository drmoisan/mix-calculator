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
_NORMAL_ATTRS: dict[str, tuple[float, float]] = {
    # attribute: (AOP, LE)
    "Gross Sales Per Lb": (10.0, 11.0),
    "Lbs": (8.0, 10.0),
    "Gross Sales": (80.0, 110.0),
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
