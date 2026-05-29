"""Exporter abstraction for the mix-pipeline GUI export feature.

This module declares :class:`ExporterProtocol`, the contract every concrete
exporter (Excel, CSV, future formats) implements. Keeping the contract separate
from the registry and the concrete exporters lets the export presenter depend on
the abstraction and lets new formats be added by registering a new exporter with
no presenter change.

Responsibilities:
    - Define the exporter contract: a ``format_name`` identity and an ``export``
      operation over a selected subset of tables.

The Protocol carries no Qt import and no I/O; concrete exporters own the
file-writing side effects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pandas as pd

__all__ = ["ExporterProtocol"]


@runtime_checkable
class ExporterProtocol(Protocol):
    """Contract for a table exporter (one per output format).

    Purpose:
        Define the uniform surface the export presenter uses to write selected
        tables in a chosen format, so new formats are additive.

    Responsibilities:
        Identify the format via ``format_name`` and write the selected tables to
        a destination. Implementations own the file-writing side effects; the
        Protocol carries only the call surface.

    Usage:
        Concrete exporters are registered in an ``ExporterRegistry`` keyed by
        ``format_name`` and resolved by the export presenter.
    """

    @property
    def format_name(self) -> str:
        """Return the human-readable format identifier (for example ``"Excel"``).

        Returns:
            The format name used as the registry key and in the UI selector.
        """
        ...

    def export(
        self,
        tables: dict[str, pd.DataFrame],
        selected_names: list[str],
        destination_path: str,
    ) -> None:
        """Write the selected tables to the destination in this format.

        Args:
            tables: All available tables keyed by table name.
            selected_names: The subset of table names to export.
            destination_path: The destination file or directory path.

        Returns:
            ``None``.

        Side effects:
            Writes one or more files at ``destination_path``.
        """
        ...
