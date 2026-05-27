"""Unit tests for the lookup and comparison transforms in :mod:`src.mix_lookups`.

Covers ``build_customer_lu`` (distinct pairs), ``build_aop_norm`` /
``build_le_norm`` (column drop and Scenario literal), ``build_aop_vs_le``
(concat, pivot, Cases exclusion, Diff, classification), and ``build_mix_base``
(SKU # str cast, left-join enrichment, six-attribute filter, inactive
exclusion). Arrange-Act-Assert; fabricated data only; the SkuLu fixture uses
fabricated descriptions and categories.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from src.mix_lookups import (
    MIX_BASE_ATTRIBUTES,
    build_aop_norm,
    build_aop_vs_le,
    build_customer_lu,
    build_le_norm,
    build_mix_base,
)


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _aop_long_frame() -> pd.DataFrame:
    """Build a fabricated long AOP frame with dimension columns and measures."""
    base = {
        "Customer Master": "Master Group",
        "Customer": "Acme Foods",
        "Super Category": "Category X",
        "PPG": "PPG-1",
        "SKU Descripiton": "Widget A",
        "SKU #": "SKU-001",
    }
    measures = [("Lbs", 10.0), ("Gross Sales", 100.0), ("Cases", 5.0)]
    return pd.DataFrame(
        [{**base, "Attribute": attr, "Value": value} for attr, value in measures]
    )


def _le_long_frame() -> pd.DataFrame:
    """Build a fabricated long LE frame with dimension columns and measures."""
    base = {
        "Customer": "Acme Foods",
        "Super Category": "Category X",
        "PPG": "PPG-1",
        "SKU Descripiton": "Widget A",
        "SKU #": "SKU-001",
    }
    measures = [("Lbs", 12.0), ("Gross Sales", 120.0)]
    return pd.DataFrame(
        [{**base, "Attribute": attr, "Value": value} for attr, value in measures]
    )


# ---------------------------------------------------------------------------
# build_customer_lu
# ---------------------------------------------------------------------------


def test_build_customer_lu_distinct_pairs() -> None:
    """build_customer_lu returns one row per distinct Customer/Master pair."""
    # Arrange: duplicate the same pair plus a distinct one.
    aop_raw = pd.DataFrame(
        {
            "Customer": ["Acme Foods", "Acme Foods", "Globex Market"],
            "Customer Master": ["Master Group", "Master Group", "Other Master"],
            "SKU #": ["SKU-001", "SKU-001", "SKU-002"],
        }
    )

    # Act
    result = build_customer_lu(aop_raw)

    # Assert: two distinct pairs, only the two lookup columns.
    assert list(result.columns) == ["Customer", "Customer Master"]
    assert len(result) == 2
    pairs = set(
        zip(
            result["Customer"].tolist(),
            result["Customer Master"].tolist(),
            strict=True,
        )
    )
    assert pairs == {
        ("Acme Foods", "Master Group"),
        ("Globex Market", "Other Master"),
    }


# ---------------------------------------------------------------------------
# build_aop_norm / build_le_norm
# ---------------------------------------------------------------------------


def test_build_aop_norm_drops_dimensions_and_adds_scenario() -> None:
    """build_aop_norm reduces to the comparison shape with Scenario == AOP."""
    # Arrange
    aop_long = _aop_long_frame()

    # Act
    result = build_aop_norm(aop_long)

    # Assert
    assert list(result.columns) == [
        "Customer",
        "SKU #",
        "Attribute",
        "Scenario",
        "Value",
    ]
    assert set(result["Scenario"]) == {"AOP"}


def test_build_le_norm_drops_dimensions_and_adds_scenario() -> None:
    """build_le_norm reduces to the comparison shape with Scenario == LE."""
    # Arrange
    le_long = _le_long_frame()

    # Act
    result = build_le_norm(le_long)

    # Assert
    assert list(result.columns) == [
        "Customer",
        "SKU #",
        "Attribute",
        "Scenario",
        "Value",
    ]
    assert set(result["Scenario"]) == {"LE"}


# ---------------------------------------------------------------------------
# build_aop_vs_le
# ---------------------------------------------------------------------------


def test_build_aop_vs_le_pivots_filters_cases_and_diffs() -> None:
    """build_aop_vs_le pivots scenarios, drops Cases, and computes Diff."""
    # Arrange
    aop_norm = build_aop_norm(_aop_long_frame())
    le_norm = build_le_norm(_le_long_frame())

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: Cases excluded, AOP/LE/Diff/Classification present.
    assert "Cases" not in set(result["Attribute"])
    assert set(["Customer", "SKU #", "Attribute", "AOP", "LE", "Diff"]).issubset(
        result.columns
    )
    assert "Classification" in result.columns
    lbs_row = result[result["Attribute"] == "Lbs"].iloc[0]
    # Diff = LE - AOP = 12 - 10 = 2.
    assert _f(lbs_row["Diff"]) == 2.0


def test_build_aop_vs_le_missing_scenario_column_filled_zero() -> None:
    """When a scenario has no rows, its pivot column is created and zero-filled."""
    # Arrange: AOP rows present, LE empty, so the LE column is absent from the
    # pivot and must be created as zero before the Diff.
    aop_norm = build_aop_norm(_aop_long_frame())
    le_norm = aop_norm.iloc[0:0].copy()

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: LE present and zero; Diff = LE - AOP = -AOP for the Lbs row.
    assert "LE" in result.columns
    lbs_row = result[result["Attribute"] == "Lbs"].iloc[0]
    assert _f(lbs_row["LE"]) == 0.0
    assert _f(lbs_row["Diff"]) == -10.0


def test_build_aop_vs_le_classifies_normal_for_nonzero_lbs() -> None:
    """A customer-SKU with nonzero AOP and LE Lbs is classified normal."""
    # Arrange
    aop_norm = build_aop_norm(_aop_long_frame())
    le_norm = build_le_norm(_le_long_frame())

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert
    assert set(result["Classification"]) == {"normal"}


# ---------------------------------------------------------------------------
# build_mix_base
# ---------------------------------------------------------------------------


def _sku_lu_frame() -> pd.DataFrame:
    """Build a fabricated SKU lookup; SKU-002 is intentionally absent (unmatched)."""
    return pd.DataFrame(
        {
            "SKU": ["SKU-001"],
            "SKU Description": ["Widget A"],
            "Category": ["Category X"],
            "Country": ["US"],
        }
    )


def _aop_vs_le_with_two_skus() -> pd.DataFrame:
    """Build an AopVsLe-shaped frame with one matched and one unmatched SKU."""
    aop_rows = [
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-001",
            "Attribute": "Lbs",
            "Value": 10.0,
        },
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-001",
            "Attribute": "Gross Sales",
            "Value": 100.0,
        },
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-002",
            "Attribute": "Lbs",
            "Value": 4.0,
        },
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-002",
            "Attribute": "Gross Sales",
            "Value": 40.0,
        },
    ]
    le_rows = [
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-001",
            "Attribute": "Lbs",
            "Value": 12.0,
        },
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-001",
            "Attribute": "Gross Sales",
            "Value": 120.0,
        },
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-002",
            "Attribute": "Lbs",
            "Value": 5.0,
        },
        {
            "Customer": "Acme Foods",
            "SKU #": "SKU-002",
            "Attribute": "Gross Sales",
            "Value": 50.0,
        },
    ]
    aop_norm = pd.DataFrame([{**row, "Scenario": "AOP"} for row in aop_rows])
    le_norm = pd.DataFrame([{**row, "Scenario": "LE"} for row in le_rows])
    return build_aop_vs_le(aop_norm, le_norm)


def test_build_mix_base_enriches_and_filters() -> None:
    """build_mix_base casts SKU #, joins the lookup, and filters attributes."""
    # Arrange
    aop_vs_le = _aop_vs_le_with_two_skus()
    sku_lu = _sku_lu_frame()

    # Act
    result = build_mix_base(aop_vs_le, sku_lu)

    # Assert: canonical columns and only measure attributes retained.
    assert list(result.columns) == [
        "Customer",
        "SKU #",
        "SKU Description",
        "Category",
        "Country",
        "Attribute",
        "AOP",
        "LE",
        "Diff",
        "Classification",
    ]
    assert set(result["Attribute"]).issubset(set(MIX_BASE_ATTRIBUTES))


def test_build_mix_base_left_join_unmatched_is_null() -> None:
    """An unmatched SKU keeps its rows but has null enrichment columns."""
    # Arrange: SKU-002 is absent from the lookup.
    aop_vs_le = _aop_vs_le_with_two_skus()
    sku_lu = _sku_lu_frame()

    # Act
    result = build_mix_base(aop_vs_le, sku_lu)

    # Assert: SKU-002 present with null Category; SKU-001 enriched.
    sku2 = result[result["SKU #"] == "SKU-002"]
    assert len(sku2) > 0
    assert sku2["Category"].isna().all()
    sku1 = result[result["SKU #"] == "SKU-001"]
    assert (sku1["Category"] == "Category X").all()


def test_build_mix_base_excludes_inactive() -> None:
    """Inactive customer-SKU lines are excluded from the mix base."""
    # Arrange: SKU-003 has zero AOP and LE so it classifies inactive.
    aop_norm = pd.DataFrame(
        [
            {
                "Customer": "Acme Foods",
                "SKU #": "SKU-003",
                "Attribute": "Lbs",
                "Scenario": "AOP",
                "Value": 0.0,
            },
            {
                "Customer": "Acme Foods",
                "SKU #": "SKU-003",
                "Attribute": "Gross Sales",
                "Scenario": "AOP",
                "Value": 0.0,
            },
        ]
    )
    le_norm = pd.DataFrame(
        [
            {
                "Customer": "Acme Foods",
                "SKU #": "SKU-003",
                "Attribute": "Lbs",
                "Scenario": "LE",
                "Value": 0.0,
            },
            {
                "Customer": "Acme Foods",
                "SKU #": "SKU-003",
                "Attribute": "Gross Sales",
                "Scenario": "LE",
                "Value": 0.0,
            },
        ]
    )
    aop_vs_le = build_aop_vs_le(aop_norm, le_norm)
    sku_lu = _sku_lu_frame()

    # Act
    result = build_mix_base(aop_vs_le, sku_lu)

    # Assert: the inactive SKU is dropped entirely.
    assert result.empty
