"""Shared in-memory test fixtures and helpers for the normalize-le test suite.

All Excel source fixtures are built in-memory via ``io.BytesIO`` and openpyxl;
all SQLite round-trips use ``sqlite3.connect(":memory:")``. No temporary files
are created on disk, per the repository unit-test policy.

This module holds the helpers shared between the transform test module
(``test_normalize_le.py``) and the I/O/CLI test module
(``test_normalize_le_io.py``) so the behavior is defined once.
"""

from __future__ import annotations

import io
import math
import sqlite3
from typing import TYPE_CHECKING, cast

import pandas as pd
from openpyxl import Workbook

from src.normalize_le import (
    MONTH_COLUMNS,
    SOURCE_COLUMNS,
    load_source,
    normalize,
)

if TYPE_CHECKING:
    import pytest


def as_float(value: object) -> float:
    """Convert a pandas/numpy scalar to a built-in float for typed assertions.

    Args:
        value: A scalar pulled from a DataFrame cell (pandas ``Scalar``, numpy
            scalar, ``int``, ``float``, or numeric string).

    Returns:
        The value as a Python ``float``.
    """
    return float(cast("float", value))


def close(
    actual: object,
    expected: float,
    tol: float = 1e-6,
    rel: float = 1e-9,
) -> bool:
    """Return whether two numeric values are within tolerance.

    Used in place of ``pytest.approx`` because pytest's ``approx`` is untyped
    and produces partially-unknown comparison expressions under Pyright strict.
    Both an absolute and a relative tolerance are applied so large-magnitude
    floating-point sums (where an absolute floor is unreachable) still compare
    equal within rounding error.

    Args:
        actual: The observed value (any numeric scalar).
        expected: The expected float value.
        tol: Absolute tolerance.
        rel: Relative tolerance.

    Returns:
        ``True`` when the values are within either the absolute or relative
        tolerance.
    """
    return math.isclose(as_float(actual), expected, abs_tol=tol, rel_tol=rel)


def read_table(con: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    """Read a full table back from an open SQLite connection as a DataFrame.

    Args:
        con: An open SQLite connection.
        table_name: The table to read.

    Returns:
        The table contents as a typed ``pd.DataFrame``.
    """
    query = f'SELECT * FROM "{table_name}"'  # noqa: S608 - trusted test table name
    # pandas-stubs types read_sql's con union against an unstubbed connection
    # type, so the member resolves as partially unknown under Pyright strict.
    # The result is explicitly typed; the ignore is scoped to this read.
    result: pd.DataFrame = pd.read_sql(  # pyright: ignore[reportUnknownMemberType]
        query, con
    )
    return result


class PersistentConnection(sqlite3.Connection):
    """An in-memory SQLite connection whose ``close`` is a no-op.

    ``write_sqlite`` closes its connection in a ``finally`` block. For the
    in-memory round-trip tests the same connection must survive so the test can
    read the table back, so ``close`` is neutralized and the test owns the real
    teardown via :meth:`real_close`.
    """

    def close(self) -> None:
        """Suppress closing so the shared in-memory database persists."""
        return None

    def real_close(self) -> None:
        """Actually close the underlying connection (test teardown)."""
        super().close()


def patch_connect(monkeypatch: pytest.MonkeyPatch) -> PersistentConnection:
    """Patch ``sqlite3.connect`` to return a single shared in-memory connection.

    Args:
        monkeypatch: The pytest monkeypatch fixture.

    Returns:
        The shared in-memory connection that ``write_sqlite`` will reuse. The
        connection's ``close`` is a no-op; call ``real_close`` to tear down.
    """
    con = sqlite3.connect(":memory:", factory=PersistentConnection)

    def _fake_connect(_db_path: str) -> PersistentConnection:
        return con

    monkeypatch.setattr(sqlite3, "connect", _fake_connect)
    return con


def patch_load_source(
    monkeypatch: pytest.MonkeyPatch,
    buffer: io.BytesIO,
) -> None:
    """Patch ``src.normalize_le.load_source`` to read the in-memory workbook.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        buffer: The in-memory ``.xlsx`` buffer to load instead of a path.
    """

    def _fake_load_source(_path: str, sheet: str) -> pd.DataFrame:
        # Rewind so repeated reads of the shared buffer succeed.
        buffer.seek(0)
        return load_source(buffer, sheet)

    monkeypatch.setattr("src.normalize_le.load_source", _fake_load_source)


def make_row(
    *,
    customer: object,
    sku: object,
    type_: str,
    ppg: str,
    months: list[float],
    ytd_ytg: str = "YTD",
    super_category: str = "SOURCE_SUPER_SHOULD_BE_IGNORED",
    description: str = "Some Description",
    gtn: str = "RollUp",
    key: str = "STALE_KEY_VALUE",
) -> dict[str, object]:
    """Build a single source-row dict keyed by :data:`SOURCE_COLUMNS`.

    Args:
        customer: Customer cell value (``None`` simulates a blank row).
        sku: SKU value (int, float, numpy scalar, or string code).
        type_: Type segment of the key.
        ppg: Source PPG value (drives both output PPG and Super Category).
        months: The 12 monthly values, Jan..Dec.
        ytd_ytg: ``"YTD"`` or ``"YTG"`` marker (dropped on output).
        super_category: Source Super Category (must be ignored by the quirk).
        description: SKU Descripiton text (typo intentional).
        gtn: GtN Mapping text.
        key: A stale KEY cell value that must be ignored and rebuilt.

    Returns:
        A dict mapping every source column to a cell value.
    """
    record: dict[str, object] = {
        "KEY": key,
        "YTD/YTG": ytd_ytg,
        "Customer": customer,
        "SKU Descripiton": description,
        "SKU #": sku,
        "Type": type_,
        "GtN Mapping": gtn,
        "Super Category": super_category,
        "PPG": ppg,
    }
    # Populate the 12 monthly columns from the supplied vector.
    for index, month in enumerate(MONTH_COLUMNS):
        record[month] = months[index]
    record["FY"] = float(sum(months))
    record["Q1"] = float(sum(months[0:3]))
    record["Q2"] = float(sum(months[3:6]))
    record["Q3"] = float(sum(months[6:9]))
    record["Q4"] = float(sum(months[9:12]))
    return record


def build_workbook(
    rows: list[dict[str, object]],
    sheet_name: str = "LE-8 + 4",
    header: list[str] | None = None,
) -> io.BytesIO:
    """Build an in-memory ``.xlsx`` matching the source layout.

    The sheet has two leading non-data rows, the header on Excel row 3, and the
    data rows beginning on row 4.

    Args:
        rows: Source-row dicts (see :func:`make_row`).
        sheet_name: Name of the worksheet to create.
        header: Optional explicit header row; defaults to :data:`SOURCE_COLUMNS`.

    Returns:
        A ``BytesIO`` positioned at offset 0 containing the workbook bytes.
    """
    columns = header if header is not None else SOURCE_COLUMNS
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet_name

    # Two leading padding rows precede the header on Excel row 3.
    worksheet.append(["leading note row 1"])
    worksheet.append(["leading note row 2"])
    worksheet.append(columns)

    # Append each data row in source-column order.
    for record in rows:
        worksheet.append([record.get(column) for column in SOURCE_COLUMNS])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def loaded_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a workbook from rows and return the loaded (validated) frame.

    Args:
        rows: Source-row dicts (see :func:`make_row`).

    Returns:
        The validated source DataFrame as produced by ``load_source``.
    """
    return load_source(build_workbook(rows), "LE-8 + 4")


def normalized_sample() -> pd.DataFrame:
    """Return a small normalized frame with two unique keys.

    Returns:
        A normalized DataFrame containing two distinct KEYs.
    """
    frame = loaded_frame(
        [
            make_row(customer="CustB", sku=5, type_="GS", ppg="PX", months=[1.0] * 12),
            make_row(customer="CustA", sku=9, type_="Lbs", ppg="PY", months=[2.0] * 12),
        ]
    )
    return normalize(frame)
