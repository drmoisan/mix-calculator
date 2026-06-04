"""Tests for the per-tab schema-dropdown population wiring (issue #48, R-AC-3).

Verifies that ``build_application`` populates each of the three source tabs'
schema dropdowns with the available schema names from the injected schema service
(so the bundled defaults are selectable), and that the underlying
:func:`populate_schema_lists` helper calls ``set_schema_list`` once per view with
the service's names. Runs headless under ``QT_QPA_PLATFORM=offscreen`` from
:mod:`tests.gui.conftest`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui._schema_list_wiring import populate_schema_lists
from src.gui.app import build_application
from src.gui.runners import SynchronousRunner
from tests.gui.fakes.fake_services import FakeSchemaService
from tests.gui.fakes.fake_source_selection_view import FakeSourceSelectionView

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

    from src.gui.widgets.source_input_widget import SourceInputWidget

# The placeholder the widget always inserts as the first dropdown item; the
# populated schema names follow it. Mirrored from the widget so the assertions
# describe the expected post-population dropdown state.
_PLACEHOLDER = "<Choose Schema>"


def _assert_populated_with_defaults(widget: SourceInputWidget) -> None:
    """Assert a source widget's schema dropdown carries the bundled defaults.

    Uses the widget's public surface only (``current_schema`` plus
    ``set_selected_schema``), matching the repository's widget-test convention:
    after population the placeholder is selected, and each bundled-default name
    is selectable, demonstrating the dropdown was filled with those names.

    Args:
        widget: The source widget whose schema dropdown is verified.

    Returns:
        ``None``. Raises ``AssertionError`` on any unmet expectation.
    """
    # Population leaves the placeholder selected so no schema is auto-chosen.
    assert widget.current_schema() == _PLACEHOLDER
    # Each bundled-default name must be selectable from the populated dropdown.
    for name in ("default_aop", "default_le"):
        widget.set_selected_schema(name)
        assert widget.current_schema() == name
    # Reset to the placeholder so the assertion leaves no schema selected.
    widget.set_selected_schema(_PLACEHOLDER)


def test_build_application_populates_each_tab_schema_dropdown(qtbot: QtBot) -> None:
    """All three source tabs' dropdowns carry the bundled-default names (R-AC-3)."""
    # Arrange: inject a fake service offering the two bundled defaults.
    service = FakeSchemaService(schema_names=["default_aop", "default_le"])

    # Act: build the wired application with the fake service and a sync runner.
    wired = build_application(schema_service=service, runner=SynchronousRunner())
    qtbot.addWidget(wired.window)

    # Assert: each tab's dropdown was populated with the bundled defaults,
    # demonstrating a production caller of set_schema_list populated with defaults.
    for widget in (
        wired.window.le_widget,
        wired.window.aop_widget,
        wired.window.skulu_widget,
    ):
        _assert_populated_with_defaults(widget)


def test_populate_schema_lists_calls_set_schema_list_once_per_view() -> None:
    """populate_schema_lists pushes the service names to each view exactly once."""
    # Arrange: two fake views and a service offering the bundled-default names.
    views = [FakeSourceSelectionView(), FakeSourceSelectionView()]
    service = FakeSchemaService(schema_names=["default_aop", "default_le"])

    # Act
    populate_schema_lists(views, service)

    # Assert: each view recorded exactly one set_schema_list call with the names.
    for view in views:
        assert view.schema_lists == [["default_aop", "default_le"]]
