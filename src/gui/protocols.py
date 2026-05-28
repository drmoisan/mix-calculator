"""View Protocol interfaces for the mix-pipeline GUI (MVP passive views).

This module declares the ``typing.Protocol`` interfaces that the Qt widgets
implement and the presenters depend on. Keeping the view contracts here (with no
Qt import) lets presenters be written and tested as plain Python against fakes,
and lets the concrete Qt widgets satisfy the same contract without the presenter
knowing about Qt.

Responsibilities:
    - Define the per-area view contracts (source selection, pipeline, export).
    - Carry only the methods the presenters call; nothing Qt-specific leaks in.

The three Protocols mirror the spec API surface exactly. They are structural,
so any object implementing the listed methods satisfies the contract; the Qt
widgets and the test fakes both implement them.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = [
    "ExportViewProtocol",
    "PipelineViewProtocol",
    "SourceSelectionViewProtocol",
]


@runtime_checkable
class SourceSelectionViewProtocol(Protocol):
    """Contract for a per-input source-selection view.

    Purpose:
        The view that lets the user pick an Excel file and worksheet tab for one
        pipeline input (LE, AOP, or SKU_LU) and shows an optional tab preview.

    Responsibilities:
        Render the worksheet-tab list, render a preview grid, and surface error
        messages. It holds no logic; the ``SourceSelectionPresenter`` drives it.

    Usage:
        The presenter calls these methods in response to user actions; a Qt
        ``SourceInputWidget`` (or a test fake) implements them.
    """

    def set_tab_list(self, tabs: list[str]) -> None:
        """Render the available worksheet-tab names in the tab dropdown.

        Args:
            tabs: The worksheet-tab names to display, in source order.

        Returns:
            ``None``.

        Side effects:
            Updates the view's tab control.
        """
        ...

    def show_preview(self, rows: list[list[str]]) -> None:
        """Render a tabular preview of the selected worksheet tab.

        Args:
            rows: The preview rows, each a list of string cell values.

        Returns:
            ``None``.

        Side effects:
            Updates the view's preview surface.
        """
        ...

    def show_error(self, message: str) -> None:
        """Display an error message to the user.

        Args:
            message: The human-readable error text to display.

        Returns:
            ``None``.

        Side effects:
            Updates the view's error surface.
        """
        ...


@runtime_checkable
class PipelineViewProtocol(Protocol):
    """Contract for the pipeline (import/run/save/open) view.

    Purpose:
        The view that reflects pipeline run state and reports run outcomes.

    Responsibilities:
        Reflect the running/idle state, show a success summary, and surface
        errors. It holds no logic; the ``PipelinePresenter`` drives it.

    Usage:
        The presenter calls these methods as the pipeline transitions between
        idle and running; a Qt main window (or a test fake) implements them.
    """

    def set_running(self, is_running: bool) -> None:
        """Reflect whether a pipeline or import job is in flight.

        Args:
            is_running: ``True`` while a job runs (controls disable busy UI),
                ``False`` when idle.

        Returns:
            ``None``.

        Side effects:
            Updates the view's busy/idle state.
        """
        ...

    def show_result(self, summary: str) -> None:
        """Display a success summary for a completed run.

        Args:
            summary: The human-readable run summary to display.

        Returns:
            ``None``.

        Side effects:
            Updates the view's result surface.
        """
        ...

    def show_error(self, message: str) -> None:
        """Display an error message for a failed run or operation.

        Args:
            message: The human-readable error text to display.

        Returns:
            ``None``.

        Side effects:
            Updates the view's error surface.
        """
        ...


@runtime_checkable
class ExportViewProtocol(Protocol):
    """Contract for the export-dialog view.

    Purpose:
        The view that lets the user pick which tables to export and trigger an
        export-all.

    Responsibilities:
        Render the table checklist, report the user's current selection, and
        check every item on export-all. It holds no logic; the
        ``ExportPresenter`` drives it.

    Usage:
        The presenter calls these methods in response to user actions; a Qt
        ``ExportDialog`` (or a test fake) implements them.
    """

    def set_table_list(self, names: list[str]) -> None:
        """Render the exportable table names as a checklist.

        Args:
            names: The table names available for export, in stable order.

        Returns:
            ``None``.

        Side effects:
            Updates the view's checklist control.
        """
        ...

    def get_selected_names(self) -> list[str]:
        """Return the table names the user has currently checked.

        Returns:
            The checked table names, in the order the view presents them.
        """
        ...

    def select_all_tables(self) -> None:
        """Check every table in the checklist (export-all).

        Returns:
            ``None``.

        Side effects:
            Marks all checklist items as selected.
        """
        ...
