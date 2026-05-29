"""Registry of table exporters keyed by format name.

This module provides :class:`ExporterRegistry`, the lookup the export presenter
uses to resolve a concrete exporter from a chosen format name. Registering a new
exporter is the only step needed to add a format; the presenter is unchanged.

Responsibilities:
    - Register exporters keyed by their ``format_name``.
    - Resolve an exporter by format name, raising a specific error when unknown.
    - List the available format names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.gui.exporters.base import ExporterProtocol

__all__ = ["ExporterRegistry"]


class ExporterRegistry:
    """In-memory registry mapping a format name to its exporter.

    Purpose:
        Decouple the export presenter from concrete exporter classes so adding a
        format requires only a registration call.

    Responsibilities:
        Store exporters keyed by ``format_name``, resolve by name, and list the
        registered names. It holds no export logic of its own.

    Usage:
        Constructed at the composition root; ``ExcelExporter`` and
        ``CsvExporter`` are registered there. The presenter calls ``get`` and
        ``available_formats``.

    Key invariants:
        Registering a format name that already exists overwrites the prior
        exporter for that name (last registration wins).
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._exporters: dict[str, ExporterProtocol] = {}

    def register(self, exporter: ExporterProtocol) -> None:
        """Register an exporter under its ``format_name``.

        Args:
            exporter: The exporter to register; its ``format_name`` is the key.

        Returns:
            ``None``.

        Side effects:
            Adds or overwrites the entry for ``exporter.format_name``.
        """
        self._exporters[exporter.format_name] = exporter

    def get(self, format_name: str) -> ExporterProtocol:
        """Resolve the exporter registered under ``format_name``.

        Args:
            format_name: The format name to resolve.

        Returns:
            The registered exporter for ``format_name``.

        Raises:
            KeyError: When no exporter is registered under ``format_name``.
        """
        # Fail fast with a specific error so an unknown format is unambiguous to
        # the caller (and to the presenter's error handling).
        if format_name not in self._exporters:
            raise KeyError(f"No exporter registered for format {format_name!r}.")
        return self._exporters[format_name]

    def available_formats(self) -> list[str]:
        """Return the registered format names.

        Returns:
            The format names currently registered, in insertion order.
        """
        return list(self._exporters)
