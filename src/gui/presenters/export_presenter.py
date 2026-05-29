"""Presenter for the export feature (table checklist + format selection).

This presenter drives a passive :class:`ExportViewProtocol` and resolves the
chosen export format from an injected :class:`ExporterRegistry`. It contains no
Qt import and is fully testable without a ``QApplication``. An export with no
tables selected is rejected before any exporter call.

Responsibilities:
    - ``set_available_tables`` pushes the exportable table names to the view.
    - ``on_select_all`` triggers the view's select-all.
    - ``on_export`` resolves the exporter, reads the selection, rejects an empty
      selection, then calls ``exporter.export``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

    from src.gui.exporters.registry import ExporterRegistry
    from src.gui.protocols import ExportViewProtocol

__all__ = ["ExportPresenter"]

logger = logging.getLogger(__name__)


class ExportPresenter:
    """Presenter coordinating the export checklist and format-driven export.

    Purpose:
        Translate export UI actions into registry lookups and exporter calls,
        keeping selection logic out of the view.

    Responsibilities:
        Push the available table names, trigger select-all, and run an export
        for the chosen format over the user's selection. It rejects an empty
        selection before any exporter call.

    Usage:
        Constructed with a view and an exporter registry at the composition root.
        Tables to export are supplied to :meth:`on_export`.

    Attributes:
        _view: The export view this presenter drives.
        _registry: The exporter registry resolving a format to an exporter.
        _available: The most recent available table names pushed to the view.
    """

    def __init__(
        self,
        view: ExportViewProtocol,
        registry: ExporterRegistry,
    ) -> None:
        """Initialize the presenter with its view and exporter registry.

        Args:
            view: The export view to drive.
            registry: The registry resolving a format name to an exporter.
        """
        self._view = view
        self._registry = registry
        self._available: list[str] = []

    def set_available_tables(self, names: list[str]) -> None:
        """Push the exportable table names to the view.

        Args:
            names: The table names available for export.

        Returns:
            ``None``.

        Side effects:
            Records the names and updates the view's checklist.
        """
        self._available = list(names)
        self._view.set_table_list(list(names))

    def on_select_all(self) -> None:
        """Trigger the view to check every table (export-all).

        Returns:
            ``None``.

        Side effects:
            Calls ``view.select_all_tables``.
        """
        self._view.select_all_tables()

    def on_export(
        self,
        tables: dict[str, pd.DataFrame],
        format_name: str,
        destination_path: str,
    ) -> None:
        """Export the user's selected tables in the chosen format.

        Resolves the exporter from the registry, reads the current selection from
        the view, rejects an empty selection before any exporter call, then
        delegates to the exporter.

        Args:
            tables: All available tables keyed by name.
            format_name: The chosen export format (a registry key).
            destination_path: The export destination path.

        Returns:
            ``None``.

        Side effects:
            Calls ``exporter.export`` on a non-empty selection. The export view
            has no error surface, so the guards fail fast instead: a
            ``ValueError`` is raised for an empty selection and a registry
            ``KeyError`` propagates for an unknown format.

        Raises:
            ValueError: When no tables are selected (rejected before exporting).
            KeyError: When ``format_name`` is not registered (from the registry).
        """
        logger.info(
            "Export requested: format=%r dest=%r.", format_name, destination_path
        )
        # Resolve the exporter first so an unknown format fails before reading
        # the selection (a registry KeyError propagates to the caller).
        exporter = self._registry.get(format_name)

        selected = self._view.get_selected_names()
        # Reject an empty selection before any exporter call so no empty export
        # is ever attempted.
        if not selected:
            logger.error("Export rejected: no tables selected.")
            raise ValueError("No tables selected for export.")

        exporter.export(tables, selected, destination_path)
        logger.info("Export complete: %d tables.", len(selected))
