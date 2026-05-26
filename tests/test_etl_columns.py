"""Tests for position-independent column resolution (:mod:`src.etl_columns`).

Covers ``normalize_name`` and the pure ``resolve_columns`` resolver
(exact-by-position, reordered-by-name, fuzzy >= 0.85, missing-required halt, and
extras), plus a ``load_source``-level test asserting the extra-column warning is
emitted. All Excel fixtures are built in-memory via ``io.BytesIO``; no temporary
files are created on disk.
"""

from __future__ import annotations

import logging

import pytest

from src.etl_columns import normalize_name, resolve_columns
from src.normalize_le import EXPECTED_COLUMNS, SOURCE_COLUMNS, load_source
from tests.le_fixtures import build_workbook, make_row, source_header_without_key

# ---------------------------------------------------------------------------
# normalize_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("SKU #", "sku"),
        ("Customer ", "customer"),
        ("GtN Mapping", "gtnmapping"),
        ("YTD/YTG", "ytdytg"),
        ("KEY", "key"),
        ("Super Category", "supercategory"),
    ],
)
def test_normalize_name_strips_case_space_punctuation(raw: str, expected: str) -> None:
    """normalize_name lower-cases and removes whitespace and punctuation."""
    # Act / Assert
    assert normalize_name(raw) == expected


# ---------------------------------------------------------------------------
# resolve_columns
# ---------------------------------------------------------------------------


def test_resolve_columns_exact_by_position() -> None:
    """Columns already in canonical order resolve identity with no extras."""
    # Arrange / Act
    mapping, extras = resolve_columns(list(EXPECTED_COLUMNS), EXPECTED_COLUMNS)

    # Assert
    assert extras == []
    assert all(mapping[column] == column for column in EXPECTED_COLUMNS)


def test_resolve_columns_reordered_resolved_by_name() -> None:
    """A reversed column order still resolves each expected column by name."""
    # Arrange: reverse the actual column order so the position pass mostly misses.
    reordered = list(reversed(EXPECTED_COLUMNS))

    # Act
    mapping, extras = resolve_columns(reordered, EXPECTED_COLUMNS)

    # Assert: every expected column binds to its same-named actual column.
    assert extras == []
    assert all(mapping[column] == column for column in EXPECTED_COLUMNS)


def test_resolve_columns_trailing_space_variant_resolved() -> None:
    """A trailing-space variant of an expected column resolves by normalization."""
    # Arrange: replace "Customer" with "Customer " (trailing space).
    actual = ["Customer " if c == "Customer" else c for c in EXPECTED_COLUMNS]

    # Act
    mapping, extras = resolve_columns(actual, EXPECTED_COLUMNS)

    # Assert
    assert extras == []
    assert mapping["Customer"] == "Customer "


def test_resolve_columns_typo_resolved_by_fuzzy() -> None:
    """A near-miss typo resolves via the fuzzy pass at the >= 0.85 threshold."""
    # Arrange: "GtN Mappingg" is a one-character variant of "GtN Mapping".
    actual = ["GtN Mappingg" if c == "GtN Mapping" else c for c in EXPECTED_COLUMNS]

    # Act
    mapping, extras = resolve_columns(actual, EXPECTED_COLUMNS)

    # Assert: the variant binds and no genuine column is left over.
    assert extras == []
    assert mapping["GtN Mapping"] == "GtN Mappingg"


def test_resolve_columns_missing_required_raises_naming_column() -> None:
    """A genuinely missing required column raises ValueError naming it."""
    # Arrange: drop "PPG" entirely from the actual columns.
    actual = [c for c in EXPECTED_COLUMNS if c != "PPG"]

    # Act / Assert
    with pytest.raises(ValueError, match="PPG"):
        resolve_columns(actual, EXPECTED_COLUMNS)


def test_resolve_columns_extra_column_returned_as_extra() -> None:
    """An unmatched actual column is returned in extras after all required match."""
    # Arrange: append an extra column that no expected column claims.
    actual = [*EXPECTED_COLUMNS, "UnexpectedExtra"]

    # Act
    mapping, extras = resolve_columns(actual, EXPECTED_COLUMNS)

    # Assert
    assert extras == ["UnexpectedExtra"]
    assert all(mapping[column] == column for column in EXPECTED_COLUMNS)


def test_resolve_columns_unrelated_column_not_force_bound() -> None:
    """A genuinely unrelated column is not force-bound to a missing required one."""
    # Arrange: drop "PPG" and add a clearly dissimilar column; the dissimilar
    # column must not be bound to PPG below the 0.85 threshold.
    actual = [c for c in EXPECTED_COLUMNS if c != "PPG"]
    actual.append("ZZZ-totally-unrelated-9999")

    # Act / Assert: PPG remains unmatched, so the resolver halts.
    with pytest.raises(ValueError, match="PPG"):
        resolve_columns(actual, EXPECTED_COLUMNS)


# ---------------------------------------------------------------------------
# load_source-level resolution behavior
# ---------------------------------------------------------------------------


def test_load_source_reordered_columns_resolve_to_canonical() -> None:
    """A shuffled source header still yields canonical columns after load."""
    # Arrange: build a workbook whose header omits KEY and is reversed.
    header = list(reversed(source_header_without_key()))
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    buffer = build_workbook(rows, header=header)

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert: downstream sees canonical names regardless of source order
    # (KEY is created from the pattern since the source omitted it).
    assert set(frame.columns) == set(SOURCE_COLUMNS)
    assert frame.iloc[0]["Customer"] == "CustA"


def test_load_source_logs_warning_for_extra_columns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An extra source column is logged as a warning and the run continues."""
    # Arrange: append an unexpected column to the (no-KEY) header.
    header = [*source_header_without_key(), "UnexpectedExtra"]
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    buffer = build_workbook(rows, header=header)

    # Act
    with caplog.at_level(logging.WARNING, logger="src.normalize_le"):
        frame = load_source(buffer, "LE-8 + 4")

    # Assert: the warning names the extra column and the frame is still produced.
    assert any("UnexpectedExtra" in record.message for record in caplog.records)
    assert frame.iloc[0]["Customer"] == "CustA"
    assert "UnexpectedExtra" not in frame.columns
