"""Fake view implementations for the GUI presenter test suite.

Each fake implements one of the Phase 1 view Protocols, records the calls the
presenter makes, and returns controlled data. The fakes hold no logic; they let
presenter tests run with no ``QApplication`` and assert on what the presenter
pushed to the view.
"""

from __future__ import annotations


class FakeSourceSelectionView:
    """Records calls made to a :class:`SourceSelectionViewProtocol`.

    Attributes:
        tab_lists: Each ``set_tab_list`` argument, in call order.
        previews: Each ``show_preview`` argument, in call order.
        errors: Each ``show_error`` message, in call order.
    """

    def __init__(self) -> None:
        """Initialize empty call records."""
        self.tab_lists: list[list[str]] = []
        self.previews: list[list[list[str]]] = []
        self.errors: list[str] = []

    def set_tab_list(self, tabs: list[str]) -> None:
        """Record the tab list pushed by the presenter.

        Args:
            tabs: The worksheet-tab names.

        Returns:
            ``None``.
        """
        self.tab_lists.append(list(tabs))

    def show_preview(self, rows: list[list[str]]) -> None:
        """Record the preview rows pushed by the presenter.

        Args:
            rows: The preview rows.

        Returns:
            ``None``.
        """
        self.previews.append([list(row) for row in rows])

    def show_error(self, message: str) -> None:
        """Record an error message pushed by the presenter.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)


class FakePipelineView:
    """Records calls made to a :class:`PipelineViewProtocol`.

    Attributes:
        running_states: Each ``set_running`` flag, in call order.
        results: Each ``show_result`` summary, in call order.
        errors: Each ``show_error`` message, in call order.
        import_button_states: Each ``set_import_button_enabled`` call recorded
            as ``(key, enabled)`` in call order.
        run_button_states: Each ``set_run_button_enabled`` flag, in call order.
        save_button_states: Each ``set_save_button_enabled`` flag, in call
            order.
        export_button_states: Each ``set_export_button_enabled`` flag, in call
            order.
    """

    def __init__(self) -> None:
        """Initialize empty call records."""
        self.running_states: list[bool] = []
        self.results: list[str] = []
        self.errors: list[str] = []
        self.import_button_states: list[tuple[str, bool]] = []
        self.run_button_states: list[bool] = []
        self.save_button_states: list[bool] = []
        self.export_button_states: list[bool] = []

    def set_running(self, is_running: bool) -> None:
        """Record a running-state transition.

        Args:
            is_running: The new running flag.

        Returns:
            ``None``.
        """
        self.running_states.append(is_running)

    def show_result(self, summary: str) -> None:
        """Record a success summary.

        Args:
            summary: The run summary.

        Returns:
            ``None``.
        """
        self.results.append(summary)

    def show_error(self, message: str) -> None:
        """Record an error message.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)

    def set_import_button_enabled(self, key: str, enabled: bool) -> None:
        """Record a per-input import-button enable transition.

        Args:
            key: The import key being toggled.
            enabled: The new enabled state.

        Returns:
            ``None``.
        """
        self.import_button_states.append((key, enabled))

    def set_run_button_enabled(self, enabled: bool) -> None:
        """Record a Run-button enable transition.

        Args:
            enabled: The new enabled state.

        Returns:
            ``None``.
        """
        self.run_button_states.append(enabled)

    def set_save_button_enabled(self, enabled: bool) -> None:
        """Record a Save-button enable transition.

        Args:
            enabled: The new enabled state.

        Returns:
            ``None``.
        """
        self.save_button_states.append(enabled)

    def set_export_button_enabled(self, enabled: bool) -> None:
        """Record an Export-button enable transition.

        Args:
            enabled: The new enabled state.

        Returns:
            ``None``.
        """
        self.export_button_states.append(enabled)


class FakeExportView:
    """Records calls made to an :class:`ExportViewProtocol` and returns selection.

    Attributes:
        table_lists: Each ``set_table_list`` argument, in call order.
        select_all_calls: The number of ``select_all_tables`` calls.
        selected: The controlled selection ``get_selected_names`` returns.
    """

    def __init__(self, selected: list[str] | None = None) -> None:
        """Initialize records and the controlled selection.

        Args:
            selected: The selection ``get_selected_names`` returns; defaults to
                an empty list.
        """
        self.table_lists: list[list[str]] = []
        self.select_all_calls = 0
        self.selected: list[str] = list(selected) if selected is not None else []

    def set_table_list(self, names: list[str]) -> None:
        """Record the table list pushed by the presenter.

        Args:
            names: The exportable table names.

        Returns:
            ``None``.
        """
        self.table_lists.append(list(names))

    def get_selected_names(self) -> list[str]:
        """Return the controlled selection.

        Returns:
            The configured selected table names.
        """
        return list(self.selected)

    def select_all_tables(self) -> None:
        """Record a select-all call and set the selection to the last list.

        Returns:
            ``None``.

        Side effects:
            Sets ``selected`` to the most recent ``set_table_list`` argument so
            a subsequent ``get_selected_names`` reflects the select-all.
        """
        self.select_all_calls += 1
        # Mirror a real view: selecting all checks every name last set.
        if self.table_lists:
            self.selected = list(self.table_lists[-1])
