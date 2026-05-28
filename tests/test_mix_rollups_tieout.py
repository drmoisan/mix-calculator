"""AC8 four-layer tie-out and issue #20 single-scenario-volume regression tests.

Verifies the corrected coarser layers aggregate the unfiltered Mix_Base at their
own granularity.
"""

from __future__ import annotations

import pandas as pd

from src._mix_rollups_helpers import build_mix_stage
from src.mix_rollups import build_mix_2_category, build_mix_3_customer
from tests._mix_rollups_fixtures import (
    _f,
    _single_scenario_mix_base_fixture,
    _unfiltered_group_lbs_le,
)

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
