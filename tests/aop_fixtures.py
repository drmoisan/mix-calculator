"""Shared in-memory test fixtures and helpers for the load-aop test suite.

All Excel source fixtures are built in-memory via ``io.BytesIO`` and openpyxl;
all SQLite round-trips reuse the ``PersistentConnection``/``patch_connect``
helpers from ``tests.le_fixtures`` with ``sqlite3.connect(":memory:")``. No
temporary files are created on disk, per the repository unit-test policy.

This module holds the AOP-specific builders shared between the transform test
module (``test_load_aop.py``) and the I/O/CLI test module
(``test_load_aop_io.py``) so the behavior is defined once. The SQLite helpers
(``PersistentConnection``, ``patch_connect``, ``read_table``) are reused from
``tests.le_fixtures`` rather than duplicated.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from openpyxl import Workbook

from src.load_aop import MONTHS, SOURCE_COLUMNS, load_aop

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    import pandas as pd
    import pytest


def aop_header_without_key() -> list[str]:
    """Return the AOP source header with the optional ``KEY`` column removed.

    Returns:
        A copy of :data:`src.load_aop.SOURCE_COLUMNS` excluding ``"KEY"``,
        preserving order.
    """
    return [column for column in SOURCE_COLUMNS if column != "KEY"]


def make_aop_row(
    *,
    customer: object,
    sku: object,
    type_: str,
    months: Sequence[float | None],
    customer_master: str = "Master Co",
    description: str = "Some Description",
    super_category: object = "SuperCat",
    ppg: object = "PPGroup",
    key: str | None = None,
    blank_totals: bool = False,
) -> dict[str, object]:
    """Build a single AOP source-row dict keyed by :data:`SOURCE_COLUMNS`.

    Args:
        customer: Customer cell value (``None`` simulates a blank row that the
            blank-``Customer`` filter drops).
        sku: SKU value (int, float, or string code).
        type_: Type segment of the key.
        months: The 12 monthly values, Jan..Dec.
        customer_master: Customer Master cell value.
        description: SKU Descripiton text (typo intentional, preserved verbatim).
        super_category: Super Category cell value (may be a sentinel such as
            ``0``/``"0"``/``"#N/A"``/``None``).
        ppg: PPG cell value (same sentinel caveat as Super Category).
        key: Optional ``KEY`` cell value. ``None`` (the default) means the row
            carries no KEY cell; the default workbook header therefore omits the
            ``KEY`` column so KEY is created from the rebuilt pattern.
        blank_totals: When ``True``, leave the ``YTD``/``Q1``..``Q4``/``YTG``
            cells blank (``None``) to reproduce the source quirk where totals are
            omitted while the monthly columns are populated. When ``False`` (the
            default), each total is set to the sum of its constituent months.

    Returns:
        A dict mapping every AOP source column to a cell value.
    """
    record: dict[str, object] = {
        "KEY": key,
        "Customer": customer,
        "SKU Descripiton": description,
        "SKU #": sku,
        "Customer Master": customer_master,
        "Type": type_,
        "Super Category": super_category,
        "PPG": ppg,
    }
    # Populate the 12 monthly columns from the supplied vector.
    for index, month in enumerate(MONTHS):
        record[month] = months[index]

    # Either omit the totals (blank-cell quirk) or set each to its month sum so a
    # well-formed row ties out under the per-row identity checks.
    if blank_totals:
        for total in ("YTD", "Q1", "Q2", "Q3", "Q4", "YTG"):
            record[total] = None
    else:
        record["YTD"] = _month_sum(months)
        record["Q1"] = _month_sum(months[0:3])
        record["Q2"] = _month_sum(months[3:6])
        record["Q3"] = _month_sum(months[6:9])
        record["Q4"] = _month_sum(months[9:12])
        record["YTG"] = _month_sum(months[4:12])
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


def build_aop_workbook(
    rows: list[dict[str, object]],
    sheet_name: str = "AOP1",
    header: list[str] | None = None,
) -> io.BytesIO:
    """Build an in-memory ``.xlsx`` matching the AOP source layout.

    The sheet has two leading non-data rows, the header on Excel row 3, and the
    data rows beginning on row 4. The data cells are written in the order of the
    chosen header so a reordered or pruned header produces a correspondingly
    reordered/pruned workbook (used by the column-resolution tests).

    The default header omits the optional ``KEY`` column (so the absent-KEY
    branch is the baseline). Pass an explicit ``header`` that includes ``"KEY"``
    to exercise the present-KEY branches.

    Args:
        rows: AOP source-row dicts (see :func:`make_aop_row`).
        sheet_name: Name of the worksheet to create.
        header: Optional explicit header row; defaults to the source columns with
            the ``KEY`` column removed. Cells are emitted in this header's order.

    Returns:
        A ``BytesIO`` positioned at offset 0 containing the workbook bytes.
    """
    columns = header if header is not None else aop_header_without_key()
    workbook = Workbook()
    worksheet = workbook.active
    assert worksheet is not None
    worksheet.title = sheet_name

    # Two leading padding rows precede the header on Excel row 3.
    worksheet.append(["leading note row 1"])
    worksheet.append(["leading note row 2"])
    worksheet.append(columns)

    # Append each data row in the chosen header's column order so the on-sheet
    # layout matches the (possibly reordered/pruned) header exactly.
    for record in rows:
        worksheet.append([record.get(column) for column in columns])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def loaded_aop_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    """Build an AOP workbook from rows and return the loaded (validated) frame.

    Args:
        rows: AOP source-row dicts (see :func:`make_aop_row`).

    Returns:
        The validated AOP DataFrame produced by ``load_aop`` (canonical column
        names with an established ``KEY``).

    Notes:
        The default workbook omits the optional ``KEY`` column, so KEY is created
        from the rebuilt pattern (the absent-KEY branch) without consulting the
        ``--key-mismatch`` policy or stdin.
    """
    return load_aop(build_aop_workbook(rows), sheet="AOP1")


def patch_load_aop(
    monkeypatch: pytest.MonkeyPatch,
    buffer: io.BytesIO,
    *,
    is_tty: bool = False,
    prompt: Callable[[str], str] | None = None,
) -> None:
    """Patch ``src.load_aop.load_aop`` to read the in-memory workbook.

    Forwards the ``key_mismatch`` policy and injects deterministic interactivity
    seams (``is_tty``/``prompt``) so the CLI path never touches real stdin. The
    patched callable matches the ``main`` call site, which invokes
    ``load_aop(input, sheet=..., key_mismatch=...)``.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        buffer: The in-memory ``.xlsx`` buffer to load instead of a path.
        is_tty: The interactive-TTY flag injected into ``load_aop``.
        prompt: Optional prompt callable injected into ``load_aop``; when
            ``None`` a callable that raises is used so an unexpected prompt
            surfaces loudly instead of blocking.
    """

    def _raising_prompt(_message: str) -> str:
        raise AssertionError("prompt should not be invoked in this test path")

    chosen_prompt = prompt if prompt is not None else _raising_prompt

    def _fake_load_aop(
        _path: str, *, sheet: str = "AOP1", key_mismatch: str = "prompt"
    ) -> pd.DataFrame:
        # Rewind so repeated reads of the shared buffer succeed.
        buffer.seek(0)
        return load_aop(
            buffer,
            sheet=sheet,
            key_mismatch=key_mismatch,
            is_tty=lambda: is_tty,
            prompt=chosen_prompt,
        )

    monkeypatch.setattr("src.load_aop.load_aop", _fake_load_aop)
