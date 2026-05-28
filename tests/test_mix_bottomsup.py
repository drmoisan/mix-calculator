"""Unit and property tests for the BottomsUp mix builders.

Covers the shared contribution helper in :mod:`src._mix_bottomsup_helpers`
(``classify_from_lbs`` four-branch zero-test and the ``SKU Mix`` identity), and
the three builders in :mod:`src.mix_bottomsup` (``build_mix_2_sku_bottomsup``,
``build_mix_3_category_bottomsup``, ``build_mix_4_customer_bottomsup``): column
presence and order, grain/row counts, the normal tie-out, the New/Disco
contribution branch activation, the zero-subtotal share guard, and the
Classification join. The fabricated fixtures and the real-chain runner live in
:mod:`tests.mix_bottomsup_fixtures`. Arrange-Act-Assert; fabricated data only;
no temp files.
"""

from __future__ import annotations

from typing import cast

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src._mix_bottomsup_helpers import build_contribution_columns, classify_from_lbs
from src.mix_bottomsup import (
    build_mix_2_sku_bottomsup,
    build_mix_3_category_bottomsup,
    build_mix_4_customer_bottomsup,
)
from tests.mix_bottomsup_fixtures import (
    CATEGORY_BOTTOMSUP_COLUMNS,
    CUSTOMER_BOTTOMSUP_COLUMNS,
    SKU_BOTTOMSUP_COLUMNS,
    build_chain,
    mix_base_rows,
)

# Hypothesis strategies bound magnitude so that the products of up to three terms
# in the contribution formulas stay well within float64 precision. An unbounded
# strategy makes the sum-equals-parts identity unverifiable because float64
# overflow/cancellation, not a logic defect, would drive any failure (see
# agent-memory hypothesis-float-magnitude-bounds).
#
# Measure terms (Lbs, rates, blended rates) are bounded to +/- 1e3. Subtotal
# denominators are bounded to the magnitude band [1.0, 1e3] so the Share ratios
# (Lbs / Subtotal) stay finite and small, keeping the triple products well inside
# the float64 range while still exercising both contribution sign and magnitude.
_MEASURE_FLOATS = st.floats(
    min_value=-1.0e3,
    max_value=1.0e3,
    allow_nan=False,
    allow_infinity=False,
)
_SUBTOTAL_FLOATS = st.floats(
    min_value=1.0,
    max_value=1.0e3,
    allow_nan=False,
    allow_infinity=False,
)

_CLASSIFICATIONS = st.sampled_from(
    ["normal", "new", "new distribution", "lost distribution", "eliminated"]
)


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


# ---------------------------------------------------------------------------
# Shared contribution helper
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(
    classification=_CLASSIFICATIONS,
    lbs_aop=_MEASURE_FLOATS,
    lbs_le=_MEASURE_FLOATS,
    net_rev_aop=_MEASURE_FLOATS,
    net_rev_le=_MEASURE_FLOATS,
    blended_aop=_MEASURE_FLOATS,
    blended_le=_MEASURE_FLOATS,
    subtotal_aop=_SUBTOTAL_FLOATS,
    subtotal_le=_SUBTOTAL_FLOATS,
)
def test_build_contribution_columns_sku_mix_equals_sum(
    classification: str,
    lbs_aop: float,
    lbs_le: float,
    net_rev_aop: float,
    net_rev_le: float,
    blended_aop: float,
    blended_le: float,
    subtotal_aop: float,
    subtotal_le: float,
) -> None:
    """SKU Mix equals New + Disco + Normal for arbitrary valid float inputs.

    Property (AC11): the contribution helper defines ``SKU Mix`` as the sum of the
    three mutually-exclusive contribution columns, so the identity must hold for
    every row regardless of classification or measure magnitudes.
    """
    # Arrange: a single-row frame carrying every input column the helper reads.
    frame = pd.DataFrame(
        {
            "Classification": [classification],
            "Lbs - AOP": [lbs_aop],
            "Lbs - LE": [lbs_le],
            "Net Rev Per Lb - AOP": [net_rev_aop],
            "Net Rev Per Lb - LE": [net_rev_le],
            "Blended Rate - AOP": [blended_aop],
            "Blended Rate - LE": [blended_le],
            "Lbs Subtotal - AOP": [subtotal_aop],
            "Lbs Subtotal - LE": [subtotal_le],
        }
    )

    # Act
    result = build_contribution_columns(frame)

    # Assert: SKU Mix ties out to the sum of the three contribution columns.
    parts = (
        _f(result.iloc[0]["New Contribution"])
        + _f(result.iloc[0]["Disco Contribution"])
        + _f(result.iloc[0]["Normal Contribution"])
    )
    sku_mix = _f(result.iloc[0]["SKU Mix"])
    tolerance = 1e-6 * (1.0 + abs(parts))
    assert abs(sku_mix - parts) <= tolerance


def test_build_contribution_columns_does_not_mutate_input() -> None:
    """The helper returns a new frame and leaves the caller's frame unchanged."""
    # Arrange
    frame = pd.DataFrame(
        {
            "Classification": ["normal"],
            "Lbs - AOP": [10.0],
            "Lbs - LE": [12.0],
            "Net Rev Per Lb - AOP": [9.0],
            "Net Rev Per Lb - LE": [10.0],
            "Blended Rate - AOP": [8.0],
            "Blended Rate - LE": [8.5],
            "Lbs Subtotal - AOP": [100.0],
            "Lbs Subtotal - LE": [110.0],
        }
    )
    original_columns = list(frame.columns)

    # Act
    result = build_contribution_columns(frame)

    # Assert: input is untouched; result carries the new columns.
    assert list(frame.columns) == original_columns
    assert "SKU Mix" in result.columns


@pytest.mark.parametrize(
    ("lbs_aop", "lbs_le", "expected"),
    [
        (0.0, 0.0, "eliminated"),
        (0.0, 5.0, "new distribution"),
        (5.0, 0.0, "lost distribution"),
        (5.0, 6.0, "normal"),
    ],
)
def test_classify_from_lbs_branches(
    lbs_aop: float, lbs_le: float, expected: str
) -> None:
    """classify_from_lbs returns the correct token for each zero/nonzero pair."""
    # Act / Assert: the four-branch zero-test maps each Lbs pair to its token.
    assert classify_from_lbs(lbs_aop, lbs_le) == expected


# ---------------------------------------------------------------------------
# SKU BottomsUp builder
# ---------------------------------------------------------------------------


def test_build_mix_2_sku_bottomsup_columns_present() -> None:
    """The SKU table carries the 22 spec columns in order (AC1)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_2_sku_bottomsup(
        chain["mix_0_detail"], chain["mix_base"], chain["mix_1_sku"]
    )

    # Assert: exact spec column order.
    assert list(result.columns) == SKU_BOTTOMSUP_COLUMNS


def test_build_mix_2_sku_bottomsup_row_count_matches_detail() -> None:
    """The SKU table has one row per mix_0_detail row (AC1)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_2_sku_bottomsup(
        chain["mix_0_detail"], chain["mix_base"], chain["mix_1_sku"]
    )

    # Assert
    assert len(result) == len(chain["mix_0_detail"])


def test_build_mix_2_sku_bottomsup_normal_sku_mix_tieout() -> None:
    """A normal SKU's SKU Mix equals Normal Contribution and a hand calc (AC2)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_2_sku_bottomsup(
        chain["mix_0_detail"], chain["mix_base"], chain["mix_1_sku"]
    )
    row = result[result["SKU #"] == "SKU-001"].iloc[0]

    # Assert: SKU Mix equals Normal Contribution (the other branches are zero), and
    # ties out to share-shift * mix-rate * Lbs Subtotal - LE computed from the row.
    expected = (
        (_f(row["Share - LE"]) - _f(row["Share - AOP"]))
        * (_f(row["Net Rev Per Lb - AOP"]) - _f(row["Blended Rate - AOP"]))
        * _f(row["Lbs Subtotal - LE"])
    )
    assert _f(row["New Contribution"]) == 0.0
    assert _f(row["Disco Contribution"]) == 0.0
    assert abs(_f(row["Normal Contribution"]) - expected) < 1e-9
    assert abs(_f(row["SKU Mix"]) - _f(row["Normal Contribution"])) < 1e-9


def test_build_mix_2_sku_bottomsup_new_contribution_active_when_new() -> None:
    """A new-distribution SKU has nonzero New Contribution, zero others (AC3)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_2_sku_bottomsup(
        chain["mix_0_detail"], chain["mix_base"], chain["mix_1_sku"]
    )
    row = result[result["SKU #"] == "SKU-003"].iloc[0]

    # Assert: only the New Contribution branch is active.
    assert row["Classification"] == "new distribution"
    assert _f(row["New Contribution"]) != 0.0
    assert _f(row["Disco Contribution"]) == 0.0
    assert _f(row["Normal Contribution"]) == 0.0


def test_build_mix_2_sku_bottomsup_disco_contribution_active_when_lost() -> None:
    """A lost-distribution SKU has nonzero Disco Contribution, zero others (AC4)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_2_sku_bottomsup(
        chain["mix_0_detail"], chain["mix_base"], chain["mix_1_sku"]
    )
    row = result[result["SKU #"] == "SKU-004"].iloc[0]

    # Assert: only the Disco Contribution branch is active.
    assert row["Classification"] == "lost distribution"
    assert _f(row["Disco Contribution"]) != 0.0
    assert _f(row["New Contribution"]) == 0.0
    assert _f(row["Normal Contribution"]) == 0.0


def test_build_mix_2_sku_bottomsup_zero_lbs_subtotal_share_is_zero() -> None:
    """When Lbs Subtotal is 0, the Share columns are 0.0 (not NaN) (AC5)."""
    # Arrange: a detail row whose (Customer, Category) has no mix_1_sku match, so
    # the merged Lbs Subtotal is 0 after fillna. A standalone Category Z SKU that is
    # new-distribution is excluded from mix_1_sku (zero AOP Lbs), so its subtotal
    # zero-fills.
    chain = build_chain()
    detail = chain["mix_0_detail"]
    extra = detail.iloc[[0]].copy()
    extra["SKU #"] = "SKU-099"
    extra["Category"] = "Category Z"
    extra["Lbs - AOP"] = 0.0
    extra["CustCatCountry"] = "Acme Foods - Category Z - US"
    detail_with_gap = pd.concat([detail, extra], ignore_index=True)
    mix_base = pd.concat(
        [
            chain["mix_base"],
            pd.DataFrame(
                mix_base_rows(
                    "Acme Foods",
                    "SKU-099",
                    "Category Z",
                    "US",
                    lbs_aop=0.0,
                    lbs_le=4.0,
                    net_rev_aop=0.0,
                    net_rev_le=30.0,
                    classification="new distribution",
                )
            ),
        ],
        ignore_index=True,
    )

    # Act
    result = build_mix_2_sku_bottomsup(detail_with_gap, mix_base, chain["mix_1_sku"])
    row = result[result["SKU #"] == "SKU-099"].iloc[0]

    # Assert: the unmatched subtotal zero-fills and the guarded shares are 0.0.
    assert _f(row["Lbs Subtotal - AOP"]) == 0.0
    assert _f(row["Share - AOP"]) == 0.0
    assert not pd.isna(row["Share - AOP"])
    assert not pd.isna(row["Share - LE"])


def test_build_mix_2_sku_bottomsup_classification_joined_correctly() -> None:
    """Output Classification matches mix_base for the same (Customer, SKU #) (AC6)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_2_sku_bottomsup(
        chain["mix_0_detail"], chain["mix_base"], chain["mix_1_sku"]
    )

    # Assert: each output row's Classification matches the mix_base value.
    base_lookup = (
        chain["mix_base"][["Customer", "SKU #", "Classification"]]
        .drop_duplicates()
        .set_index(["Customer", "SKU #"])["Classification"]
        .to_dict()
    )
    # Walk each output row and compare against the mix_base classification mapping.
    for _, row in result.iterrows():
        key = (row["Customer"], row["SKU #"])
        assert row["Classification"] == base_lookup[key]


# ---------------------------------------------------------------------------
# Category and customer BottomsUp builders
# ---------------------------------------------------------------------------


def test_build_mix_3_category_bottomsup_columns_present() -> None:
    """The category table carries the spec columns in order (AC7)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_3_category_bottomsup(
        chain["mix_0_detail"], chain["mix_2_category"]
    )

    # Assert
    assert list(result.columns) == CATEGORY_BOTTOMSUP_COLUMNS


def test_build_mix_3_category_bottomsup_row_count_matches_distinct_keys() -> None:
    """The category table has one row per distinct CustCatCountry (AC7)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_3_category_bottomsup(
        chain["mix_0_detail"], chain["mix_2_category"]
    )

    # Assert
    distinct = chain["mix_0_detail"]["CustCatCountry"].nunique()
    assert len(result) == distinct


def test_build_mix_3_category_bottomsup_sku_mix_tieout() -> None:
    """A normal category group ties out SKU Mix to a hand-calculated value (AC8)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_3_category_bottomsup(
        chain["mix_0_detail"], chain["mix_2_category"]
    )
    # Category X for Acme Foods aggregates two normal SKUs and one new SKU; the
    # aggregated AOP and LE Lbs are both nonzero, so it re-derives as normal.
    row = result[result["CustCatCountry"] == "Acme Foods - Category X - US"].iloc[0]

    # Assert: re-derived as normal and SKU Mix ties out to the normal contribution.
    expected = (
        (_f(row["Share - LE"]) - _f(row["Share - AOP"]))
        * (_f(row["Net Rev Per Lb - AOP"]) - _f(row["Blended Rate - AOP"]))
        * _f(row["Lbs Subtotal - LE"])
    )
    assert row["Classification"] == "normal"
    assert abs(_f(row["SKU Mix"]) - expected) < 1e-9


def test_build_mix_4_customer_bottomsup_columns_present() -> None:
    """The customer table carries the spec columns in order (AC9)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_4_customer_bottomsup(
        chain["mix_0_detail"], chain["mix_3_customer"]
    )

    # Assert
    assert list(result.columns) == CUSTOMER_BOTTOMSUP_COLUMNS


def test_build_mix_4_customer_bottomsup_row_count_matches_distinct_keys() -> None:
    """The customer table has one row per distinct CustCountry (AC9)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_4_customer_bottomsup(
        chain["mix_0_detail"], chain["mix_3_customer"]
    )

    # Assert
    distinct = chain["mix_0_detail"]["CustCountry"].nunique()
    assert len(result) == distinct


def test_build_mix_4_customer_bottomsup_sku_mix_tieout() -> None:
    """A normal customer group ties out SKU Mix to a hand-calculated value (AC10)."""
    # Arrange
    chain = build_chain()

    # Act
    result = build_mix_4_customer_bottomsup(
        chain["mix_0_detail"], chain["mix_3_customer"]
    )
    # The single customer-country group nets to nonzero AOP and LE Lbs -> normal.
    row = result[result["CustCountry"] == "Acme Foods - US"].iloc[0]

    # Assert: re-derived as normal and SKU Mix ties out to the normal contribution.
    expected = (
        (_f(row["Share - LE"]) - _f(row["Share - AOP"]))
        * (_f(row["Net Rev Per Lb - AOP"]) - _f(row["Blended Rate - AOP"]))
        * _f(row["Lbs Subtotal - LE"])
    )
    assert row["Classification"] == "normal"
    assert abs(_f(row["SKU Mix"]) - expected) < 1e-9
