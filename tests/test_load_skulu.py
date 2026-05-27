"""Unit tests for :mod:`src.load_skulu`.

Covers ``load_skulu`` (the ``International`` -> ``Country`` rename, the
``"0"`` -> ``"US"`` / ``"1"`` -> ``"Canada"`` country mapping, and the text
casts) using an in-memory ``BytesIO`` Excel fixture, and ``persist_skulu`` using
an in-memory ``sqlite3.connect(":memory:")`` connection. No temporary files are
created. Fixtures use fabricated SKU codes, descriptions, and categories only;
no confidential values appear.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from openpyxl import Workbook

from src.load_skulu import EXPECTED_COLUMNS, load_skulu, persist_skulu
from src.pandas_io import read_table
from tests.le_fixtures import patch_connect

if TYPE_CHECKING:
    import pytest


def _build_skulu_workbook(
    rows: list[dict[str, object]],
    *,
    sheet_name: str = "SKU_LU",
    header: list[str] | None = None,
) -> io.BytesIO:
    """Build an in-memory SKU_LU workbook with the header on Excel row 1.

    Args:
        rows: SKU lookup row dicts keyed by the source column labels.
        sheet_name: Worksheet name (default ``"SKU_LU"``).
        header: Optional explicit header order; defaults to the canonical columns.

    Returns:
        A ``BytesIO`` positioned at offset 0 containing the workbook bytes.
    """
    columns = header if header is not None else list(EXPECTED_COLUMNS)
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet_name

    # The SKU_LU sheet places its header on row 1, so it is the first appended
    # row, followed directly by the data rows.
    worksheet.append(columns)
    for record in rows:
        worksheet.append([record.get(column) for column in columns])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def _fabricated_rows() -> list[dict[str, object]]:
    """Return fabricated SKU lookup rows covering both country codes."""
    return [
        {
            "SKU": "SKU-001",
            "SKU Description": "Widget A",
            "Category": "Category X",
            "International": 0,
        },
        {
            "SKU": "SKU-002",
            "SKU Description": "Widget B",
            "Category": "Category Y",
            "International": 1,
        },
    ]


def test_load_skulu_renames_international_to_country() -> None:
    """load_skulu renames the International column to Country."""
    # Arrange
    buffer = _build_skulu_workbook(_fabricated_rows())

    # Act
    frame = load_skulu(buffer, sheet="SKU_LU")

    # Assert
    assert "Country" in frame.columns
    assert "International" not in frame.columns
    assert list(frame.columns) == ["SKU", "SKU Description", "Category", "Country"]


def test_load_skulu_maps_country_codes() -> None:
    """Country codes 0 and 1 map to US and Canada respectively."""
    # Arrange
    buffer = _build_skulu_workbook(_fabricated_rows())

    # Act
    frame = load_skulu(buffer, sheet="SKU_LU")

    # Assert
    by_sku = frame.set_index("SKU")["Country"]
    assert by_sku.loc["SKU-001"] == "US"
    assert by_sku.loc["SKU-002"] == "Canada"


def test_load_skulu_casts_columns_to_text() -> None:
    """The four lookup columns are cast to text."""
    # Arrange
    buffer = _build_skulu_workbook(_fabricated_rows())

    # Act
    frame = load_skulu(buffer, sheet="SKU_LU")

    # Assert: every value in each column is a Python string after the cast.
    for column in ("SKU", "SKU Description", "Category", "Country"):
        assert all(isinstance(value, str) for value in frame[column])


def test_load_skulu_resolves_reordered_header() -> None:
    """A reordered source header still resolves to the canonical columns."""
    # Arrange: reverse the header order.
    reordered = list(reversed(EXPECTED_COLUMNS))
    buffer = _build_skulu_workbook(_fabricated_rows(), header=reordered)

    # Act
    frame = load_skulu(buffer, sheet="SKU_LU")

    # Assert
    assert list(frame.columns) == ["SKU", "SKU Description", "Category", "Country"]
    assert frame.set_index("SKU")["Country"].loc["SKU-002"] == "Canada"


def test_load_skulu_warns_on_extra_column() -> None:
    """An extra unexpected source column is dropped (and triggers the warning path)."""
    # Arrange: append an unexpected column to the header and rows.
    header = [*EXPECTED_COLUMNS, "Unexpected Extra"]
    rows = _fabricated_rows()
    for record in rows:
        record["Unexpected Extra"] = "noise"
    buffer = _build_skulu_workbook(rows, header=header)

    # Act
    frame = load_skulu(buffer, sheet="SKU_LU")

    # Assert: the extra column is not carried into the resolved frame.
    assert "Unexpected Extra" not in frame.columns
    assert list(frame.columns) == ["SKU", "SKU Description", "Category", "Country"]


def test_persist_skulu_round_trips_through_sqlite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """persist_skulu writes the frame to SQLite and it reads back unchanged."""
    # Arrange: in-memory connection that survives the writer's close().
    con = patch_connect(monkeypatch)
    buffer = _build_skulu_workbook(_fabricated_rows())
    frame = load_skulu(buffer, sheet="SKU_LU")

    # Act
    persist_skulu(frame, ":memory:", table="sku_lu")
    read_back = read_table(con, "sku_lu")

    # Assert
    assert list(read_back.columns) == [
        "SKU",
        "SKU Description",
        "Category",
        "Country",
    ]
    assert len(read_back) == 2
    assert read_back.set_index("SKU")["Country"].loc["SKU-001"] == "US"
    con.real_close()
