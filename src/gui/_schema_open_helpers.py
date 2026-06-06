"""Open-path helpers for the schema-builder dialog (drag-tab + template seeding).

This module holds the dialog open-path helpers extracted from
:mod:`src.gui._schema_wiring` so that file stays under the repository's 500-line
cap once the drag-tab preview seeding, the Derived-tab handler, and the
new-from-template open path are wired:

    - ``seed_dialog_preview_slice``: push the masked preview slice into the dialog's
      drag Columns tab before the presenter seeds (Decision 4/5).
    - ``install_new_derived_handler``: install the Derived-tab "New derived column"
      handler that opens the PowerQuery-style formula dialog (Decision 7).
    - ``open_new_from_template_builder``: open the builder seeded from an existing
      schema as a template with a cleared name (Decision 6, R5/R6).

Scope boundaries:
    - Qt open-path wiring only; no transform logic. The presenter owns state and
      assembly; the formula dialog reuses the existing evaluator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.main_window import MainWindow
    from src.gui.presenters._schema_builder_state import PreviewSlice
    from src.gui.services.schema_service import SchemaServiceProtocol
    from src.gui.widgets.schema_builder_dialog import SchemaBuilderDialog

__all__ = [
    "install_new_derived_handler",
    "open_new_from_template_builder",
    "seed_dialog_preview_slice",
]


def seed_dialog_preview_slice(
    dialog: SchemaBuilderDialog, preview_slice: PreviewSlice | None
) -> None:
    """Push the masked preview slice into the dialog's drag Columns tab.

    Args:
        dialog: The schema-builder dialog (or a test stub) to seed.
        preview_slice: The masked preview slice, or ``None`` for the blank path.

    Returns:
        ``None``.

    Side effects:
        Calls ``dialog.set_columns_preview_slice`` when the dialog supports it;
        recording test stubs that lack the method are skipped.
    """
    setter = getattr(dialog, "set_columns_preview_slice", None)
    # Only the production dialog exposes the drag-tab slice setter; minimal test
    # stubs skip it so they remain compatible with the open path.
    if callable(setter):
        setter(preview_slice)


def install_new_derived_handler(dialog: SchemaBuilderDialog, presenter: object) -> None:
    """Install the Derived-tab "New derived column" handler on the dialog.

    The handler opens the :class:`DerivedFormulaDialog` over the live presenter
    state (declared + prior-derived names, reusing the existing evaluator) and, on
    accept, appends the authored derived column so it surfaces on the Columns tab.

    Args:
        dialog: The schema-builder dialog to install the handler on.
        presenter: The schema-builder presenter driving the dialog.

    Returns:
        ``None``.

    Side effects:
        Calls ``dialog.set_new_derived_handler`` when both the dialog and presenter
        expose the required seams; otherwise it is a no-op so minimal test stubs
        remain compatible.
    """
    from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter

    install = getattr(dialog, "set_new_derived_handler", None)
    # Require the production dialog seam and a concrete presenter; a minimal
    # recording stub that lacks either skips installation rather than failing the
    # open path.
    if not callable(install) or not isinstance(presenter, SchemaBuilderPresenter):
        return
    concrete_presenter = presenter

    def _open_derived_dialog() -> None:
        """Open the derived-formula dialog and append an accepted derived column."""
        from src.gui.presenters._schema_builder_state import known_column_names
        from src.gui.widgets._derived_formula_dialog import DerivedFormulaDialog

        # Offer the declared columns plus prior-derived names so a new formula may
        # reference any existing or earlier-derived column.
        available = known_column_names(concrete_presenter.state)
        derived_dialog = DerivedFormulaDialog(available, parent=dialog)
        # A rejected dialog leaves the schema unchanged; only an accepted, validated
        # entry appends a derived column.
        if derived_dialog.exec() and derived_dialog.validate_current():
            concrete_presenter.add_derived(
                derived_dialog.derived_name(), derived_dialog.derived_expression()
            )

    install(_open_derived_dialog)


def open_new_from_template_builder(
    window: MainWindow,
    service: SchemaServiceProtocol,
    template_name: str,
    *,
    dialog_factory: Callable[[], SchemaBuilderDialog] | None = None,
    presenter_factory: (
        Callable[[SchemaBuilderDialog, SchemaServiceProtocol], object] | None
    ) = None,
) -> None:
    """Open the builder seeded from an existing schema as a template (Decision 6).

    Shared by the explicit "New from template" affordance (R5) and the source-tab
    partial-match hand-off (R6). A fresh dialog and presenter are built, then the
    presenter's ``new_from_template`` copies the closest existing schema's columns,
    structured key, and dedup into the live dialog with a cleared Identity name so a
    subsequent save-as writes a new schema and never overwrites the template.

    Args:
        window: The shell the presenter is retained on.
        service: The schema service the builder presenter drives.
        template_name: The closest existing schema's name to seed the template from.
        dialog_factory: Optional dialog factory; defaults to the production factory.
        presenter_factory: Optional presenter factory; defaults to the production
            factory.

    Returns:
        ``None``.

    Side effects:
        Builds and shows a dialog seeded from ``template_name`` with a blank name,
        retaining the presenter on ``window``.
    """
    from src.gui._schema_wiring import default_schema_builder_factories
    from src.gui.presenters.schema_builder_presenter import SchemaBuilderPresenter

    # Resolve the production factories unless the caller (tests) injects recorders.
    if dialog_factory is None or presenter_factory is None:
        default_dialog, default_presenter = default_schema_builder_factories()
        dialog_factory = dialog_factory or default_dialog
        presenter_factory = presenter_factory or default_presenter
    dialog = dialog_factory()
    presenter = presenter_factory(dialog, service)
    window.schema_builder_presenter = presenter
    # Install the derived handler so the template's Derived tab stays functional.
    install_new_derived_handler(dialog, presenter)
    # Seed from the template through the production presenter's new_from_template
    # path; a recording test stub that is not a concrete presenter skips seeding.
    if isinstance(presenter, SchemaBuilderPresenter):
        presenter.new_from_template(template_name)
    dialog.show()
