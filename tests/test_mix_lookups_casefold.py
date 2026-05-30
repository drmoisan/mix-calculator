"""Unit tests for the case-insensitive Customer join (issue #35).

Covers ``build_aop_norm`` / ``build_le_norm`` Customer whitespace stripping
(AC2), ``build_customer_lu`` whitespace stripping (AC4), and the casefolded
pivot rework in ``build_aop_vs_le`` (AC3, AC5, AC6a-e). Tests use synthetic
in-memory fixtures only; no workbook reads, no temp files.

These tests are factored out of ``tests/test_mix_lookups.py`` to keep both
files under the 500-line policy cap.
"""

from __future__ import annotations

from typing import cast

import pandas as pd

from src.mix_lookups import (
    build_aop_norm,
    build_aop_vs_le,
    build_customer_lu,
    build_le_norm,
)


def _f(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions."""
    return float(cast("float", value))


def _aop_norm_rows(
    customer: str, sku: str, attribute: str, value: float
) -> dict[str, object]:
    """Build a single AOP-normalized row dict for synthetic Customer-join tests.

    Returns a dict shaped as a row in the ``aop_norm`` frame contract:
    ``{Customer, SKU #, Attribute, Scenario, Value}``. Used by the
    Customer-case-insensitivity tests to keep fixture construction terse.

    Args:
        customer: Raw Customer string (casing/whitespace preserved).
        sku: SKU # value (string or numeric-as-string).
        attribute: Attribute name (e.g., ``"Lbs"``, ``"Off Invoice $"``).
        value: Measure value.

    Returns:
        A dict suitable for inclusion in a list passed to ``pd.DataFrame``.
    """
    return {
        "Customer": customer,
        "SKU #": sku,
        "Attribute": attribute,
        "Scenario": "AOP",
        "Value": value,
    }


def _le_norm_rows(
    customer: str, sku: str, attribute: str, value: float
) -> dict[str, object]:
    """Build a single LE-normalized row dict for synthetic Customer-join tests.

    Returns a dict shaped as a row in the ``le_norm`` frame contract:
    ``{Customer, SKU #, Attribute, Scenario, Value}``.

    Args:
        customer: Raw Customer string (casing/whitespace preserved).
        sku: SKU # value.
        attribute: Attribute name.
        value: Measure value.

    Returns:
        A dict suitable for inclusion in a list passed to ``pd.DataFrame``.
    """
    return {
        "Customer": customer,
        "SKU #": sku,
        "Attribute": attribute,
        "Scenario": "LE",
        "Value": value,
    }


def test_build_aop_vs_le_casefold_winco_merges() -> None:
    """AC5: AOP 'Winco' and LE 'WINCO' for SKU 69005 merge to one row per attribute."""
    # Arrange: AOP has two deduction rows under 'Winco'; LE has the same two
    # deductions under 'WINCO' plus Gross Sales and Lbs under 'Winco'.
    aop_norm = pd.DataFrame(
        [
            _aop_norm_rows("Winco", "69005", "Off Invoice $", -1000.0),
            _aop_norm_rows("Winco", "69005", "Non-Trade $", -200.0),
        ]
    )
    le_norm = pd.DataFrame(
        [
            _le_norm_rows("WINCO", "69005", "Off Invoice $", -1000.0),
            _le_norm_rows("WINCO", "69005", "Non-Trade $", -200.0),
            _le_norm_rows("Winco", "69005", "Gross Sales", 5000.0),
            _le_norm_rows("Winco", "69005", "Lbs", 1000.0),
        ]
    )

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: exactly one row per attribute; all displayed Customer values are 'Winco'.
    attributes = sorted(result["Attribute"].tolist())
    assert attributes == sorted(["Off Invoice $", "Non-Trade $", "Gross Sales", "Lbs"])
    assert len(result) == 4
    assert set(result["Customer"].tolist()) == {"Winco"}


def test_build_aop_vs_le_casefold_collapses_three_casings() -> None:
    """AC6a: 'Winco', 'WINCO', 'winco' on AOP side collapse to one key."""
    # Arrange: three different casings for the same customer on the AOP side.
    aop_norm = pd.DataFrame(
        [
            _aop_norm_rows("Winco", "69005", "Lbs", 10.0),
            _aop_norm_rows("WINCO", "69005", "Lbs", 20.0),
            _aop_norm_rows("winco", "69005", "Lbs", 30.0),
        ]
    )
    le_norm = aop_norm.iloc[0:0].copy()
    le_norm["Scenario"] = "LE"

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: exactly one row for the (SKU, Attribute) pair; AOP equals the sum;
    # displayed Customer is the first observed casing ('Winco').
    assert len(result) == 1
    row = result.iloc[0]
    assert row["Customer"] == "Winco"
    assert _f(row["AOP"]) == 60.0


def test_build_aop_vs_le_casefold_strips_whitespace() -> None:
    """AC6b: leading/trailing whitespace on Customer is normalized for the join."""
    # Arrange: AOP 'Winco' joins to LE 'Winco ' (trailing) on Lbs and to LE
    # ' Winco' (leading) on Gross Sales.
    aop_norm = pd.DataFrame(
        [
            _aop_norm_rows("Winco", "69005", "Lbs", 10.0),
        ]
    )
    le_norm = pd.DataFrame(
        [
            _le_norm_rows("Winco ", "69005", "Lbs", 12.0),
            _le_norm_rows(" Winco", "69005", "Gross Sales", 100.0),
        ]
    )

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: one row per attribute; displayed Customer is 'Winco' on both.
    assert len(result) == 2
    assert set(result["Customer"].tolist()) == {"Winco"}
    lbs_row = result[result["Attribute"] == "Lbs"].iloc[0]
    assert _f(lbs_row["LE"]) == 12.0
    gross_row = result[result["Attribute"] == "Gross Sales"].iloc[0]
    assert _f(gross_row["LE"]) == 100.0


def test_build_aop_vs_le_display_aop_casing_wins() -> None:
    """AC6c: When AOP and LE both match, displayed Customer uses AOP-side casing."""
    # Arrange: AOP has 'Winco'; LE has 'WINCO' for the same SKU/Attribute.
    aop_norm = pd.DataFrame(
        [
            _aop_norm_rows("Winco", "69005", "Lbs", 10.0),
        ]
    )
    le_norm = pd.DataFrame(
        [
            _le_norm_rows("WINCO", "69005", "Lbs", 12.0),
        ]
    )

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: AOP-side casing wins on display.
    assert len(result) == 1
    assert result.iloc[0]["Customer"] == "Winco"


def test_build_aop_vs_le_le_only_keeps_le_casing() -> None:
    """AC6d: LE-only customer (no AOP row) preserves LE casing on display."""
    # Arrange: AOP has no rows for this customer; LE has 'WINCO'.
    aop_norm = pd.DataFrame(
        columns=["Customer", "SKU #", "Attribute", "Scenario", "Value"]
    )
    le_norm = pd.DataFrame(
        [
            _le_norm_rows("WINCO", "69005", "Off Invoice $", -1000.0),
        ]
    )

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: one row, displayed Customer equals 'WINCO' (LE-side casing kept).
    assert len(result) == 1
    assert result.iloc[0]["Customer"] == "WINCO"


def test_build_aop_vs_le_five_casings_collapse_to_one() -> None:
    """AC6e: A single customer in five casings collapses to one output row."""
    # Arrange: five casing variants on AOP side, same SKU and Attribute.
    aop_norm = pd.DataFrame(
        [
            _aop_norm_rows("Winco", "69005", "Lbs", 1.0),
            _aop_norm_rows("WINCO", "69005", "Lbs", 2.0),
            _aop_norm_rows("winco", "69005", "Lbs", 3.0),
            _aop_norm_rows("WinCo", "69005", "Lbs", 4.0),
            _aop_norm_rows("wInCo", "69005", "Lbs", 5.0),
        ]
    )
    le_norm = aop_norm.iloc[0:0].copy()
    le_norm["Scenario"] = "LE"

    # Act
    result = build_aop_vs_le(aop_norm, le_norm)

    # Assert: one row for the (SKU, Attribute) pair; AOP equals the sum of values.
    assert len(result) == 1
    assert _f(result.iloc[0]["AOP"]) == 15.0


def test_build_customer_lu_strips_whitespace() -> None:
    """AC4: build_customer_lu strips whitespace so 'Winco ' and 'Winco' collapse."""
    # Arrange: two rows differing only by trailing whitespace.
    aop_raw = pd.DataFrame(
        {
            "Customer": ["Winco ", "Winco"],
            "Customer Master": ["Master", "Master"],
            "SKU #": ["69005", "69005"],
        }
    )

    # Act
    result = build_customer_lu(aop_raw)

    # Assert: collapsed to a single row.
    assert len(result) == 1
    assert result.iloc[0]["Customer"] == "Winco"
    assert result.iloc[0]["Customer Master"] == "Master"


def test_build_aop_norm_strips_customer_whitespace() -> None:
    """AC2: build_aop_norm strips leading/trailing whitespace on the Customer column."""
    # Arrange: a long AOP frame with a trailing-whitespace Customer value.
    aop_long = pd.DataFrame(
        [
            {
                "Customer Master": "Master",
                "Customer": "Winco ",
                "Super Category": "Cat",
                "PPG": "PPG-1",
                "SKU Descripiton": "Widget",
                "SKU #": "69005",
                "Attribute": "Lbs",
                "Value": 10.0,
            }
        ]
    )

    # Act
    result = build_aop_norm(aop_long)

    # Assert: trailing whitespace removed; casing preserved.
    assert result["Customer"].tolist() == ["Winco"]


def test_build_le_norm_strips_customer_whitespace() -> None:
    """AC2: build_le_norm strips leading/trailing whitespace on the Customer column."""
    # Arrange: a long LE frame with a leading-whitespace Customer value.
    le_long = pd.DataFrame(
        [
            {
                "Customer": " Winco",
                "Super Category": "Cat",
                "PPG": "PPG-1",
                "SKU Descripiton": "Widget",
                "SKU #": "69005",
                "Attribute": "Lbs",
                "Value": 12.0,
            }
        ]
    )

    # Act
    result = build_le_norm(le_long)

    # Assert: leading whitespace removed; casing preserved.
    assert result["Customer"].tolist() == ["Winco"]
