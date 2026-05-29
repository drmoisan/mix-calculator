"""Fake exporter implementing :class:`ExporterProtocol` for registry/presenter tests.

The fake records each ``export`` call (no I/O) so tests can assert which tables
and destination an exporter received without writing files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class ExportCall:
    """A single recorded ``export`` invocation.

    Attributes:
        selected_names: The table names passed to ``export``.
        destination_path: The destination path passed to ``export``.
        table_names: The keys of the ``tables`` mapping passed to ``export``.
    """

    selected_names: list[str]
    destination_path: str
    table_names: list[str]


class FakeExporter:
    """In-memory exporter that records calls instead of writing files.

    Purpose:
        Satisfy :class:`~src.gui.exporters.base.ExporterProtocol` for registry
        and export-presenter tests without touching the filesystem.

    Responsibilities:
        Report a fixed ``format_name`` and record every ``export`` invocation.

    Attributes:
        calls: The recorded ``export`` invocations, in call order.
    """

    def __init__(self, format_name: str = "Fake") -> None:
        """Initialize the fake with a format name.

        Args:
            format_name: The format identifier this fake reports.
        """
        self._format_name = format_name
        self.calls: list[ExportCall] = []

    @property
    def format_name(self) -> str:
        """Return the configured format name."""
        return self._format_name

    def export(
        self,
        tables: dict[str, pd.DataFrame],
        selected_names: list[str],
        destination_path: str,
    ) -> None:
        """Record the export call without performing any I/O.

        Args:
            tables: All available tables keyed by name.
            selected_names: The subset of table names to export.
            destination_path: The destination path.

        Returns:
            ``None``.
        """
        # Record the call so tests can assert on the selection and destination.
        self.calls.append(
            ExportCall(
                selected_names=list(selected_names),
                destination_path=destination_path,
                table_names=list(tables),
            )
        )
