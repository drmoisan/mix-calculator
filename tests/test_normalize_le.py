"""Pure-transform tests for :mod:`src.normalize_le`.

Covers ``coerce_sku``, ``rebuild_key``, ``decide_key_action``, ``resolve_key``,
``load_source``, ``compute_ytg``, and ``normalize``. The ``load_source``
blank-total fill cases live in ``test_normalize_le_totals.py``; I/O, persistence,
and CLI tests live in ``test_normalize_le_io.py``; column-resolution tests live
in ``test_le_columns.py``. Shared in-memory fixtures live in ``le_fixtures.py``;
no temporary files are created on disk.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.normalize_le import (
    MONTH_COLUMNS,
    SOURCE_COLUMNS,
    TARGET_COLUMNS,
    coerce_sku,
    compute_ytg,
    load_source,
    normalize,
    rebuild_key,
)
from tests.le_fixtures import (
    as_float,
    build_workbook,
    close,
    loaded_frame,
    make_row,
)

# ---------------------------------------------------------------------------
# coerce_sku
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (5, "5"),
        (np.int64(5), "5"),
        (5.0, "5"),
        (5.5, "5.5"),
        (np.float64(7.0), "7"),
        (np.nan, ""),
        (None, ""),
        ("RGFBOWLCB", "RGFBOWLCB"),
        ("NotSKU", "NotSKU"),
        (True, "True"),
        (False, "False"),
    ],
)
def test_coerce_sku_branches(value: object, expected: str) -> None:
    """coerce_sku renders each value type the way the Excel key formula does."""
    # Act / Assert
    assert coerce_sku(value) == expected


@given(st.integers())
def test_coerce_sku_integer_property(value: int) -> None:
    """For any integer, coerce_sku equals str(value) and has no decimal point."""
    # Act
    result = coerce_sku(value)

    # Assert
    assert result == str(value)
    assert "." not in result


# ---------------------------------------------------------------------------
# rebuild_key
# ---------------------------------------------------------------------------


def test_rebuild_key_whole_number_sku() -> None:
    """A whole-number SKU renders as an integer segment with no separators."""
    # Act / Assert
    assert rebuild_key("CustA", 5.0, "Gross Sales") == "CustA5Gross Sales"


def test_rebuild_key_preserves_non_numeric_sku() -> None:
    """A non-numeric SKU code is preserved verbatim in the rebuilt key."""
    # Act / Assert
    assert rebuild_key("CustA", "RGFBOWLCB", "Lbs") == "CustARGFBOWLCBLbs"


@given(
    customer=st.text(),
    sku=st.integers(),
    type_=st.text(),
)
def test_rebuild_key_property(customer: str, sku: int, type_: str) -> None:
    """The rebuilt key equals customer + str(int_sku) + type_ with no separator."""
    # Act / Assert
    assert rebuild_key(customer, sku, type_) == f"{customer}{sku}{type_}"


# ---------------------------------------------------------------------------
# load_source
# ---------------------------------------------------------------------------


def test_load_source_header_and_columns() -> None:
    """load_source reads with header=2 and yields the source columns."""
    # Arrange
    rows = [
        make_row(
            customer="CustA",
            sku=5,
            type_="Gross Sales",
            ppg="PPGX",
            months=[1.0] * 12,
        )
    ]
    buffer = build_workbook(rows, sheet_name="LE-8 + 4")

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert: every canonical source column is present (KEY established last);
    # the "YTD/YTG" column is retained here and dropped later in normalize.
    assert set(frame.columns) == set(SOURCE_COLUMNS)


def test_load_source_drops_blank_customer_rows() -> None:
    """Rows with a blank Customer are dropped on load."""
    # Arrange: one real row followed by a trailing blank-Customer row.
    rows = [
        make_row(
            customer="CustA",
            sku=5,
            type_="Gross Sales",
            ppg="PPGX",
            months=[1.0] * 12,
        ),
        make_row(
            customer=None,
            sku=9,
            type_="Lbs",
            ppg="PPGZ",
            months=[2.0] * 12,
        ),
    ]
    buffer = build_workbook(rows)

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert
    assert len(frame) == 1
    assert frame.iloc[0]["Customer"] == "CustA"


def test_load_source_overwrite_rebuilds_key_ignoring_loaded_value() -> None:
    """Under overwrite, a present diverging KEY is rebuilt from components."""
    # Arrange: include the optional KEY column with a stale, diverging value.
    rows = [
        make_row(
            customer="CustA",
            sku=5,
            type_="Gross Sales",
            ppg="PPGX",
            months=[1.0] * 12,
            key="THIS_SHOULD_BE_IGNORED",
        )
    ]
    buffer = build_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    frame = load_source(buffer, "LE-8 + 4", key_mismatch="overwrite")

    # Assert
    assert frame.iloc[0]["KEY"] == "CustA5Gross Sales"


# ---------------------------------------------------------------------------
# compute_ytg
# ---------------------------------------------------------------------------


def test_compute_ytg_sums_may_through_dec() -> None:
    """compute_ytg sums May..Dec and excludes Jan..Apr."""
    # Arrange: Jan..Apr = 100 each (excluded), May..Dec = 1..8.
    months = [100.0, 100.0, 100.0, 100.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    frame = pd.DataFrame([dict(zip(MONTH_COLUMNS, months, strict=True))])

    # Act
    result = compute_ytg(frame)

    # Assert
    assert close(result.iloc[0], 36.0)


@given(
    months=st.lists(
        st.floats(allow_nan=False, allow_infinity=False, width=32),
        min_size=12,
        max_size=12,
    )
)
def test_compute_ytg_property(months: list[float]) -> None:
    """compute_ytg equals the sum of months 5..12 within tolerance."""
    # Arrange
    frame = pd.DataFrame([dict(zip(MONTH_COLUMNS, months, strict=True))])

    # Act
    result = as_float(compute_ytg(frame).iloc[0])

    # Assert
    assert close(result, sum(months[4:]), tol=1e-9)


# ---------------------------------------------------------------------------
# normalize
# ---------------------------------------------------------------------------


def test_normalize_singleton_key_passthrough() -> None:
    """A KEY appearing once passes its values through unchanged."""
    # Arrange
    months = [float(i) for i in range(1, 13)]
    frame = loaded_frame(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=months)]
    )

    # Act
    out = normalize(frame)

    # Assert
    assert len(out) == 1
    assert close(out.iloc[0]["FY"], sum(months))


def test_normalize_two_row_pair_sums_numeric() -> None:
    """A YTD+YTG pair sums month/FY/quarter columns and keeps first-row text."""
    # Arrange
    ytd = [1.0, 2.0, 3.0, 4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ytg = [0.0, 0.0, 0.0, 0.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]
    frame = loaded_frame(
        [
            make_row(
                customer="CustB",
                sku=5,
                type_="Gross Sales",
                ppg="PPGX",
                months=ytd,
                ytd_ytg="YTD",
                description="First Desc",
            ),
            make_row(
                customer="CustB",
                sku=5,
                type_="Gross Sales",
                ppg="PPGX",
                months=ytg,
                ytd_ytg="YTG",
                description="Second Desc",
            ),
        ]
    )

    # Act
    out = normalize(frame)

    # Assert
    assert len(out) == 1
    row = out.iloc[0]
    assert close(row["Jan"], 1.0)
    assert close(row["May"], 5.0)
    assert close(row["FY"], sum(ytd) + sum(ytg))
    assert row["SKU Descripiton"] == "First Desc"


def test_normalize_three_rows_sum_and_nan_as_zero() -> None:
    """3+ rows per KEY sum all matching rows and treat NaN months as 0."""
    # Arrange: third row carries NaN months that must be treated as 0.
    base = [1.0] * 12
    nan_months = [float("nan")] * 12
    frame = loaded_frame(
        [
            make_row(customer="A", sku=1, type_="T", ppg="P", months=base),
            make_row(customer="A", sku=1, type_="T", ppg="P", months=base),
            make_row(customer="A", sku=1, type_="T", ppg="P", months=nan_months),
        ]
    )

    # Act
    out = normalize(frame)

    # Assert: each month sums to 2.0 (two rows of 1.0; NaN row contributes 0).
    assert len(out) == 1
    assert close(out.iloc[0]["Jan"], 2.0)
    assert close(out.iloc[0]["FY"], 24.0)


def test_normalize_column_order_and_no_ytd_ytg() -> None:
    """Output has the 26 target columns in order and no YTD/YTG column."""
    # Arrange
    frame = loaded_frame(
        [make_row(customer="A", sku=1, type_="T", ppg="P", months=[1.0] * 12)]
    )

    # Act
    out = normalize(frame)

    # Assert
    assert list(out.columns) == TARGET_COLUMNS
    assert "YTD/YTG" not in out.columns


def test_normalize_first_appearance_order_preserved() -> None:
    """Rows appear in first-appearance order, not alphabetical/KEY order."""
    # Arrange: deliberately non-alphabetical first appearance (Zeta before Alpha).
    frame = loaded_frame(
        [
            make_row(customer="Zeta", sku=1, type_="T", ppg="P", months=[1.0] * 12),
            make_row(customer="Alpha", sku=2, type_="T", ppg="P", months=[1.0] * 12),
        ]
    )

    # Act
    out = normalize(frame)

    # Assert
    assert out["KEY"].tolist() == ["Zeta1T", "Alpha2T"]


def test_normalize_super_category_ppg_quirk() -> None:
    """Super Category and PPG both equal the source PPG and match per row."""
    # Arrange
    frame = loaded_frame(
        [
            make_row(
                customer="A",
                sku=1,
                type_="T",
                ppg="PPG_VALUE",
                super_category="IGNORED_SOURCE_SUPER",
                months=[1.0] * 12,
            )
        ]
    )

    # Act
    out = normalize(frame)

    # Assert
    assert out.iloc[0]["Super Category"] == "PPG_VALUE"
    assert out.iloc[0]["PPG"] == "PPG_VALUE"
    assert out.iloc[0]["Super Category"] == out.iloc[0]["PPG"]


def test_normalize_non_numeric_sku_preserved() -> None:
    """Non-numeric SKU codes are preserved verbatim in KEY and SKU #."""
    # Arrange
    frame = loaded_frame(
        [
            make_row(
                customer="CustA",
                sku="RGFBOWLCB",
                type_="Lbs",
                ppg="P",
                months=[1.0] * 12,
            )
        ]
    )

    # Act
    out = normalize(frame)

    # Assert
    assert out.iloc[0]["KEY"] == "CustARGFBOWLCBLbs"
    assert out.iloc[0]["SKU #"] == "RGFBOWLCB"


@given(
    specs=st.lists(
        st.tuples(
            st.integers(min_value=1, max_value=5),
            st.lists(
                st.lists(
                    st.floats(
                        allow_nan=False,
                        allow_infinity=False,
                        min_value=-1e6,
                        max_value=1e6,
                        width=32,
                    ),
                    min_size=12,
                    max_size=12,
                ),
                min_size=1,
                max_size=4,
            ),
        ),
        min_size=1,
        max_size=5,
    )
)
def test_normalize_property_row_count_and_sums(
    specs: list[tuple[int, list[list[float]]]],
) -> None:
    """Output row count equals unique KEYs and month columns equal per-key sums."""
    # Arrange: each spec is a distinct customer index with 1..N source rows.
    rows: list[dict[str, object]] = []
    expected_sums: dict[str, list[float]] = {}
    for index, (_, month_vectors) in enumerate(specs):
        customer = f"Cust{index}"
        key = f"{customer}1T"
        # Accumulate the expected per-key monthly sums across that key's rows.
        running = [0.0] * 12
        for vector in month_vectors:
            rows.append(
                make_row(customer=customer, sku=1, type_="T", ppg="P", months=vector)
            )
            for month_index in range(12):
                running[month_index] += vector[month_index]
        expected_sums[key] = running

    frame = loaded_frame(rows)

    # Act
    out = normalize(frame)

    # Assert
    assert len(out) == len(expected_sums)
    # Compare each output row's monthly sums against the per-key running totals.
    for _, output_row in out.iterrows():
        key = str(output_row["KEY"])
        for month_index, month in enumerate(MONTH_COLUMNS):
            assert close(output_row[month], expected_sums[key][month_index], tol=1e-6)
