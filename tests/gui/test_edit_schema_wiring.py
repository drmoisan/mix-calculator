"""Tests for the Edit-Schema composition wiring (issue #60 Defect 1).

Verifies that :func:`wire_edit_schema_buttons` connects each source tab's
``edit_schema_requested`` signal to a handler that opens the schema builder and
seeds it from the tab's currently-selected schema via
``schema_builder_presenter.load_existing(<selected name>)``. Also verifies the
guard paths: a placeholder/empty selection short-circuits (no builder opens, no
crash), exercising the #50 no-schema seam. Runs headless under
``QT_QPA_PLATFORM=offscreen`` from :mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_discovery_wiring import wire_edit_schema_buttons
from src.gui.main_window import MainWindow
from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog
from tests.gui.fakes.fake_services import FakeSchemaService

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytestqt.qtbot import QtBot


class _RecordingPresenter:
    """Recording schema-builder presenter capturing ``load_existing`` calls.

    Purpose:
        Stand in for the production ``SchemaBuilderPresenter`` so the Edit-Schema
        wiring tests can assert that the selected schema name was seeded via
        ``load_existing`` without constructing the real presenter.

    Attributes:
        loaded: The schema names passed to :meth:`load_existing`, in call order.
    """

    def __init__(self) -> None:
        """Initialize the recorder with an empty call log."""
        self.loaded: list[str] = []

    def load_existing(self, name: str) -> None:
        """Record a ``load_existing`` call.

        Args:
            name: The schema name the wiring seeded the builder from.

        Returns:
            ``None``.
        """
        self.loaded.append(name)


def _dialog_factory(qtbot: QtBot) -> Callable[[], SchemaBuilderDialog]:
    """Return a recording dialog factory that registers each dialog with qtbot.

    Args:
        qtbot: The pytest-qt bot used to manage dialog lifetime.

    Returns:
        A zero-argument factory building a fresh :class:`SchemaBuilderDialog`.
    """

    def _factory() -> SchemaBuilderDialog:
        dialog = SchemaBuilderDialog()
        qtbot.addWidget(dialog)
        return dialog

    return _factory


def test_edit_with_real_schema_opens_builder_and_calls_load_existing(
    qtbot: QtBot,
) -> None:
    """AC-2: clicking Edit with a real schema opens the builder via load_existing.

    The wiring opens a blank builder through the shared open path (retaining the
    presenter on the window) and then seeds it from the selected schema name via
    ``schema_builder_presenter.load_existing(<name>)``.
    """
    # Arrange: a window whose LE tab has a real schema selected, wired with a
    # recording presenter factory.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    presenters: list[_RecordingPresenter] = []

    def presenter_factory(_dialog: object, _service: object) -> object:
        presenter = _RecordingPresenter()
        presenters.append(presenter)
        return presenter

    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=presenter_factory,
    )
    window.le_widget.set_schema_list(["le_v1"])
    window.le_widget.set_selected_schema("le_v1")

    # Act: trigger the Edit button exactly as the user would.
    window.le_widget.edit_schema_requested.emit()

    # Assert: a presenter was retained and seeded from the selected schema name.
    assert len(presenters) == 1
    assert window.schema_builder_presenter is presenters[0]
    assert presenters[0].loaded == ["le_v1"]


def test_edit_with_placeholder_short_circuits_without_opening(qtbot: QtBot) -> None:
    """AC-3/AC-9: an Edit emit on the placeholder opens no builder and does not crash.

    Defense in depth alongside the widget-level disabled state: even if the
    ``edit_schema_requested`` signal fires while the placeholder is selected, the
    wiring short-circuits so no builder opens and no presenter is retained.
    """
    # Arrange: a window left on the placeholder selection.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    opened: list[object] = []

    def presenter_factory(_dialog: object, _service: object) -> object:
        presenter = _RecordingPresenter()
        opened.append(presenter)
        return presenter

    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=presenter_factory,
    )
    assert window.le_widget.current_schema() == "<Choose Schema>"

    # Act: emit the Edit signal while the placeholder is selected.
    window.le_widget.edit_schema_requested.emit()

    # Assert: the guard short-circuited — no builder opened, no presenter retained.
    assert opened == []
    assert window.schema_builder_presenter is None


def test_edit_no_schema_seam_does_not_crash_on_each_tab(qtbot: QtBot) -> None:
    """AC-9: emitting Edit on every tab with no schema selected never crashes (seam).

    Drives the no-schema seam for all three source tabs: with no schema selected,
    each tab's Edit emit short-circuits without opening a builder or raising.
    """
    # Arrange: wire all three tabs with no schema selected on any.
    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=lambda _d, _s: _RecordingPresenter(),
    )

    # Act: emit Edit on each tab with no schema selected (the no-schema seam).
    window.le_widget.edit_schema_requested.emit()
    window.aop_widget.edit_schema_requested.emit()
    window.skulu_widget.edit_schema_requested.emit()

    # Assert: no builder opened on any tab and no exception propagated.
    assert window.schema_builder_presenter is None


def test_edit_with_stub_presenter_lacking_load_existing_does_not_crash(
    qtbot: QtBot,
) -> None:
    """A retained presenter without ``load_existing`` is tolerated (getattr guard).

    The wiring seeds via ``getattr(presenter, "load_existing", None)`` so a
    recording stub that does not expose the seeding contract simply skips
    seeding rather than raising, mirroring the established ``_seed_presenter``
    tolerance for minimal test factories.
    """

    # Arrange: a presenter factory returning a bare stub with no load_existing.
    class _BarePresenter:
        """A minimal presenter stub exposing no ``load_existing`` method."""

    window = MainWindow()
    qtbot.addWidget(window)
    service = FakeSchemaService()
    built: list[_BarePresenter] = []

    def presenter_factory(_dialog: object, _service: object) -> object:
        presenter = _BarePresenter()
        built.append(presenter)
        return presenter

    wire_edit_schema_buttons(
        window,
        service,
        dialog_factory=_dialog_factory(qtbot),
        presenter_factory=presenter_factory,
    )
    window.le_widget.set_schema_list(["le_v1"])
    window.le_widget.set_selected_schema("le_v1")

    # Act: trigger Edit with a real schema; the stub lacks load_existing.
    window.le_widget.edit_schema_requested.emit()

    # Assert: the builder still opened (presenter retained) and no crash occurred
    # despite the absent load_existing seeding contract.
    assert len(built) == 1
    assert window.schema_builder_presenter is built[0]
