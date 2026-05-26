"""Pure-transform and behavior tests for :mod:`src.load_aop`.

Covers column resolution (exact/reordered/fuzzy/missing-required/extras), the
KEY reconcile branches as wired by AOP, per-row validation (pass/fail/empty/
duplicate-warn), sentinel cleaning, transform-after-validation ordering, and
hypothesis property tests for the pure AOP functions. I/O, persistence, and CLI
tests live in ``test_load_aop_io.py``. All Excel fixtures are built in-memory via
``io.BytesIO``; no temporary files are created on disk.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.load_aop import (
    EXPECTED_COLUMNS,
    MONTHS,
    SOURCE_COLUMNS,
    clean_label_sentinels,
    coerce_numeric,
    load_aop,
    validate_aop,
)
from tests.aop_fixtures import (
    aop_header_without_key,
    build_aop_workbook,
    loaded_aop_frame,
    make_aop_row,
)
from tests.le_fixtures import as_float

# ---------------------------------------------------------------------------
# Column resolution
# ---------------------------------------------------------------------------


def test_resolution_exact_by_position() -> None:
    """An in-order header resolves to all canonical columns by position."""
    # Arrange
    rows = [
        make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
    ]

    # Act
    frame = loaded_aop_frame(rows)

    # Assert: every expected column plus the established KEY is present.
    for column in EXPECTED_COLUMNS:
        assert column in frame.columns
    assert "KEY" in frame.columns


def test_resolution_reordered_columns() -> None:
    """A reordered header still resolves to the canonical names by name."""
    # Arrange: reverse the non-KEY header order.
    reordered = list(reversed(aop_header_without_key()))
    rows = [make_aop_row(customer="A", sku=1, type_="T", months=[2.0] * 12)]
    buffer = build_aop_workbook(rows, header=reordered)

    # Act
    frame = load_aop(buffer, sheet="AOP1")

    # Assert
    assert frame.iloc[0]["Customer"] == "A"
    assert float(frame.iloc[0]["YTD"]) == 24.0


def test_resolution_fuzzy_match_above_threshold() -> None:
    """A minor typographic variant resolves via the fuzzy pass (>= 0.85)."""
    # Arrange: introduce a small typo in a header label that should still bind.
    header = aop_header_without_key()
    header[header.index("Customer Master")] = "Customer Mastor"
    rows = [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    buffer = build_aop_workbook(rows, header=header)

    # Act
    frame = load_aop(buffer, sheet="AOP1")

    # Assert: the canonical name is bound despite the source typo.
    assert "Customer Master" in frame.columns


def test_resolution_missing_required_column_raises() -> None:
    """A header missing a required column halts with a ValueError naming it."""
    # Arrange: drop the PPG column so resolution cannot bind it.
    bad_header = [c for c in aop_header_without_key() if c != "PPG"]
    rows = [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    buffer = build_aop_workbook(rows, header=bad_header)

    # Act / Assert
    with pytest.raises(ValueError, match="PPG"):
        load_aop(buffer, sheet="AOP1")


def test_resolution_extra_column_warns_and_continues(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An extra unexpected column is logged as a warning and processing continues."""
    # Arrange: append an unexpected column to the header.
    header = [*aop_header_without_key(), "Unexpected Extra"]
    row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    row["Unexpected Extra"] = "noise"
    buffer = build_aop_workbook([row], header=header)

    # Act
    with caplog.at_level("WARNING", logger="src.load_aop"):
        frame = load_aop(buffer, sheet="AOP1")

    # Assert: a warning naming the extra column is emitted and the frame loads.
    assert any("extra source column" in r.message.lower() for r in caplog.records)
    assert len(frame) == 1
    assert "Unexpected Extra" not in frame.columns


def test_optional_key_located_by_name_only() -> None:
    """A present KEY column is located by name and excluded from required set."""
    # Arrange: include KEY in the header with a value matching the rebuilt pattern.
    header = SOURCE_COLUMNS
    rows = [
        make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12, key="A1T"),
    ]
    buffer = build_aop_workbook(rows, header=header)

    # Act: trust the matching KEY without consulting the policy.
    frame = load_aop(buffer, sheet="AOP1")

    # Assert
    assert frame.iloc[0]["KEY"] == "A1T"


# ---------------------------------------------------------------------------
# KEY reconcile branches (AOP wiring of resolve_key)
# ---------------------------------------------------------------------------


def test_key_absent_create_branch() -> None:
    """With no KEY column, KEY is created from the rebuilt pattern."""
    # Arrange / Act
    frame = loaded_aop_frame(
        [make_aop_row(customer="Cust", sku=7, type_="GS", months=[1.0] * 12)]
    )

    # Assert
    assert frame.iloc[0]["KEY"] == "Cust7GS"


def test_key_present_matching_trust_branch() -> None:
    """A present KEY equal to the rebuilt pattern is trusted as-is."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="Cust7GS"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    frame = load_aop(buffer, sheet="AOP1")

    # Assert
    assert frame.iloc[0]["KEY"] == "Cust7GS"


def test_key_diverging_trust_branch_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A diverging KEY under 'trust' keeps the existing value and warns."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="LEGACY"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        frame = load_aop(buffer, sheet="AOP1", key_mismatch="trust")

    # Assert
    assert frame.iloc[0]["KEY"] == "LEGACY"
    assert any("trust" in r.message.lower() for r in caplog.records)


def test_key_diverging_overwrite_branch_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A diverging KEY under 'overwrite' is replaced and warns."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="LEGACY"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        frame = load_aop(buffer, sheet="AOP1", key_mismatch="overwrite")

    # Assert
    assert frame.iloc[0]["KEY"] == "Cust7GS"
    assert any("overwrit" in r.message.lower() for r in caplog.records)


def test_key_diverging_prompt_non_tty_raises() -> None:
    """A diverging KEY under default 'prompt' on non-TTY stdin raises ValueError."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="LEGACY"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act / Assert: non-interactive prompt fails fast naming the remedy flag.
    with pytest.raises(ValueError, match="--key-mismatch"):
        load_aop(buffer, sheet="AOP1", key_mismatch="prompt", is_tty=lambda: False)


# ---------------------------------------------------------------------------
# Per-row validation
# ---------------------------------------------------------------------------


def test_validation_passing_case() -> None:
    """A frame whose totals tie out passes validation without raising."""
    # Arrange / Act: well-formed rows whose totals equal their month sums.
    frame = loaded_aop_frame(
        [
            make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
            make_aop_row(customer="B", sku=2, type_="T", months=[3.0] * 12),
        ]
    )

    # Assert: validation is a no-op on an already-loaded (validated) frame.
    assert validate_aop(frame) is None


def test_validation_failing_case_aggregates_failures() -> None:
    """Multiple per-row identity violations raise a single aggregated ValueError."""
    # Arrange: load a valid frame, then perturb YTD and Q1 to break two identities.
    frame = loaded_aop_frame(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    )
    frame.loc[frame.index[0], "YTD"] = as_float(frame.loc[frame.index[0], "YTD"]) + 5.0
    frame.loc[frame.index[0], "Q1"] = as_float(frame.loc[frame.index[0], "Q1"]) + 9.0

    # Act / Assert: both YTD and Q1 are named in one error message.
    with pytest.raises(ValueError) as exc_info:
        validate_aop(frame)
    message = str(exc_info.value)
    assert "YTD" in message
    assert "Q1" in message


def test_validation_empty_frame_raises() -> None:
    """A frame with zero data rows fails the row-count check."""
    # Arrange: an empty frame with the canonical columns and a KEY column.
    columns = [*SOURCE_COLUMNS]
    empty = pd.DataFrame({column: [] for column in columns})

    # Act / Assert
    with pytest.raises(ValueError, match="no data rows"):
        validate_aop(empty)


def test_validation_duplicate_key_warns_not_raises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Duplicate KEYs produce a WARNING and never raise."""
    # Arrange: two rows that rebuild to the same KEY (AOP does not collapse rows).
    frame = loaded_aop_frame(
        [
            make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
            make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
        ]
    )

    # Act: validate the already-loaded frame, capturing duplicate-KEY warnings.
    with caplog.at_level("WARNING", logger="src.load_aop"):
        result = validate_aop(frame)

    # Assert: no raise, both rows preserved, and a duplicate-KEY warning emitted.
    assert result is None
    assert len(frame) == 2
    assert any("duplicate key" in r.message.lower() for r in caplog.records)


def test_numeric_coercion_precedes_validation() -> None:
    """Text-typed numeric cells are coerced before validation so identities hold."""
    # Arrange: a frame whose numeric cells are strings; coercion must run first.
    frame = loaded_aop_frame(
        [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
    )
    # Re-introduce a string in a numeric cell to confirm coerce_numeric fixes it.
    frame["Jan"] = frame["Jan"].astype(object)
    frame.loc[frame.index[0], "Jan"] = "1.0"

    # Act
    coerced = coerce_numeric(frame)

    # Assert: the coerced cell parses to the expected float and validation passes.
    assert as_float(coerced.loc[coerced.index[0], "Jan"]) == 1.0
    assert validate_aop(coerced) is None


# ---------------------------------------------------------------------------
# Sentinel cleaning and transform ordering
# ---------------------------------------------------------------------------


def test_clean_label_sentinels_converts_sentinels_to_none() -> None:
    """0, "0", "#N/A", and NaN become None for the named label columns."""
    # Arrange: one row per sentinel encoding across Super Category and PPG.
    frame = pd.DataFrame(
        {
            "Super Category": [0, "0", "#N/A", float("nan"), "Keep"],
            "PPG": ["#N/A", float("nan"), 0, "0", "AlsoKeep"],
        }
    )

    # Act
    cleaned = clean_label_sentinels(frame, ["Super Category", "PPG"])

    # Assert: sentinels map to None; non-sentinel values are preserved.
    assert cleaned["Super Category"].tolist()[:4] == [None, None, None, None]
    assert cleaned["Super Category"].tolist()[4] == "Keep"
    assert cleaned["PPG"].tolist()[:4] == [None, None, None, None]
    assert cleaned["PPG"].tolist()[4] == "AlsoKeep"


def test_aop_does_not_apply_le_super_category_quirk() -> None:
    """AOP keeps Super Category independent of PPG (no LE quirk)."""
    # Arrange / Act: distinct Super Category and PPG values must remain distinct.
    frame = loaded_aop_frame(
        [
            make_aop_row(
                customer="A",
                sku=1,
                type_="T",
                months=[1.0] * 12,
                super_category="CatX",
                ppg="GroupY",
            )
        ]
    )

    # Assert: Super Category is not overwritten by PPG.
    assert frame.iloc[0]["Super Category"] == "CatX"
    assert frame.iloc[0]["PPG"] == "GroupY"


def test_transform_applied_after_validation_and_before_return() -> None:
    """A caller transform runs only after validation passes, then is returned."""

    # Arrange: a transform that adds a derived column; it must see a validated frame.
    def add_marker(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Marker"] = "applied"
        return df

    # Act
    frame = load_aop(
        build_aop_workbook(
            [make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)]
        ),
        sheet="AOP1",
        transform=add_marker,
    )

    # Assert: the transform-added column is present on the returned frame.
    assert frame.iloc[0]["Marker"] == "applied"


def test_transform_not_applied_when_validation_fails() -> None:
    """A transform is never applied when validation fails (ordering guarantee)."""
    # Arrange: a transform that records whether it ran, plus a broken-total source.
    calls: list[int] = []

    def recording_transform(df: pd.DataFrame) -> pd.DataFrame:
        calls.append(1)
        return df

    # A row whose YTD does not equal sum(months) fails validation before transform.
    bad_row = make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12)
    bad_row["YTD"] = 999.0
    buffer = build_aop_workbook([bad_row], header=aop_header_without_key())

    # Act / Assert
    with pytest.raises(ValueError, match="YTD"):
        load_aop(buffer, sheet="AOP1", transform=recording_transform)
    assert calls == []


def test_aop_does_not_collapse_rows_by_key() -> None:
    """AOP preserves every data row even when KEYs duplicate (no collapse)."""
    # Arrange / Act: three rows, two sharing a rebuilt KEY.
    frame = loaded_aop_frame(
        [
            make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
            make_aop_row(customer="A", sku=1, type_="T", months=[1.0] * 12),
            make_aop_row(customer="B", sku=2, type_="T", months=[2.0] * 12),
        ]
    )

    # Assert: all three rows survive (LE would collapse the first two).
    assert len(frame) == 3


# ---------------------------------------------------------------------------
# Property-based tests (T2: >= 1 per pure function)
# ---------------------------------------------------------------------------


@given(
    labels=st.lists(
        st.sampled_from([0, "0", "#N/A", float("nan"), "Real", "Other", 42, "x"]),
        min_size=1,
        max_size=8,
    )
)
def test_clean_label_sentinels_property(labels: list[object]) -> None:
    """Every sentinel maps to None and every non-sentinel value is preserved."""
    # Arrange
    frame = pd.DataFrame({"Super Category": labels})
    sentinels = {0, "0", "#N/A"}

    # Act
    cleaned = clean_label_sentinels(frame, ["Super Category"])

    # Assert: position-by-position, a sentinel/NaN became None, else unchanged.
    for original, result in zip(labels, cleaned["Super Category"], strict=True):
        is_nan = isinstance(original, float) and math.isnan(original)
        if original in sentinels or is_nan:
            assert result is None
        else:
            assert result == original


@given(
    months=st.lists(
        st.floats(
            allow_nan=False,
            allow_infinity=False,
            min_value=-1e6,
            max_value=1e6,
            width=32,
        ),
        min_size=12,
        max_size=12,
    )
)
def test_coerce_numeric_property(months: list[float]) -> None:
    """coerce_numeric yields float-typed numeric columns with no NaN remaining."""
    # Arrange: a one-row frame with all numeric columns derived from months.
    record: dict[str, object] = dict(zip(MONTHS, months, strict=True))
    record["YTD"] = sum(months)
    record["Q1"] = sum(months[0:3])
    record["Q2"] = sum(months[3:6])
    record["Q3"] = sum(months[6:9])
    record["Q4"] = sum(months[9:12])
    record["YTG"] = sum(months[4:12])
    frame = pd.DataFrame([record])

    # Act
    coerced = coerce_numeric(frame)

    # Assert: the coerced YTD is a finite float equal to the month sum (tol).
    ytd = as_float(coerced.loc[coerced.index[0], "YTD"])
    assert math.isfinite(ytd)
    assert math.isclose(ytd, sum(months), abs_tol=1e-6, rel_tol=1e-9)
