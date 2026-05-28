"""Unit tests for the mix rollup chain in :mod:`src.mix_rollups`.

Covers the rollup chain with a fabricated ``mix_base``/``rate_impacts`` fixture:
``build_mix_rollup_1..3`` grouping, ``build_mix_rollup_4`` scalar sum,
``build_mix_1_sku``/``build_mix_2_category``/``build_mix_3_customer``/
``build_mix_4_country`` mix columns, the ``fill_zero_with_avg`` application in
the customer and country layers, ``build_mix_0_detail`` composite keys, and the
rollup tie-out. Arrange-Act-Assert; fabricated data only.
"""

from __future__ import annotations

from typing import cast

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


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _mix_base_rows(
    customer: str,
    sku: str,
    category: str,
    country: str,
    *,
    lbs_aop: float,
    lbs_le: float,
    net_rev_aop: float,
    net_rev_le: float,
) -> list[dict[str, object]]:
    """Build all six measure Mix_Base rows for one customer-SKU pair.

    Gross Sales and the three (negated) deduction columns are derived so that
    ``Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $``
    holds for both scenarios, matching the pivot-stage invariant ``add_ratios``
    relies on. The deductions are a fixed fraction of gross sales.
    """

    def _measures(net_rev: float, lbs: float) -> list[tuple[str, float]]:
        # Gross sales is net revenue grossed up by the total deduction fraction;
        # each deduction is a fixed share of gross, stored negative.
        gross = net_rev / 0.8
        off_invoice = -0.10 * gross
        trade = -0.06 * gross
        non_trade = -0.04 * gross
        return [
            ("Gross Sales", gross),
            ("Lbs", lbs),
            ("Off Invoice $", off_invoice),
            ("Trade Spend $", trade),
            ("Non-Trade $", non_trade),
            ("Net-Revenue $", net_rev),
        ]

    aop_measures = dict(_measures(net_rev_aop, lbs_aop))
    le_measures = dict(_measures(net_rev_le, lbs_le))
    rows: list[dict[str, object]] = []
    # Each measure becomes one classified Mix_Base row with AOP, LE, and Diff.
    for attribute in aop_measures:
        aop = aop_measures[attribute]
        le = le_measures[attribute]
        rows.append(
            {
                "Customer": customer,
                "SKU #": sku,
                "SKU Description": f"Widget {sku[-1]}",
                "Category": category,
                "Country": country,
                "Attribute": attribute,
                "AOP": aop,
                "LE": le,
                "Diff": le - aop,
                "Classification": "normal",
            }
        )
    return rows


def _mix_base_fixture() -> pd.DataFrame:
    """Build a fabricated Mix_Base spanning two categories in two customers."""
    rows: list[dict[str, object]] = []
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-001",
        "Category X",
        "US",
        lbs_aop=10.0,
        lbs_le=12.0,
        net_rev_aop=90.0,
        net_rev_le=120.0,
    )
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-002",
        "Category Y",
        "US",
        lbs_aop=8.0,
        lbs_le=9.0,
        net_rev_aop=64.0,
        net_rev_le=81.0,
    )
    rows += _mix_base_rows(
        "Globex Market",
        "SKU-003",
        "Category X",
        "Canada",
        lbs_aop=5.0,
        lbs_le=6.0,
        net_rev_aop=40.0,
        net_rev_le=54.0,
    )
    return pd.DataFrame(rows)


def _rate_impacts_fixture() -> pd.DataFrame:
    """Build a fabricated rate-impacts table for the rollup-1 grouping test."""
    return pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Acme Foods", "Globex Market"],
            "Country": ["US", "US", "Canada"],
            "Category": ["Category X", "Category Y", "Category X"],
            "Calc Net Price Impact": [12.0, 8.0, 6.0],
        }
    )


def _single_scenario_mix_base_fixture() -> pd.DataFrame:
    """Build a Mix_Base with single-scenario lines that the SKU filter drops.

    The fabricated frame puts three SKU lines inside one ``{Customer, Country}``
    group (``Acme Foods`` / ``US``):

    - a normal two-scenario line with nonzero AOP and LE Lbs (survives the SKU
      filter on its own);
    - a SKU that is new in LE (``lbs_aop=0`` / nonzero ``lbs_le``), which the
      ``build_mix_stage`` nonzero-Lbs filter removes at the SKU layer; and
    - a SKU dropped in LE (nonzero ``lbs_aop`` / ``lbs_le=0``), likewise removed
      at the SKU layer.

    Because each coarser layer must re-aggregate the unfiltered ``mix_base`` at
    its own granularity, the LE volume of the new-in-LE line and the AOP volume
    of the dropped-in-LE line must still reach the ``{Customer, Country}`` group
    total. A normal line in a second group (``Globex Market`` / ``Canada``)
    guards against accidental cross-group leakage. Fabricated labels only.
    """
    rows: list[dict[str, object]] = []
    # Normal two-scenario line: nonzero AOP and LE Lbs, survives the SKU filter.
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-001",
        "Category X",
        "US",
        lbs_aop=10.0,
        lbs_le=12.0,
        net_rev_aop=90.0,
        net_rev_le=120.0,
    )
    # SKU new in LE: zero AOP Lbs, nonzero LE Lbs -> dropped by the SKU filter.
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-002",
        "Category Y",
        "US",
        lbs_aop=0.0,
        lbs_le=7.0,
        net_rev_aop=0.0,
        net_rev_le=70.0,
    )
    # SKU dropped in LE: nonzero AOP Lbs, zero LE Lbs -> dropped by the SKU filter.
    rows += _mix_base_rows(
        "Acme Foods",
        "SKU-003",
        "Category Z",
        "US",
        lbs_aop=5.0,
        lbs_le=0.0,
        net_rev_aop=40.0,
        net_rev_le=0.0,
    )
    # A normal line in a separate {Customer, Country} group for leakage guarding.
    rows += _mix_base_rows(
        "Globex Market",
        "SKU-004",
        "Category X",
        "Canada",
        lbs_aop=5.0,
        lbs_le=6.0,
        net_rev_aop=40.0,
        net_rev_le=54.0,
    )
    return pd.DataFrame(rows)


def _unfiltered_group_lbs_le(
    mix_base: pd.DataFrame,
    group_keys: list[str],
    group_values: dict[str, str],
) -> float:
    """Sum the unfiltered Mix_Base ``Lbs`` LE measure for one group.

    Directly aggregates the ``Attribute == "Lbs"`` rows of ``mix_base`` over the
    given group (no nonzero-Lbs filter), which is the volume the corrected
    coarser layer must retain at ``group_keys`` granularity.

    Args:
        mix_base: The fabricated Mix_Base frame.
        group_keys: The grouping dimensions (e.g. ``["Customer", "Country"]``).
        group_values: The specific group to total (e.g. ``{"Customer": ...}``).

    Returns:
        The summed LE-scenario ``Lbs`` for the selected group.
    """
    lbs_rows = mix_base[mix_base["Attribute"] == "Lbs"].copy()
    # Narrow to the requested group across every supplied key dimension.
    for key in group_keys:
        lbs_rows = lbs_rows[lbs_rows[key] == group_values[key]]
    return _f(lbs_rows["LE"].sum())


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


# ---------------------------------------------------------------------------
# Single-scenario volume retention (issue #20 regression) and the
# NPI-minus-rollup identity. The corrected coarser layers must aggregate the
# unfiltered Mix_Base at their own granularity, so single-scenario lines that
# the SKU-layer filter drops still contribute their volume to the coarser
# aggregates.
# ---------------------------------------------------------------------------


def test_category_layer_retains_single_scenario_volume() -> None:
    """Category layer retains single-scenario LE volume from unfiltered Mix_Base.

    A SKU new in LE (zero AOP Lbs / nonzero LE Lbs) is dropped by the SKU-layer
    nonzero-Lbs filter, so re-aggregating the filtered SKU layer understates the
    ``{Customer, Country}`` LE volume. The corrected category layer aggregates
    the unfiltered ``mix_base`` at ``{Customer, Country}`` granularity, so its
    group ``Lbs - LE`` must equal the directly computed unfiltered Mix_Base
    group sum.
    """
    # Arrange
    mix_base = _single_scenario_mix_base_fixture()
    rollup_2 = pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Globex Market"],
            "Country": ["US", "Canada"],
            "Calc Net Price Impact": [0.0, 0.0],
        }
    )
    expected_lbs_le = _unfiltered_group_lbs_le(
        mix_base,
        ["Customer", "Country"],
        {"Customer": "Acme Foods", "Country": "US"},
    )

    # Act
    mix_2 = build_mix_2_category(mix_base, rollup_2)

    # Assert: the {Acme Foods, US} group LE volume equals the unfiltered sum
    # (normal 12.0 + new-in-LE 7.0 + dropped-in-LE 0.0 = 19.0), proving the
    # single-scenario LE line was retained.
    acme_us = mix_2[(mix_2["Customer"] == "Acme Foods") & (mix_2["Country"] == "US")]
    assert len(acme_us) == 1
    assert abs(_f(acme_us.iloc[0]["Lbs - LE"]) - expected_lbs_le) < 1e-9


def test_customer_layer_retains_single_scenario_volume() -> None:
    """Customer layer retains single-scenario LE volume at {Country} granularity.

    The corrected customer layer aggregates the unfiltered ``mix_base`` grouped
    by ``{Country}``, so the new-in-LE line's volume reaches the customer-layer
    aggregate. The group ``Lbs - LE`` must equal the directly computed
    unfiltered Mix_Base ``{Country}`` group sum.
    """
    # Arrange
    mix_base = _single_scenario_mix_base_fixture()
    rollup_3 = pd.DataFrame(
        {
            "Country": ["US", "Canada"],
            "Calc Net Price Impact": [0.0, 0.0],
        }
    )
    expected_lbs_le = _unfiltered_group_lbs_le(
        mix_base,
        ["Country"],
        {"Country": "US"},
    )

    # Act
    mix_3 = build_mix_3_customer(mix_base, rollup_3)

    # Assert: the US-country group LE volume equals the unfiltered Mix_Base sum
    # (12.0 + 7.0 + 0.0 = 19.0), proving the single-scenario LE line reaches the
    # customer-layer aggregate.
    us_group = mix_3[mix_3["Country"] == "US"]
    assert len(us_group) == 1
    assert abs(_f(us_group.iloc[0]["Lbs - LE"]) - expected_lbs_le) < 1e-9


def test_layer_mix_equals_full_aggregation_minus_rollup() -> None:
    """Each layer's mix equals its recomputed NPI minus the prior-layer NPI sum.

    For the category and customer layers, the mix column must equal the layer's
    own recomputed ``Calc Net Price Impact`` minus the summed prior-finer-layer
    ``Calc Net Price Impact`` supplied as the rollup target (AC2). The rollup
    target here is fabricated so the identity is checkable without confidential
    figures.
    """
    # Arrange: fabricated rollup targets for each coarser layer.
    mix_base = _single_scenario_mix_base_fixture()
    rollup_2 = pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Globex Market"],
            "Country": ["US", "Canada"],
            "Calc Net Price Impact": [3.0, 1.5],
        }
    )
    rollup_3 = pd.DataFrame(
        {
            "Country": ["US", "Canada"],
            "Calc Net Price Impact": [4.0, 2.0],
        }
    )

    # Act
    mix_2 = build_mix_2_category(mix_base, rollup_2)
    mix_3 = build_mix_3_customer(mix_base, rollup_3)

    # Independently recompute the category-layer NPI from the unfiltered Mix_Base
    # at {Customer, Country} granularity (the corrected full-aggregation source),
    # so the comparison is against an external recomputation rather than the
    # builder's own readback.
    expected_category = build_mix_stage(mix_base, ["Customer", "Country"])
    expected_category_npi = {
        (str(row["Customer"]), str(row["Country"])): _f(row["Calc Net Price Impact"])
        for _, row in expected_category.iterrows()
    }

    # The corrected category layer must produce the same {Customer, Country}
    # groups the full aggregation yields (pre-fix the layer is empty, so this
    # presence check fails).
    assert len(mix_2) == len(expected_category)
    assert len(mix_2) > 0

    rollup_2_lookup = {
        (str(row["Customer"]), str(row["Country"])): _f(row["Calc Net Price Impact"])
        for _, row in rollup_2.iterrows()
    }
    # Verify Category Mix == full-aggregation NPI minus the matched rollup-2 NPI.
    for _, row in mix_2.iterrows():
        key = (str(row["Customer"]), str(row["Country"]))
        layer_npi = expected_category_npi[key]
        assert abs(_f(row["Calc Net Price Impact"]) - layer_npi) < 1e-9
        expected_mix = layer_npi - rollup_2_lookup.get(key, 0.0)
        assert abs(_f(row["Category Mix"]) - expected_mix) < 1e-9

    # The corrected customer layer must produce non-empty {Country} groups
    # (pre-fix the layer is empty).
    assert len(mix_3) > 0

    rollup_3_lookup = {
        str(row["Country"]): _f(row["Calc Net Price Impact"])
        for _, row in rollup_3.iterrows()
    }
    # Verify Customer Mix == the layer's recomputed NPI minus the matched
    # rollup-3 NPI for every customer-layer row.
    for _, row in mix_3.iterrows():
        key = str(row["Country"])
        expected_mix = _f(row["Calc Net Price Impact"]) - rollup_3_lookup.get(key, 0.0)
        assert abs(_f(row["Customer Mix"]) - expected_mix) < 1e-9
