"""Unit tests for :mod:`src.gui.exporters.csv_exporter`.

Verifies ``CsvExporter.export`` writes one CSV per selected table with correct
content, using an injected in-memory write seam (a ``StringIO``-backed
``open_writer``) so no temp files are created. Covers subset selection and the
``format_name`` value. Fabricated data only.
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
    """A ``StringIO`` whose ``close`` is a no-op so its value survives the with.

    ``CsvExporter.export`` writes inside a ``with`` block, which would close a
    real file. For the in-memory seam the captured text must remain readable
    after the block exits, so closing is suppressed; the test owns teardown.
    """

    def close(self) -> None:
        """Suppress closing so the captured CSV text persists for assertions."""
        return None


def _capturing_open_writer() -> (
    tuple[dict[str, _NonClosingStringIO], Callable[[str], IO[str]]]
):
    """Return a (captures, open_writer) pair for capturing per-path CSV text.

    Returns:
        A tuple of the captures dict (keyed by path) and an ``open_writer``
        callable that records each path's text sink without touching disk.
    """
    captures: dict[str, _NonClosingStringIO] = {}

    def _open_writer(path: str) -> IO[str]:
        # Record one in-memory sink per requested path so the test can read back
        # the CSV text without any file on disk.
        sink = _NonClosingStringIO()
        captures[path] = sink
        return sink

    return captures, _open_writer


def _fabricated_tables() -> dict[str, pd.DataFrame]:
    """Return a fabricated two-table set for CSV export tests."""
    return {
        "le_wide": pd.DataFrame({"KEY": ["k1", "k2"], "FY": [10.0, 20.0]}),
        "mix_rollup_4": pd.DataFrame({"value": [42.0]}),
    }


def test_format_name_is_csv() -> None:
    """The exporter reports the CSV format name."""
    # Arrange / Act / Assert
    assert CsvExporter().format_name == "CSV"


def test_export_writes_one_csv_per_selected_table() -> None:
    """export writes one CSV per selected name with correct content."""
    # Arrange: an in-memory write seam so no temp files are created.
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    # Act
    exporter.export(tables, ["le_wide", "mix_rollup_4"], "out-dir")

    # Assert: one CSV per selected table at the expected path with round-trip content.
    le_path = os.path.join("out-dir", "le_wide.csv")
    rollup_path = os.path.join("out-dir", "mix_rollup_4.csv")
    assert set(captures) == {le_path, rollup_path}
    le_back = pd.read_csv(io.StringIO(captures[le_path].getvalue()))
    pd.testing.assert_frame_equal(le_back, tables["le_wide"])


def test_export_subset_excludes_unselected_tables() -> None:
    """Only the selected table produces a CSV."""
    # Arrange
    captures, open_writer = _capturing_open_writer()
    exporter = CsvExporter(open_writer=open_writer)
    tables = _fabricated_tables()

    # Act: select only one table.
    exporter.export(tables, ["mix_rollup_4"], "out-dir")

    # Assert
    assert set(captures) == {os.path.join("out-dir", "mix_rollup_4.csv")}


def test_default_writer_opens_path_for_text_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default (production) exporter opens each CSV path for UTF-8 text.

    Exercises the default text-sink path through the public ``CsvExporter`` (no
    injected writer) by patching ``builtins.open`` to return an in-memory sink,
    so no file is created on disk while the production open is verified.
    """
    # Arrange: capture the open() call args and return an in-memory sink so no
    # file is created on disk. A default CsvExporter uses the real-file opener.
    recorded: list[tuple[str, str, str]] = []

    def _fake_open(path: str, mode: str, *, encoding: str, newline: str) -> io.StringIO:
        recorded.append((path, mode, encoding))
        return io.StringIO()

    monkeypatch.setattr("builtins.open", _fake_open)
    exporter = CsvExporter()

    # Act
    exporter.export(_fabricated_tables(), ["mix_rollup_4"], "results")

    # Assert: the production path opened the CSV for text writing in UTF-8.
    assert recorded == [(os.path.join("results", "mix_rollup_4.csv"), "w", "utf-8")]
