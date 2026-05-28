"""Unit tests for the mix rollup chain in :mod:`src.mix_rollups`.

Covers the rollup chain with a fabricated ``mix_base``/``rate_impacts`` fixture:
``build_mix_rollup_1..3`` grouping, ``build_mix_rollup_4`` scalar sum,
``build_mix_1_sku``/``build_mix_2_category``/``build_mix_3_customer``/
``build_mix_4_country`` mix columns, the ``fill_zero_with_avg`` application in
the customer and country layers, ``build_mix_0_detail`` composite keys, and the
rollup tie-out. Arrange-Act-Assert; fabricated data only.
"""

from __future__ import annotations

import pandas as pd

from src._mix_rollups_helpers import build_mix_stage
from src.mix_rollups import (
    build_mix_0_detail,
    build_mix_1_sku,
    build_mix_2_category,
    build_mix_3_customer,
    build_mix_4_country,
    build_mix_rollup_1,
    build_mix_rollup_2,
    build_mix_rollup_3,
    build_mix_rollup_4,
)
from tests._mix_rollups_fixtures import _f, _mix_base_fixture, _rate_impacts_fixture

# ---------------------------------------------------------------------------
# Rollups (group-and-sum lookups)
# ---------------------------------------------------------------------------


def test_build_mix_rollup_1_groups_by_customer_country_category() -> None:
    """Mix-Rollup-1 sums net price impact per Customer/Country/Category."""
    # Arrange
    rate_impacts = _rate_impacts_fixture()

    # Act
    result = build_mix_rollup_1(rate_impacts)

    # Assert: three distinct groups, sums preserved.
    assert len(result) == 3
    acme_x = result[
        (result["Customer"] == "Acme Foods") & (result["Category"] == "Category X")
    ]
    assert _f(acme_x.iloc[0]["Calc Net Price Impact"]) == 12.0


def test_build_mix_rollup_4_returns_scalar_sum() -> None:
    """Mix-Rollup-4 returns the float total of the customer layer impact."""
    # Arrange: a minimal customer layer with a known impact total.
    mix_3 = pd.DataFrame({"Calc Net Price Impact": [3.0, 4.0, -1.0]})

    # Act
    result = build_mix_rollup_4(mix_3)

    # Assert
    assert isinstance(result, float)
    assert result == 6.0


# ---------------------------------------------------------------------------
# Mix layers
# ---------------------------------------------------------------------------


def test_build_mix_1_sku_produces_sku_mix_column() -> None:
    """Mix-1-SKu produces a SKU Mix column and a net price impact."""
    # Arrange
    mix_base = _mix_base_fixture()
    rollup_1 = build_mix_rollup_1(_rate_impacts_fixture())

    # Act
    result = build_mix_1_sku(mix_base, rollup_1)

    # Assert
    assert "SKU Mix" in result.columns
    assert "Calc Net Price Impact" in result.columns
    assert len(result) > 0


def test_full_mix_chain_columns_and_fill_zero() -> None:
    """The chain produces each mix column and applies fill_zero in later layers."""
    # Arrange
    mix_base = _mix_base_fixture()
    rollup_1 = build_mix_rollup_1(_rate_impacts_fixture())

    # Act: run the full chain end to end. The coarser layers aggregate the
    # unfiltered mix_base at their own granularity (issue #20); the rollup
    # targets remain the prior finer layer.
    mix_1 = build_mix_1_sku(mix_base, rollup_1)
    rollup_2 = build_mix_rollup_2(mix_1)
    mix_2 = build_mix_2_category(mix_base, rollup_2)
    rollup_3 = build_mix_rollup_3(mix_2)
    mix_3 = build_mix_3_customer(mix_base, rollup_3)
    rollup_4 = build_mix_rollup_4(mix_3)
    mix_4 = build_mix_4_country(mix_base, rollup_4)

    # Assert: each layer carries its named mix column.
    assert "Category Mix" in mix_2.columns
    assert "Customer Mix" in mix_3.columns
    assert "Country Mix" in mix_4.columns
    # The customer/country layers carry the zero-filled net rate columns.
    assert "Net Rev Per Lb - AOP" in mix_3.columns
    assert "Net Rev Per Lb - LE" in mix_3.columns


def test_mix_4_country_subtracts_scalar_rollup_4() -> None:
    """Mix-4-Country's Country Mix equals its impact minus the scalar rollup."""
    # Arrange: run the chain to the country layer. The coarser layers source the
    # unfiltered mix_base at their own granularity (issue #20).
    mix_base = _mix_base_fixture()
    rollup_1 = build_mix_rollup_1(_rate_impacts_fixture())
    mix_1 = build_mix_1_sku(mix_base, rollup_1)
    rollup_2 = build_mix_rollup_2(mix_1)
    mix_2 = build_mix_2_category(mix_base, rollup_2)
    rollup_3 = build_mix_rollup_3(mix_2)
    mix_3 = build_mix_3_customer(mix_base, rollup_3)
    rollup_4 = build_mix_rollup_4(mix_3)

    # Act
    mix_4 = build_mix_4_country(mix_base, rollup_4)

    # Assert: Country Mix = Calc Net Price Impact - scalar rollup_4 per row.
    for _, row in mix_4.iterrows():
        expected = _f(row["Calc Net Price Impact"]) - rollup_4
        assert abs(_f(row["Country Mix"]) - expected) < 1e-9


def test_build_mix_0_detail_composite_keys() -> None:
    """Mix-0-Detail produces the three composite key columns."""
    # Arrange
    mix_base = _mix_base_fixture()

    # Act
    result = build_mix_0_detail(mix_base)

    # Assert
    for column in ("CustSkuCountry", "CustCatCountry", "CustCountry"):
        assert column in result.columns
    # A composite key joins the dimensions with " - ".
    row = result[result["SKU #"] == "SKU-001"].iloc[0]
    assert row["CustSkuCountry"] == "Acme Foods - SKU-001 - US"
    assert row["CustCountry"] == "Acme Foods - US"


def test_build_mix_stage_keeps_only_nonzero_lbs_lines() -> None:
    """build_mix_stage filters out lines whose AOP or LE Lbs is zero."""
    # Arrange: one normal line plus a line whose LE Lbs is zero (must be dropped).
    rows: list[dict[str, object]] = []
    measures = [
        ("Lbs", 10.0, 12.0),
        ("Net-Revenue $", 90.0, 120.0),
    ]
    for attribute, aop, le in measures:
        rows.append(
            {
                "Country": "US",
                "SKU #": "SKU-001",
                "Attribute": attribute,
                "AOP": aop,
                "LE": le,
                "Diff": le - aop,
            }
        )
    # A zero-LE-Lbs line for a second SKU that the Lbs filter removes.
    for attribute, aop in (("Lbs", 5.0), ("Net-Revenue $", 40.0)):
        rows.append(
            {
                "Country": "US",
                "SKU #": "SKU-002",
                "Attribute": attribute,
                "AOP": aop,
                "LE": 0.0,
                "Diff": -aop,
            }
        )
    source = pd.DataFrame(rows)

    # Act
    stage = build_mix_stage(source, ["Country", "SKU #"])

    # Assert: only the nonzero-Lbs SKU survives.
    assert set(stage["SKU #"]) == {"SKU-001"}


def test_rollup_tie_out_customer_layer_sum_matches_scalar() -> None:
    """The sum of the customer-layer net price impact ties out to Mix-Rollup-4."""
    # Arrange: run the chain to the customer layer. The coarser layers source the
    # unfiltered mix_base at their own granularity (issue #20).
    mix_base = _mix_base_fixture()
    rollup_1 = build_mix_rollup_1(_rate_impacts_fixture())
    mix_1 = build_mix_1_sku(mix_base, rollup_1)
    rollup_2 = build_mix_rollup_2(mix_1)
    mix_2 = build_mix_2_category(mix_base, rollup_2)
    rollup_3 = build_mix_rollup_3(mix_2)
    mix_3 = build_mix_3_customer(mix_base, rollup_3)

    # Act
    rollup_4 = build_mix_rollup_4(mix_3)

    # Assert: the scalar rollup is exactly the sum of the customer-layer impacts.
    assert abs(_f(mix_3["Calc Net Price Impact"].sum()) - rollup_4) < 1e-9
