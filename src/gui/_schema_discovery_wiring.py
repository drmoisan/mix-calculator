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

Scope boundaries:
    - Qt signal wiring only; no transform logic. Matching flows through the
      injected source presenters and schema service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_wiring import wire_build_schema_buttons, wire_schema_builder

if TYPE_CHECKING:
    from src.gui._schema_build_specs import BuildSpecProvider
    from src.gui.main_window import MainWindow
    from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.gui.widgets.source_input_widget import SourceInputWidget

__all__ = ["wire_schema_discovery_and_gating"]


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
        """
        # Read the current path/sheet from the widget so discovery always reflects
        # the live selection at activation time.
        presenter.on_schema_discovery(widget.current_path(), widget.current_sheet())

    def _on_schema_selected(_name: str) -> None:
        """Enable this tab's Import button when a real schema is selected.

        The widget self-disables on a return to the placeholder, so this handler
        only needs to enable on a genuine selection.
        """
        widget.set_import_button_enabled(True)

    widget.tab_combo.currentTextChanged.connect(_on_tab_activated)
    widget.schema_selected.connect(_on_schema_selected)
