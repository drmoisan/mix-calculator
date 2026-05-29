"""Unit tests for :mod:`src.gui.exporters.csv_exporter` (v2 name-mangling rule).

Verifies ``CsvExporter.export`` writes per-table CSV files using the v2
``<base>_<table>.csv`` naming rule (v2 Decision 1 / spec section 7). The
destination path is now interpreted as the user-chosen CSV file path, not a
directory; the base name is the filename minus a trailing ``.csv``
(case-insensitive). Tests use an injected in-memory write seam so no temp
files are created. Fabricated data only.
"""

from __future__ import annotations

import io
import os
from typing import IO, TYPE_CHECKING

import pandas as pd

from src.gui.exporters.csv_exporter import CsvExporter

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest


class _NonClosingStringIO(io.StringIO):
    """A ``StringIO`` whose ``close`` is a no-op so its value survives the with."""

    def close(self) -> None:
        """Suppress closing so the captured CSV text persists for assertions."""
        return None


def _capturing_open_writer() -> (
    tuple[dict[str, _NonClosingStringIO], Callable[[str], IO[str]]]
):
    """Return a (captures, open_writer) pair for capturing per-path CSV text."""
    captures: dict[str, _NonClosingStringIO] = {}

    def _open_writer(path: str) -> IO[str]:
        sink = _NonClosingStringIO()
        captures[path] = sink
        return sink

    return captures, _open_writer


def _fabricated_tables() -> dict[str, pd.DataFrame]:
    """Return a fabricated three-table set for CSV export tests."""
    return {
        "LE": pd.DataFrame({"KEY": ["k1", "k2"], "FY": [10.0, 20.0]}),
        "aop": pd.DataFrame({"KEY": ["k1"], "FY": [5.0]}),
        "sku_lu": pd.DataFrame({"SKU": ["SKU-001"]}),
    }


def test_format_name_is_csv() -> None:
    """The exporter reports the CSV format name."""
    assert CsvExporter().format_name == "CSV"


def test_export_one_table_writes_base_underscore_name_csv() -> None:
    """``results.csv`` + ``["LE"]`` writes ``C:/out/results_LE.csv``."""
    # Arrange
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    # Act
    exporter.export(tables, ["LE"], "C:/out/results.csv")

    # Assert: one file at directory C:/out with base "results" mangled with "LE".
    expected = os.path.join("C:/out", "results_LE.csv")
    assert set(captures) == {expected}


def test_export_three_tables_writes_three_mangled_files() -> None:
    """Three selected names yield three ``<base>_<name>.csv`` files."""
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    exporter.export(tables, ["LE", "aop", "sku_lu"], "C:/out/results.csv")

    expected = {
        os.path.join("C:/out", "results_LE.csv"),
        os.path.join("C:/out", "results_aop.csv"),
        os.path.join("C:/out", "results_sku_lu.csv"),
    }
    assert set(captures) == expected


def test_export_without_directory_writes_into_current_dir() -> None:
    """``results.csv`` with no directory writes ``results_LE.csv``."""
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    exporter.export(tables, ["LE"], "results.csv")

    assert set(captures) == {"results_LE.csv"}


def test_export_without_csv_extension_uses_filename_as_base() -> None:
    """A destination without ``.csv`` uses the filename unchanged as the base."""
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    exporter.export(tables, ["LE"], "C:/out/results")

    assert set(captures) == {os.path.join("C:/out", "results_LE.csv")}


def test_export_with_empty_selection_writes_nothing() -> None:
    """An empty ``selected_names`` produces no output and does not crash."""
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    exporter.export(tables, [], "C:/out/results.csv")

    assert captures == {}


def test_export_csv_extension_case_insensitive() -> None:
    """``.CSV`` (uppercase) is also stripped from the base name."""
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    exporter.export(tables, ["LE"], "C:/out/RESULTS.CSV")

    assert set(captures) == {os.path.join("C:/out", "RESULTS_LE.csv")}


def test_export_round_trip_content_for_one_table() -> None:
    """The written CSV round-trips through pandas back to the source frame."""
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    exporter.export(tables, ["LE"], "C:/out/results.csv")

    captured_path = os.path.join("C:/out", "results_LE.csv")
    le_back = pd.read_csv(io.StringIO(captures[captured_path].getvalue()))
    pd.testing.assert_frame_equal(le_back, tables["LE"])


def test_default_writer_opens_path_for_text_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default (production) exporter opens each CSV path for UTF-8 text."""
    recorded: list[tuple[str, str, str]] = []

    def _fake_open(path: str, mode: str, *, encoding: str, newline: str) -> io.StringIO:
        del newline  # production opener supplies newline=""
        recorded.append((path, mode, encoding))
        return io.StringIO()

    monkeypatch.setattr("builtins.open", _fake_open)
    exporter = CsvExporter()

    exporter.export(_fabricated_tables(), ["LE"], "C:/out/results.csv")

    expected = os.path.join("C:/out", "results_LE.csv")
    assert recorded == [(expected, "w", "utf-8")]
