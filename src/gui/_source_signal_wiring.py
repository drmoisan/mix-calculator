"""Composition-root wiring for per-source input widget signals.

This helper connects each source input widget's ``file_selected`` and
``render_tab_requested`` signals to its source-selection presenter, and reports
each file selection to the pipeline presenter so the Import button re-enables on a
fresh pick. It is extracted from :mod:`src.gui.app` so the composition root stays
under the repository's 500-line cap.

Responsibilities:
    - ``wire_source_signals``: connect the three source widgets' selection and
      render-tab signals to their presenters and the pipeline presenter.

Scope boundaries:
    - Qt signal wiring only; no transform logic. All behavior lives in the injected
      presenters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.pipeline_service import ImportSpec

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.gui.main_window import MainWindow
    from src.gui.presenters.pipeline_presenter import PipelinePresenter
    from src.gui.presenters.source_selection_presenter import SourceSelectionPresenter

__all__ = ["current_import_spec", "wire_source_signals"]


def current_import_spec(window: MainWindow) -> ImportSpec:
    """Read the user's per-input file/sheet selection from the main window.

    Args:
        window: The shell exposing the three source input widgets.

    Returns:
        An :class:`ImportSpec` populated from the live widget state.
    """
    # Read each widget's path/sheet directly so the spec always reflects the
    # current user selection at the moment the signal fires.
    return ImportSpec(
        le_path=window.le_widget.current_path(),
        le_sheet=window.le_widget.current_sheet(),
        aop_path=window.aop_widget.current_path(),
        aop_sheet=window.aop_widget.current_sheet(),
        skulu_path=window.skulu_widget.current_path(),
        skulu_sheet=window.skulu_widget.current_sheet(),
    )


def wire_source_signals(
    window: MainWindow,
    pipeline_presenter: PipelinePresenter,
    le_presenter: SourceSelectionPresenter,
    aop_presenter: SourceSelectionPresenter,
    skulu_presenter: SourceSelectionPresenter,
) -> None:
    """Connect the three source widgets' selection and render-tab signals.

    For each source tab, connects:

    - ``file_selected`` to the source presenter's ``on_file_selected`` so a file
      pick populates the tab dropdown;
    - ``render_tab_requested`` to ``on_render_tab`` so a render request previews
      through the shared preview widget;
    - ``file_selected`` to the pipeline presenter's ``on_file_path_changed`` (keyed
      per source) so the Import button re-enables on a fresh pick (v2 AC-2/3/4).

    Args:
        window: The shell carrying the three source input widgets.
        pipeline_presenter: The pipeline presenter notified of path changes.
        le_presenter: The LE source-selection presenter.
        aop_presenter: The AOP source-selection presenter.
        skulu_presenter: The SKU_LU source-selection presenter.

    Returns:
        ``None``.

    Side effects:
        Connects each source widget's ``file_selected`` and
        ``render_tab_requested`` signals to the presenters.
    """
    # Pair each widget with its presenter and pipeline source key so the same
    # wiring applies uniformly to all three source tabs.
    for widget, presenter, key in (
        (window.le_widget, le_presenter, "LE"),
        (window.aop_widget, aop_presenter, "aop"),
        (window.skulu_widget, skulu_presenter, "sku_lu"),
    ):
        widget.file_selected.connect(presenter.on_file_selected)
        widget.render_tab_requested.connect(presenter.on_render_tab)
        widget.file_selected.connect(_make_path_changed(pipeline_presenter, key))


def _make_path_changed(
    pipeline_presenter: PipelinePresenter, key: str
) -> Callable[[str], None]:
    """Build a per-source file-path-changed handler bound to the pipeline presenter.

    Args:
        pipeline_presenter: The pipeline presenter notified of the path change.
        key: The pipeline source key (``"LE"``, ``"aop"``, or ``"sku_lu"``).

    Returns:
        A one-argument handler reporting the new path under ``key``.
    """

    def _on_path_changed(path: str) -> None:
        """Report the new path for this source to the pipeline presenter."""
        pipeline_presenter.on_file_path_changed(key, path)

    return _on_path_changed
