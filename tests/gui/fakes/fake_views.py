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


class FakeColumnMatchingView:
    """Records calls made to a :class:`ColumnMatchingViewProtocol`.

    Purpose:
        Let column-matching presenter tests assert on what the presenter pushed
        and return a controlled assignment map, with no Qt and no logic.

    Attributes:
        unmatched_required: Each ``set_unmatched_required`` argument, in order.
        source_columns: Each ``set_source_columns`` argument, in order.
        fuzzy_suggestions: Each ``set_fuzzy_suggestions`` argument, in order.
        assignments_set: Each ``set_assignment`` call as ``(required, source)``.
        ignored: Each ``mark_ignored`` argument, in order.
        errors: Each ``show_error`` message, in order.
        assignments: The controlled map ``get_assignments`` returns.
    """

    def __init__(self, assignments: dict[str, str] | None = None) -> None:
        """Initialize records and the controlled assignment map.

        Args:
            assignments: The map ``get_assignments`` returns (default empty).
        """
        self.unmatched_required: list[list[tuple[str, tuple[str, ...]]]] = []
        self.source_columns: list[list[str]] = []
        self.fuzzy_suggestions: list[dict[str, list[tuple[str, float]]]] = []
        self.assignments_set: list[tuple[str, str]] = []
        self.ignored: list[str] = []
        self.errors: list[str] = []
        self.assignments: dict[str, str] = dict(assignments) if assignments else {}

    def set_unmatched_required(self, items: list[tuple[str, tuple[str, ...]]]) -> None:
        """Record the unmatched-required items pushed by the presenter.

        Args:
            items: The ``(canonical_name, aliases)`` pairs.

        Returns:
            ``None``.
        """
        self.unmatched_required.append(list(items))

    def set_source_columns(self, names: list[str]) -> None:
        """Record the source columns pushed by the presenter.

        Args:
            names: The source column names.

        Returns:
            ``None``.
        """
        self.source_columns.append(list(names))

    def set_fuzzy_suggestions(self, items: dict[str, list[tuple[str, float]]]) -> None:
        """Record the fuzzy suggestions pushed by the presenter.

        Args:
            items: The per-column candidate suggestions.

        Returns:
            ``None``.
        """
        self.fuzzy_suggestions.append(dict(items))

    def set_assignment(self, required: str, source: str) -> None:
        """Record an assignment pushed by the presenter.

        Args:
            required: The required canonical name.
            source: The assigned source column.

        Returns:
            ``None``.
        """
        self.assignments_set.append((required, source))

    def mark_ignored(self, required: str) -> None:
        """Record an ignore mark pushed by the presenter.

        Args:
            required: The ignored canonical name.

        Returns:
            ``None``.
        """
        self.ignored.append(required)

    def show_error(self, message: str) -> None:
        """Record an error message pushed by the presenter.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)

    def get_assignments(self) -> dict[str, str]:
        """Return the controlled assignment map.

        Returns:
            The configured required-to-source assignment map.
        """
        return dict(self.assignments)


class FakeSchemaBuilderView:
    """Records calls and returns controlled edits for a schema-builder view.

    Purpose:
        Let schema-builder presenter tests assert on rendered state and supply
        controlled identity/column/key/dedup/derived edits, with no Qt.

    Attributes:
        identity_set: Each ``set_identity`` call as ``(name, version, desc)``.
        columns_set: Each ``set_columns`` argument, in order.
        keys_set: Each ``set_key`` call as ``(columns, sku_coercion)``.
        dedups_set: Each ``set_dedup`` call as ``(mode, discriminator)``.
        deriveds_set: Each ``set_derived`` argument, in order.
        previews: Each ``show_preview`` argument, in order.
        formula_errors: Each ``show_formula_error`` message, in order.
        clear_formula_calls: The number of ``clear_formula_error`` calls.
        errors: Each ``show_error`` message, in order.
        identity: The controlled ``get_identity`` tuple.
        columns: The controlled ``get_columns`` rows.
        key: The controlled ``get_key`` tuple.
        dedup: The controlled ``get_dedup`` tuple.
        derived: The controlled ``get_derived`` rows.
    """

    def __init__(self) -> None:
        """Initialize empty records and default controlled edit values."""
        self.identity_set: list[tuple[str, str, str]] = []
        self.columns_set: list[list[tuple[str, str, bool, tuple[str, ...]]]] = []
        self.keys_set: list[tuple[tuple[str, ...], bool]] = []
        self.dedups_set: list[tuple[str, str | None]] = []
        self.deriveds_set: list[list[tuple[str, str]]] = []
        self.previews: list[list[list[str]]] = []
        self.formula_errors: list[str] = []
        self.clear_formula_calls = 0
        self.errors: list[str] = []
        # Controlled getter values the presenter reads on sync_from_view.
        self.identity: tuple[str, str, str] = ("", "1.0", "")
        self.columns: list[tuple[str, str, bool, tuple[str, ...]]] = []
        self.key: tuple[tuple[str, ...], bool] = ((), False)
        self.dedup: tuple[str, str | None] = ("none", None)
        self.derived: list[tuple[str, str]] = []

    def set_identity(self, name: str, version: str, description: str) -> None:
        """Record an identity render call.

        Args:
            name: The schema name.
            version: The schema version.
            description: The schema description.

        Returns:
            ``None``.
        """
        self.identity_set.append((name, version, description))

    def get_identity(self) -> tuple[str, str, str]:
        """Return the controlled identity tuple.

        Returns:
            The configured ``(name, version, description)``.
        """
        return self.identity

    def set_columns(self, rows: list[tuple[str, str, bool, tuple[str, ...]]]) -> None:
        """Record a columns render call.

        Args:
            rows: The column rows.

        Returns:
            ``None``.
        """
        self.columns_set.append(list(rows))

    def get_columns(self) -> list[tuple[str, str, bool, tuple[str, ...]]]:
        """Return the controlled column rows.

        Returns:
            The configured column rows.
        """
        return list(self.columns)

    def set_key(self, columns: tuple[str, ...], sku_coercion: bool) -> None:
        """Record a key render call.

        Args:
            columns: The key column names.
            sku_coercion: The SKU coercion flag.

        Returns:
            ``None``.
        """
        self.keys_set.append((columns, sku_coercion))

    def get_key(self) -> tuple[tuple[str, ...], bool]:
        """Return the controlled key tuple.

        Returns:
            The configured ``(columns, sku_coercion)``.
        """
        return self.key

    def set_dedup(self, mode: str, discriminator: str | None) -> None:
        """Record a dedup render call.

        Args:
            mode: The dedup mode.
            discriminator: The discriminator column, or ``None``.

        Returns:
            ``None``.
        """
        self.dedups_set.append((mode, discriminator))

    def get_dedup(self) -> tuple[str, str | None]:
        """Return the controlled dedup tuple.

        Returns:
            The configured ``(mode, discriminator)``.
        """
        return self.dedup

    def set_derived(self, rows: list[tuple[str, str]]) -> None:
        """Record a derived render call.

        Args:
            rows: The derived ``(name, expression)`` rows.

        Returns:
            ``None``.
        """
        self.deriveds_set.append(list(rows))

    def get_derived(self) -> list[tuple[str, str]]:
        """Return the controlled derived rows.

        Returns:
            The configured derived rows.
        """
        return list(self.derived)

    def show_preview(self, rows: list[list[str]]) -> None:
        """Record a preview render call.

        Args:
            rows: The preview rows.

        Returns:
            ``None``.
        """
        self.previews.append([list(row) for row in rows])

    def show_formula_error(self, message: str) -> None:
        """Record an inline formula error.

        Args:
            message: The formula error text.

        Returns:
            ``None``.
        """
        self.formula_errors.append(message)

    def clear_formula_error(self) -> None:
        """Record a formula-error clear call.

        Returns:
            ``None``.
        """
        self.clear_formula_calls += 1

    def show_error(self, message: str) -> None:
        """Record a general error message.

        Args:
            message: The error text.

        Returns:
            ``None``.
        """
        self.errors.append(message)
