"""Composition-root wiring for schema discovery and import gating (Decision 8/9).

This helper connects the per-tab schema-discovery and import-gating signals at the
composition root, extracted from ``app.py`` so that file stays under the
repository's 500-line cap before this wiring is added. It connects, per source
tab:

    - the worksheet-tab combo's ``currentTextChanged`` to the source presenter's
      ``on_schema_discovery`` so activating a tab (with a file already selected)
      runs alias-aware schema matching (Decision 9, completing #48 follow-up F2);
    - the widget's ``schema_selected`` to enabling the tab's Import button, and a
      return to the placeholder to disabling it (Decision 8).

Responsibilities:
    - ``wire_schema_discovery_and_gating``: connect the discovery and import-gate
      signals for the three source tabs.
    - ``wire_edit_schema_buttons``: connect each tab's "Edit Schema" button to
      open the builder seeded from the tab's currently-selected schema (issue #60
      Defect 1). It lives here (rather than in ``_schema_wiring``) so that module
      stays under the 500-line cap and so the edit wiring sits beside its caller.

Scope boundaries:
    - Qt signal wiring only; no transform logic. Matching flows through the
      injected source presenters and schema service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_wiring import (
    open_schema_builder,
    wire_build_schema_buttons,
    wire_schema_builder,
)
from src.gui.presenters._schema_builder_state import PreviewSlice
from src.gui.presenters.source_selection_presenter import (
    read_worksheet_header_columns,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui._schema_build_specs import BuildSpecProvider
    from src.gui.main_window import MainWindow
    from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
    from src.gui.widgets.source_input_widget import SourceInputWidget

__all__ = ["wire_edit_schema_buttons", "wire_schema_discovery_and_gating"]

# The schema dropdown's "no schema selected" placeholder (issue #60 Defect 1).
# The Edit-Schema wiring short-circuits on this value (or an empty selection) so
# it never opens the builder for a non-schema, mirroring the widget-level gating.
_SCHEMA_PLACEHOLDER = "<Choose Schema>"


def wire_schema_discovery_and_gating(
    window: MainWindow,
    service: SchemaServiceProtocol,
    le_presenter: SourceSelectionPresenter,
    aop_presenter: SourceSelectionPresenter,
    skulu_presenter: SourceSelectionPresenter,
    *,
    spec_provider: BuildSpecProvider | None = None,
) -> None:
    """Wire the schema-builder, per-tab discovery, and Import-gating (Decision 8/9).

    Connects, at the composition root:

    - the ``Tools > Schema Builder...`` action and each per-tab "Build/Edit
      schema" button to open the builder (delegating to the schema-builder
      wiring);
    - for each source tab, the tab-combo activation to the presenter's
      ``on_schema_discovery`` (Decision 9) and the widget's ``schema_selected`` to
      enabling the tab's Import button (Decision 8). A return to the placeholder
      is self-gated by the widget.

    Args:
        window: The shell carrying the three source input widgets.
        service: The schema service the builder presenter drives.
        le_presenter: The LE source-selection presenter.
        aop_presenter: The AOP source-selection presenter.
        skulu_presenter: The SKU_LU source-selection presenter.
        spec_provider: Optional per-source build-spec provider. When supplied, each
            per-tab "Build/Edit schema" button seeds the builder from its source's
            required/optional specs, default key pattern, and masked preview slice
            (Decision 7); the menu-action path stays blank (Decision 7).

    Returns:
        ``None``.

    Side effects:
        Connects the schema-builder action/buttons and each source widget's
        ``currentTextChanged`` and ``schema_selected`` signals to their handlers.
    """
    # Reuse the existing builder-open wiring so the menu action and per-tab
    # buttons open the builder (Feature D AC6 / AC-13). The menu-action path stays
    # blank by design; only the per-tab buttons seed from the spec provider.
    wire_schema_builder(window, service)
    wire_build_schema_buttons(window, service, spec_provider=spec_provider)
    # Issue #60 Defect 1 / #62: wire each tab's "Edit Schema" button so it opens
    # the builder seeded from the tab's currently-selected schema via load_existing
    # and from the selected worksheet's real header columns (a live preview slice).
    # The per-tab presenters carry the workbook reader used to read those headers.
    wire_edit_schema_buttons(
        window,
        service,
        le_presenter=le_presenter,
        aop_presenter=aop_presenter,
        skulu_presenter=skulu_presenter,
    )
    # Pair each widget with its presenter so the same discovery/gating wiring
    # applies uniformly to all three source tabs.
    for widget, presenter in (
        (window.le_widget, le_presenter),
        (window.aop_widget, aop_presenter),
        (window.skulu_widget, skulu_presenter),
    ):
        _wire_one_tab(widget, presenter)


def _wire_one_tab(
    widget: SourceInputWidget, presenter: SourceSelectionPresenter
) -> None:
    """Wire one source tab's discovery and import-gate signals.

    Args:
        widget: The source input widget whose signals are connected.
        presenter: The source-selection presenter that runs discovery for this
            tab.

    Returns:
        ``None``.

    Side effects:
        Connects ``widget``'s tab-combo activation to discovery and its
        ``schema_selected`` to enabling the Import button.
    """

    def _on_tab_activated(_sheet: str) -> None:
        """Run schema discovery for the active sheet (Decision 9).

        The tab combo fires ``currentTextChanged`` on activation with a file
        already selected; discovery reads the header and auto-selects a matching
        schema. The presenter retains the existing empty-header and reader-error
        guards.

        This handler short-circuits when the widget has no file selected or no
        worksheet selected (blank/whitespace-only path or sheet). The tab combo
        emits ``currentTextChanged`` during combo population and on placeholder
        selection, before a worksheet is chosen; discovery must not run with a
        blank sheet in that window (issue #50 cycle 3, B1). The presenter applies
        the same guard, so this short-circuit is defense in depth that also avoids
        an unnecessary call.
        """
        # Read the current path/sheet from the widget so discovery always reflects
        # the live selection at activation time.
        path = widget.current_path()
        sheet = widget.current_sheet()
        # No file or no worksheet selected yet: skip discovery so the reader is
        # never invoked with a blank sheet.
        if not path.strip() or not sheet.strip():
            return
        presenter.on_schema_discovery(path, sheet)

    def _on_schema_selected(_name: str) -> None:
        """Enable this tab's Import button when a real schema is selected.

        The widget self-disables on a return to the placeholder, so this handler
        only needs to enable on a genuine selection.
        """
        widget.set_import_button_enabled(True)

    widget.tab_combo.currentTextChanged.connect(_on_tab_activated)
    widget.schema_selected.connect(_on_schema_selected)


def wire_edit_schema_buttons(
    window: MainWindow,
    service: SchemaServiceProtocol,
    *,
    le_presenter: SourceSelectionPresenter | None = None,
    aop_presenter: SourceSelectionPresenter | None = None,
    skulu_presenter: SourceSelectionPresenter | None = None,
    dialog_factory: Callable[[], SchemaBuilderDialog] | None = None,
    presenter_factory: (
        Callable[[SchemaBuilderDialog, SchemaServiceProtocol], object] | None
    ) = None,
) -> None:
    """Wire each source tab's "Edit Schema" button to open a seeded builder (#60/#62).

    For each of the three source widgets, connects ``edit_schema_requested`` to a
    closure that reads the tab's currently-selected schema name, guards against
    the placeholder/empty selection (defense in depth alongside the widget-level
    disabled state, the #50 no-schema-seam lesson), builds a live ``preview_slice``
    from the selected worksheet's real header columns (issue #62; read via the
    tab's presenter ``reader`` and the same best-header-row path discovery uses),
    opens the builder via the shared :func:`open_schema_builder` path (passing the
    ``preview_slice`` so the Columns-tab source pool is populated, retaining the
    presenter on ``window.schema_builder_presenter``), and then seeds it from the
    selected schema via ``schema_builder_presenter.load_existing(name)`` (the
    established ``_seed_presenter`` getattr pattern, so recording test factories
    that return a minimal stub remain compatible).

    When no per-tab presenter is supplied for a widget, or when no file/worksheet
    is selected, the ``preview_slice`` is ``None`` and the builder opens with an
    empty source pool — the issue #50 / AC-9 no-file/no-sheet seam, with no reader
    call and no crash.

    Args:
        window: The shell whose three source widgets carry the Edit buttons.
        service: The schema service the builder presenter drives.
        le_presenter: The LE source-selection presenter carrying the workbook
            reader used to read the LE worksheet's header columns. ``None`` opens
            the LE edit path with an empty pool.
        aop_presenter: The AOP source-selection presenter. ``None`` opens the AOP
            edit path with an empty pool.
        skulu_presenter: The SKU_LU source-selection presenter. ``None`` opens the
            SKU_LU edit path with an empty pool.
        dialog_factory: Optional dialog factory; defaults to the production
            factory. Tests inject a recording factory.
        presenter_factory: Optional presenter factory; defaults to the production
            factory. Tests inject a recording factory.

    Returns:
        ``None``.

    Side effects:
        Connects each source widget's ``edit_schema_requested`` signal to a
        handler that opens the schema builder and seeds it from the selection and
        the worksheet's real header columns.
    """

    def _make_edit(
        widget: SourceInputWidget,
        presenter: SourceSelectionPresenter | None,
    ) -> Callable[[], None]:
        """Build the per-widget Edit handler that seeds from the selection.

        Args:
            widget: The source widget whose Edit button triggers this handler.
            presenter: The source-selection presenter carrying the workbook reader
                for this tab, or ``None`` to open with an empty source pool.

        Returns:
            A zero-argument handler opening the builder seeded from ``widget``'s
            currently-selected schema and worksheet headers.
        """

        def _open_edit() -> None:
            """Open the builder seeded from the widget's selected schema."""
            name = widget.current_schema()
            # Guard the placeholder/empty selection: the Edit button is disabled in
            # that state, but the wiring short-circuits too so an unexpected emit
            # never opens the builder for a non-schema or crashes (issue #50 seam).
            if not name or name == _SCHEMA_PLACEHOLDER:
                return
            # Build a live preview slice from the selected worksheet's real header
            # columns so the Columns-tab source pool is populated (issue #62). When
            # no presenter is wired or no file/sheet is selected, the helper returns
            # an empty header and the slice stays None (empty pool, no crash — AC-9).
            preview_slice = _build_edit_preview_slice(widget, presenter, service)
            # Open the builder through the shared path; it retains the presenter on
            # the window so the subsequent load_existing seeds that presenter, and
            # the preview slice seeds the source-token pool before that render runs.
            open_schema_builder(
                window,
                service,
                dialog_factory=dialog_factory,
                presenter_factory=presenter_factory,
                preview_slice=preview_slice,
            )
            # Seed the retained presenter from the selected schema via getattr so a
            # recording test stub without load_existing is tolerated.
            retained = getattr(window, "schema_builder_presenter", None)
            load_existing = getattr(retained, "load_existing", None)
            if callable(load_existing):
                load_existing(name)

        return _open_edit

    # Wire all three per-tab Edit buttons, pairing each widget with its presenter
    # so each tab's "Edit Schema" button opens the builder seeded from that tab's
    # currently-selected schema and the selected worksheet's real header columns.
    for widget, presenter in (
        (window.le_widget, le_presenter),
        (window.aop_widget, aop_presenter),
        (window.skulu_widget, skulu_presenter),
    ):
        widget.edit_schema_requested.connect(_make_edit(widget, presenter))


def _build_edit_preview_slice(
    widget: SourceInputWidget,
    presenter: SourceSelectionPresenter | None,
    service: SchemaServiceProtocol,
) -> PreviewSlice | None:
    """Build a live preview slice from the widget's selected worksheet headers.

    Reads the selected worksheet's real header columns via the tab presenter's
    workbook reader and the shared best-header-row path, so the Edit Schema open
    path seeds the Columns-tab source pool with the worksheet's actual columns
    (issue #62, AC-5/AC-6).

    Args:
        widget: The source widget whose current file/sheet selection is read.
        presenter: The source-selection presenter carrying the workbook reader, or
            ``None`` when no reader is wired for this tab.
        service: The schema service used by the best-header-row scorer.

    Returns:
        A :class:`PreviewSlice` carrying the worksheet's real header columns, or
        ``None`` when no presenter is wired, no file/sheet is selected, or the
        worksheet has no header row (the empty-pool / AC-9 seam).

    Side effects:
        Calls the presenter's reader once when a presenter is wired and a
        file/sheet is selected.
    """
    # No presenter means no reader is available for this tab, so open with an empty
    # source pool rather than guessing a header (AC-9 graceful degradation).
    if presenter is None:
        return None
    header = read_worksheet_header_columns(
        presenter.reader,
        service,
        widget.current_path(),
        widget.current_sheet(),
    )
    # An empty header (blank path/sheet or empty preview) yields no slice so the
    # builder opens with an empty pool instead of an empty-header slice.
    if not header:
        return None
    return PreviewSlice(header=header)
