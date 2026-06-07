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

from openpyxl import Workbook

from src.normalize_le import (
    MONTH_COLUMNS,
    SOURCE_COLUMNS,
    load_source,
    normalize,
)
from src.pandas_io import read_table as pandas_io_read_table

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import pandas as pd
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

    Thin wrapper over :func:`src.pandas_io.read_table`. It exists so the test
    suite imports the read helper from this fixtures module alongside the other
    shared helpers; the typed pandas boundary (and identifier quoting) lives in
    ``src.pandas_io`` so the read here carries no type suppression.

    Args:
        con: An open SQLite connection.
        table_name: The table to read.

    Returns:
        The table contents as a typed ``pd.DataFrame``.
    """
    return pandas_io_read_table(con, table_name)


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
    *,
    is_tty: bool = False,
    prompt: Callable[[str], str] | None = None,
) -> None:
    """Patch ``src.normalize_le.load_source`` to read the in-memory workbook.

    Forwards the ``key_mismatch`` policy and injects deterministic interactivity
    seams (``is_tty``/``prompt``) so the CLI path never touches real stdin.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        buffer: The in-memory ``.xlsx`` buffer to load instead of a path.
        is_tty: The interactive-TTY flag injected into ``load_source``.
        prompt: Optional prompt callable injected into ``load_source``; when
            ``None`` a callable that raises is used so an unexpected prompt
            surfaces loudly instead of blocking.
    """

    def _raising_prompt(_message: str) -> str:
        raise AssertionError("prompt should not be invoked in this test path")

    chosen_prompt = prompt if prompt is not None else _raising_prompt

    def _fake_load_source(
        _path: str, sheet: str, *, key_mismatch: str = "prompt"
    ) -> pd.DataFrame:
        # Rewind so repeated reads of the shared buffer succeed.
        buffer.seek(0)
        return load_source(
            buffer,
            sheet,
            key_mismatch=key_mismatch,
            is_tty=lambda: is_tty,
            prompt=chosen_prompt,
        )

    monkeypatch.setattr("src.normalize_le.load_source", _fake_load_source)


def make_row(
    *,
    customer: object,
    sku: object,
    type_: str,
    ppg: str,
    months: Sequence[float | None],
    ytd_ytg: str = "YTD",
    super_category: str = "SOURCE_SUPER_SHOULD_BE_IGNORED",
    description: str = "Some Description",
    gtn: str = "RollUp",
    key: str | None = None,
    blank_totals: bool = False,
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
        key: Optional ``KEY`` cell value. ``None`` (the default) means the row
            carries no KEY cell; the default workbook header therefore omits the
            ``KEY`` column so KEY is created from the rebuilt pattern. A present
            ``KEY`` is exercised by passing an explicit value together with a
            ``header`` that includes ``"KEY"``.
        blank_totals: When ``True``, leave the ``FY`` and ``Q1``..``Q4`` cells
            blank (``None``) to reproduce the source workbook quirk where those
            totals are omitted while the monthly columns are populated. When
            ``False`` (the default), each total is set to the sum of its months.

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

    # Either omit the totals (blank-cell quirk) or set each to its month sum.
    if blank_totals:
        record["FY"] = None
        record["Q1"] = None
        record["Q2"] = None
        record["Q3"] = None
        record["Q4"] = None
    else:
        record["FY"] = _month_sum(months)
        record["Q1"] = _month_sum(months[0:3])
        record["Q2"] = _month_sum(months[3:6])
        record["Q3"] = _month_sum(months[6:9])
        record["Q4"] = _month_sum(months[9:12])
    return record


def _month_sum(values: Sequence[float | None]) -> float:
    """Sum a slice of monthly values, treating ``None`` (a blank cell) as 0.

    Args:
        values: A slice of the twelve monthly values, where ``None`` represents
            a blank source cell.

    Returns:
        The float sum of the non-``None`` values.
    """
    # Blank monthly cells contribute 0, matching the load-time fill semantics.
    return float(sum(value for value in values if value is not None))


def build_workbook(
    rows: list[dict[str, object]],
    sheet_name: str = "LE-8 + 4",
    header: list[str] | None = None,
    *,
    leading_rows: int = 2,
) -> io.BytesIO:
    """Build an in-memory ``.xlsx`` matching the source layout.

    By default the sheet has two leading non-data rows, the header on Excel row 3
    (index 2), and the data rows beginning on row 4, reproducing the standard
    ``LE-8 + 4`` layout. The data cells are written in the order of the chosen
    header so a reordered or pruned header produces a correspondingly
    reordered/pruned workbook (used by the column-resolution tests).

    The default header omits the optional ``KEY`` column (so the absent-KEY
    branch is the baseline used across the suite). Pass an explicit ``header``
    that includes ``"KEY"`` to exercise the present-KEY branches.

    Args:
        rows: Source-row dicts (see :func:`make_row`).
        sheet_name: Name of the worksheet to create.
        header: Optional explicit header row; defaults to the source columns with
            the ``KEY`` column removed. Cells are emitted in this header's order.
        leading_rows: Number of leading non-data padding rows written before the
            header row. Defaults to ``2`` so the header lands on Excel row 3
            (index 2), preserving every existing caller's behavior. Pass
            ``leading_rows=0`` to produce a flat workbook whose header is on the
            first row (index 0).

    Returns:
        A ``BytesIO`` positioned at offset 0 containing the workbook bytes.
    """
    columns = header if header is not None else source_header_without_key()
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet_name

    # Write the requested number of leading padding rows before the header so the
    # header lands on index ``leading_rows`` (default 2 keeps the standard layout;
    # 0 produces a flat header-at-index-0 sheet).
    for note_index in range(leading_rows):
        worksheet.append([f"leading note row {note_index + 1}"])
    worksheet.append(columns)

    # Append each data row in the chosen header's column order so the on-sheet
    # layout matches the (possibly reordered/pruned) header exactly.
    for record in rows:
        worksheet.append([record.get(column) for column in columns])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def source_header_without_key() -> list[str]:
    """Return the source header with the optional ``KEY`` column removed.

    Returns:
        A copy of :data:`SOURCE_COLUMNS` excluding ``"KEY"``, preserving order.
    """
    return [column for column in SOURCE_COLUMNS if column != "KEY"]


def loaded_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build a workbook from rows and return the loaded (resolved) frame.

    Args:
        rows: Source-row dicts (see :func:`make_row`).

    Returns:
        The resolved source DataFrame as produced by ``load_source`` (canonical
        column names with an established ``KEY``).

    Notes:
        The default workbook omits the optional ``KEY`` column, so KEY is created
        from the rebuilt pattern (the absent-KEY branch) without consulting the
        ``--key-mismatch`` policy or stdin.
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
