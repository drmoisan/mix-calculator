"""Composition-root wiring for the schema builder and import-flow discovery.

This helper connects the main window's ``schema_builder_requested`` signal to a
handler that opens the ``SchemaBuilderDialog`` driven by a
``SchemaBuilderPresenter`` over the injected ``SchemaServiceProtocol`` (Feature D,
AC6), and provides the import-flow schema-discovery decision used when a sheet
preview yields a header row (AC2). It lives in its own module so ``app.py`` stays
under the repository's 500-line file cap.

Responsibilities:
    - ``wire_schema_builder``: connect the menu action to open the builder.
    - ``discover_schema``: classify a header row against the registry into a
      proceed / manual-match / build decision the import flow acts on.

The module performs Qt signal wiring and a pure discovery decision only; it holds
no transform logic (matching/loading flow through the injected service).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.etl_columns import DEFAULT_THRESHOLD

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from src.gui.main_window import MainWindow
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
    from src.schema_matching import MatchResult

__all__ = [
    "SchemaDiscoveryDecision",
    "default_schema_builder_factories",
    "discover_schema",
    "open_schema_builder",
    "wire_build_schema_buttons",
    "wire_schema_builder",
]


def default_schema_builder_factories() -> tuple[
    Callable[[], SchemaBuilderDialog],
    Callable[[SchemaBuilderDialog, SchemaServiceProtocol], object],
]:
    """Return the production dialog/presenter factories for the schema builder.

    The concrete :class:`SchemaBuilderDialog` and :class:`SchemaBuilderPresenter`
    are imported lazily here so the composition root does not need to import them
    directly, keeping ``app.py`` smaller. Tests inject their own recording
    factories instead of using these defaults.

    Returns:
        A ``(dialog_factory, presenter_factory)`` pair. ``dialog_factory`` builds
        a fresh :class:`SchemaBuilderDialog`; ``presenter_factory`` builds a
        :class:`SchemaBuilderPresenter` over a given dialog and service.
    """
    # Import the concrete UI classes lazily so importing this wiring module does
    # not pull in the dialog/presenter at module load (and so app.py need not).
    from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter
    from src.gui.widgets.schema_builder_dialog import (
        SchemaBuilderDialog as _SchemaBuilderDialog,
    )

    def _dialog_factory() -> SchemaBuilderDialog:
        """Build a fresh schema-builder dialog per open."""
        return _SchemaBuilderDialog()

    def _presenter_factory(
        dialog: SchemaBuilderDialog, service: SchemaServiceProtocol
    ) -> object:
        """Build a schema-builder presenter over the given dialog and service."""
        return SchemaBuilderPresenter(dialog, service)

    return _dialog_factory, _presenter_factory


def open_schema_builder(
    window: MainWindow,
    service: SchemaServiceProtocol,
    *,
    dialog_factory: Callable[[], SchemaBuilderDialog] | None = None,
    presenter_factory: (
        Callable[[SchemaBuilderDialog, SchemaServiceProtocol], object] | None
    ) = None,
) -> None:
    """Open the schema-builder dialog driven by a fresh presenter.

    This is the imperative open path shared by the ``schema_builder_requested``
    menu action and the per-tab "Build new schema" button (WS2). A new dialog and
    presenter are built per open so the builder is repeatable; the presenter is
    retained on the window to keep it alive for the lifetime of the (modeless)
    dialog.

    Args:
        window: The shell the presenter is retained on.
        service: The schema service the builder presenter drives.
        dialog_factory: Optional dialog factory; defaults to the production
            :class:`SchemaBuilderDialog` factory.
        presenter_factory: Optional presenter factory; defaults to the production
            :class:`SchemaBuilderPresenter` factory.

    Returns:
        ``None``.

    Side effects:
        Builds and shows a dialog, retaining the presenter on ``window``.
    """
    # Resolve the factories: callers (tests) may inject recording factories;
    # otherwise use the lazy production defaults so app.py stays thin.
    if dialog_factory is None or presenter_factory is None:
        default_dialog, default_presenter = default_schema_builder_factories()
        dialog_factory = dialog_factory or default_dialog
        presenter_factory = presenter_factory or default_presenter
    dialog = dialog_factory()
    # Retain the presenter on the window so it outlives this call while the dialog
    # is open; without a reference it would be collected immediately.
    window.schema_builder_presenter = presenter_factory(dialog, service)
    dialog.show()


@dataclass(frozen=True)
class SchemaDiscoveryDecision:
    """The import-flow outcome of classifying a header row against the registry.

    Purpose:
        Carry the discovery decision so the import-flow wiring can either proceed
        with a matched schema or surface the mismatch and offer the manual-match
        and build actions.

    Attributes:
        action: One of ``"proceed"`` (a suitable match was found) or ``"resolve"``
            (no suitable match; the user must manually match or build a schema).
        result: The underlying :class:`~src.schema_matching.MatchResult`.
        explanation: The rendered mismatch report when ``action == "resolve"``;
            an empty string when proceeding.
    """

    action: str
    result: MatchResult
    explanation: str


def discover_schema(
    service: SchemaServiceProtocol,
    headers: Sequence[str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> SchemaDiscoveryDecision:
    """Classify a header row against the registry into a discovery decision.

    Runs the service's registry match and compares the coverage score against the
    Feature B acceptance threshold (reused, not redefined). A score at or above
    the threshold with a selected schema proceeds; otherwise the decision is to
    resolve via the manual-match dialog or the schema builder, carrying the
    rendered mismatch explanation.

    Args:
        service: The schema service used to run the registry match.
        headers: The actual source headers read from the sheet preview.
        threshold: The acceptance threshold for the coverage score; defaults to
            the Feature B :data:`~src.etl_columns.DEFAULT_THRESHOLD`.

    Returns:
        A :class:`SchemaDiscoveryDecision`. ``action`` is ``"proceed"`` only when
        a candidate schema scored at or above ``threshold``.
    """
    result = service.find_best_match(headers)
    # A suitable match requires both a selected candidate and a score that clears
    # the acceptance bar; otherwise the user must resolve the mismatch manually.
    if result.schema is not None and result.score >= threshold:
        return SchemaDiscoveryDecision(action="proceed", result=result, explanation="")
    return SchemaDiscoveryDecision(
        action="resolve", result=result, explanation=result.report.render()
    )


def wire_schema_builder(
    window: MainWindow,
    service: SchemaServiceProtocol,
    dialog_factory: Callable[[], SchemaBuilderDialog] | None = None,
    presenter_factory: (
        Callable[[SchemaBuilderDialog, SchemaServiceProtocol], object] | None
    ) = None,
) -> None:
    """Connect ``schema_builder_requested`` to open the schema builder (AC6).

    The actual open is delegated to :func:`open_schema_builder` so the same path
    is reused by the per-tab "Build new schema" button (WS2). The factory
    arguments are optional: the composition root omits them to use the production
    defaults (keeping ``app.py`` thin), while tests inject recording factories.

    Args:
        window: The shell whose ``schema_builder_requested`` signal is wired.
        service: The schema service the builder presenter drives.
        dialog_factory: Optional factory building a fresh
            :class:`SchemaBuilderDialog` per open; defaults to the production
            factory. Tests inject a recording factory.
        presenter_factory: Optional factory building the
            :class:`SchemaBuilderPresenter` for a given dialog and service;
            defaults to the production factory. Tests inject a recording factory.

    Returns:
        ``None``.

    Side effects:
        Connects ``window.schema_builder_requested`` to a handler that builds and
        shows a dialog, retaining the presenter on ``window``.
    """

    def _open_schema_builder() -> None:
        """Open the schema-builder dialog via the shared open path."""
        open_schema_builder(
            window,
            service,
            dialog_factory=dialog_factory,
            presenter_factory=presenter_factory,
        )

    window.schema_builder_requested.connect(_open_schema_builder)


def wire_build_schema_buttons(
    window: MainWindow,
    service: SchemaServiceProtocol,
    *,
    dialog_factory: Callable[[], SchemaBuilderDialog] | None = None,
    presenter_factory: (
        Callable[[SchemaBuilderDialog, SchemaServiceProtocol], object] | None
    ) = None,
) -> None:
    """Wire each source tab's "Build new schema" button to the builder (WS2).

    Connects the three source widgets' ``build_schema_requested`` signals to the
    shared :func:`open_schema_builder` path so the per-tab "Build new schema"
    button opens the same existing schema builder dialog as the
    ``Tools > Schema Builder...`` menu action (AC-13). The factories are optional
    so the composition root uses the production defaults while tests inject
    recording factories.

    Args:
        window: The shell whose three source widgets carry the build buttons.
        service: The schema service the builder presenter drives.
        dialog_factory: Optional dialog factory; defaults to the production
            factory.
        presenter_factory: Optional presenter factory; defaults to the production
            factory.

    Returns:
        ``None``.

    Side effects:
        Connects each source widget's ``build_schema_requested`` signal to a
        handler that opens the schema builder dialog.
    """

    def _open() -> None:
        """Open the schema builder via the shared open path."""
        open_schema_builder(
            window,
            service,
            dialog_factory=dialog_factory,
            presenter_factory=presenter_factory,
        )

    # Wire all three per-tab build buttons to the same shared open path so any
    # tab's "Build new schema" button opens the existing builder dialog.
    for widget in (window.le_widget, window.aop_widget, window.skulu_widget):
        widget.build_schema_requested.connect(_open)
