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

    from src.gui._schema_build_specs import BuildSpecProvider
    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
    from src.schema_matching import MatchResult
    from src.schema_model import ColumnSpec

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
    required_specs: Sequence[ColumnSpec] | None = None,
    optional_specs: Sequence[ColumnSpec] | None = None,
    default_key_pattern: str | None = None,
    preview_slice: PreviewSlice | None = None,
) -> None:
    """Open the schema-builder dialog driven by a fresh presenter.

    This is the imperative open path shared by the ``schema_builder_requested``
    menu action and the per-tab "Build/Edit schema" button (WS2). A new dialog
    and presenter are built per open so the builder is repeatable; the presenter
    is retained on the window to keep it alive for the lifetime of the (modeless)
    dialog.

    When the per-tab caller supplies its source-specific required/optional specs,
    a default key pattern, and a masked preview slice, the presenter is seeded
    from them (Decision 7). When all of these are omitted — the menu-action path —
    a blank builder opens unchanged.

    Args:
        window: The shell the presenter is retained on.
        service: The schema service the builder presenter drives.
        dialog_factory: Optional dialog factory; defaults to the production
            :class:`SchemaBuilderDialog` factory.
        presenter_factory: Optional presenter factory; defaults to the production
            :class:`SchemaBuilderPresenter` factory.
        required_specs: The source's required column specs, or ``None`` for the
            blank menu path.
        optional_specs: The source's optional column specs, or ``None`` for the
            blank menu path.
        default_key_pattern: The source's default key pattern string parsed into
            structured key parts, or ``None`` for the blank menu path.
        preview_slice: The masked preview slice the builder reads for the token
            pool and dtype check, or ``None`` for the blank menu path.

    Returns:
        ``None``.

    Side effects:
        Builds and shows a dialog, retaining the presenter on ``window``; seeds
        the presenter from caller specs when supplied.
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
    presenter = presenter_factory(dialog, service)
    window.schema_builder_presenter = presenter
    # Seed from caller specs only when the per-tab path supplies them; the blank
    # menu path leaves the presenter empty. seed_from_caller is a no-op for empty
    # inputs, so guarding on "any input present" keeps the menu path blank.
    if _has_caller_specs(
        required_specs, optional_specs, default_key_pattern, preview_slice
    ):
        _seed_presenter(
            presenter,
            required_specs,
            optional_specs,
            default_key_pattern,
            preview_slice,
        )
    dialog.show()


def _has_caller_specs(
    required_specs: Sequence[ColumnSpec] | None,
    optional_specs: Sequence[ColumnSpec] | None,
    default_key_pattern: str | None,
    preview_slice: PreviewSlice | None,
) -> bool:
    """Report whether the per-tab caller supplied any seeding input.

    Args:
        required_specs: The required specs, or ``None``.
        optional_specs: The optional specs, or ``None``.
        default_key_pattern: The default key pattern, or ``None``.
        preview_slice: The masked preview slice, or ``None``.

    Returns:
        ``True`` when at least one seeding input is present (the per-tab path);
        ``False`` when all are absent (the blank menu path).
    """
    return any(
        value is not None
        for value in (
            required_specs,
            optional_specs,
            default_key_pattern,
            preview_slice,
        )
    )


def _seed_presenter(
    presenter: object,
    required_specs: Sequence[ColumnSpec] | None,
    optional_specs: Sequence[ColumnSpec] | None,
    default_key_pattern: str | None,
    preview_slice: PreviewSlice | None,
) -> None:
    """Invoke the presenter's caller-seeding path when it supports it.

    The presenter factory's return type is ``object`` so the wiring need not
    import the concrete presenter. This helper calls ``seed_from_caller`` when the
    built presenter exposes it (the production presenter does), letting recording
    test factories that return a bare stub remain compatible.

    Args:
        presenter: The presenter the factory produced.
        required_specs: The required specs to seed, or ``None``.
        optional_specs: The optional specs to seed, or ``None``.
        default_key_pattern: The default key pattern to parse, or ``None``.
        preview_slice: The masked preview slice to seed, or ``None``.

    Returns:
        ``None``.

    Side effects:
        Seeds the presenter state when the presenter supports seeding.
    """
    seed = getattr(presenter, "seed_from_caller", None)
    # Only seed when the presenter exposes the seeding contract; recording test
    # factories that return a minimal stub simply skip seeding.
    if callable(seed):
        seed(
            required_specs=required_specs,
            optional_specs=optional_specs,
            default_key_pattern=default_key_pattern,
            preview_slice=preview_slice,
        )


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
    spec_provider: BuildSpecProvider | None = None,
) -> None:
    """Wire each source tab's "Build/Edit schema" button to the builder (WS2).

    Connects the three source widgets' ``build_schema_requested`` signals to the
    shared :func:`open_schema_builder` path so the per-tab "Build/Edit schema"
    button opens the same existing schema builder dialog as the
    ``Tools > Schema Builder...`` menu action (AC-13). When a ``spec_provider`` is
    supplied, each per-tab button passes its source-specific required/optional
    specs, default key pattern, and masked preview slice so the presenter is
    seeded (Decision 7); without a provider every button opens a blank builder.

    Args:
        window: The shell whose three source widgets carry the build buttons.
        service: The schema service the builder presenter drives.
        dialog_factory: Optional dialog factory; defaults to the production
            factory.
        presenter_factory: Optional presenter factory; defaults to the production
            factory.
        spec_provider: Optional per-source build-spec provider mapping a source
            key to its :class:`~src.gui._schema_build_specs.CallerBuildSpec`. When
            ``None``, each button opens a blank builder.

    Returns:
        ``None``.

    Side effects:
        Connects each source widget's ``build_schema_requested`` signal to a
        handler that opens the schema builder dialog seeded for that source.
    """

    def _make_open(key: str) -> Callable[[], None]:
        """Build the per-key open handler that seeds from the source's spec.

        Args:
            key: The source key (``"LE"``, ``"aop"``, ``"sku_lu"``) bound to the
                widget whose build button triggers this handler.

        Returns:
            A zero-argument handler opening the builder seeded for ``key``.
        """

        def _open() -> None:
            """Open the schema builder, seeding from the source's build spec."""
            # Resolve this source's caller spec when a provider is present so the
            # per-tab path seeds the presenter; otherwise open a blank builder.
            spec = spec_provider.build_spec_for(key) if spec_provider else None
            open_schema_builder(
                window,
                service,
                dialog_factory=dialog_factory,
                presenter_factory=presenter_factory,
                required_specs=spec.required_specs if spec else None,
                optional_specs=spec.optional_specs if spec else None,
                default_key_pattern=spec.default_key_pattern if spec else None,
                preview_slice=spec.preview_slice if spec else None,
            )

        return _open

    # Wire all three per-tab build buttons to a per-key open handler so each tab's
    # "Build/Edit schema" button opens the builder seeded for its own source.
    for key, widget in (
        ("LE", window.le_widget),
        ("aop", window.aop_widget),
        ("sku_lu", window.skulu_widget),
    ):
        widget.build_schema_requested.connect(_make_open(key))
