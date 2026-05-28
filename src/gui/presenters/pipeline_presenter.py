"""Presenter for import, run, save, and open of the mix pipeline.

This presenter owns the GUI's working state and drives a passive
:class:`PipelineViewProtocol` through the injected
:class:`PipelineServiceProtocol`. It contains no Qt import and is fully testable
without a ``QApplication``. The actual pipeline run is exposed as a plain task
callable so the Phase 8 worker can run it off the UI thread.

Responsibilities:
    - Track per-input import specs, imported frames, derived frames, the working
      DB path, and the running flag.
    - ``on_import_one``/``on_import_all`` populate the imported frames.
    - ``on_run`` guards on non-empty imports, runs the pipeline, and reports.
    - ``on_save``/``on_open_db`` persist and load the SQLite database.

Loader/service ``ValueError`` routes to ``view.show_error``; other exceptions
propagate so genuine defects are not hidden.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from src.gui.pipeline_service import ImportSpec, PipelineServiceProtocol
    from src.gui.protocols import PipelineViewProtocol

__all__ = ["PipelinePresenter"]

logger = logging.getLogger(__name__)

# The three import-table keys the pipeline consumes.
_IMPORT_KEYS = ("LE", "aop", "sku_lu")


class PipelinePresenter:
    """Presenter coordinating import, run, save, and open over the service seam.

    Purpose:
        Hold the GUI's working state and translate user actions (import, run,
        save, open) into service calls and passive-view updates.

    Responsibilities:
        Own the imported/derived table sets, the working DB path, and the
        running flag; guard Run until imports (or an opened DB) exist; report
        outcomes via the view. It contains no Qt code and no transform logic.

    Usage:
        Constructed with a view and a pipeline service at the composition root.
        The Run task is exposed via :meth:`make_run_task` so the worker can run
        it off the UI thread; ``apply_run_result`` records the worker's result.

    Attributes:
        _import_specs: Per-input current file/sheet selection (or ``None``).
        _imported_tables: In-memory imported frames keyed by table name.
        _derived_tables: Derived frames produced by the last run.
        _db_path: Current working DB path, or ``None``.
        _is_running: Whether a pipeline or import job is in flight.
    """

    def __init__(
        self,
        view: PipelineViewProtocol,
        pipeline_service: PipelineServiceProtocol,
    ) -> None:
        """Initialize the presenter with its view and service.

        Args:
            view: The pipeline view to update.
            pipeline_service: The service seam over loaders/transforms/SQLite.
        """
        self._view = view
        self._service = pipeline_service
        self._import_specs: dict[str, ImportSpec | None] = {
            name: None for name in _IMPORT_KEYS
        }
        self._imported_tables: dict[str, pd.DataFrame] = {}
        self._derived_tables: dict[str, pd.DataFrame] = {}
        self._db_path: str | None = None
        self._is_running = False

    @property
    def imported_tables(self) -> dict[str, pd.DataFrame]:
        """Return the current in-memory imported frames."""
        return self._imported_tables

    @property
    def derived_tables(self) -> dict[str, pd.DataFrame]:
        """Return the derived frames from the last successful run."""
        return self._derived_tables

    @property
    def db_path(self) -> str | None:
        """Return the current working DB path, or ``None``."""
        return self._db_path

    @property
    def is_running(self) -> bool:
        """Return whether a pipeline or import job is in flight."""
        return self._is_running

    def on_import_one(self, name: str, spec: ImportSpec) -> None:
        """Import one selected input and record its frame.

        Args:
            name: The import key (``"LE"``, ``"aop"``, or ``"sku_lu"``).
            spec: The per-input file/sheet selection.

        Returns:
            ``None``.

        Side effects:
            Populates ``_imported_tables[name]`` or routes a ``ValueError`` to
            ``view.show_error``.
        """
        logger.info("Importing one source: %r.", name)
        # Route only the matching loader for the requested key. A loader
        # ValueError is a user-facing condition shown via the view.
        try:
            frame = self._import_one_frame(name, spec)
        except ValueError as error:
            logger.error("Import of %r failed: %s", name, error)
            self._view.show_error(str(error))
            return
        self._imported_tables[name] = frame
        self._import_specs[name] = spec

    def _import_one_frame(self, name: str, spec: ImportSpec) -> pd.DataFrame:
        """Call the loader for one import key and return its frame.

        Args:
            name: The import key to load.
            spec: The per-input selection supplying paths and sheet names.

        Returns:
            The imported frame for ``name``.

        Raises:
            ValueError: Propagated from the loader.
            KeyError: When ``name`` is not a known import key.
        """
        # Routing table: each import key maps to its loader call. Ordering is not
        # significant; only the matching key's loader runs.
        if name == "LE":
            return self._service.import_le(spec.le_path, spec.le_sheet)
        if name == "aop":
            return self._service.import_aop(spec.aop_path, spec.aop_sheet)
        if name == "sku_lu":
            skulu_path = spec.skulu_path if spec.skulu_path else spec.le_path
            return self._service.import_skulu(skulu_path, spec.skulu_sheet)
        raise KeyError(f"Unknown import key {name!r}.")

    def on_import_all(self, spec: ImportSpec) -> None:
        """Import all three inputs and record their frames.

        Args:
            spec: The per-input file/sheet selection.

        Returns:
            ``None``.

        Side effects:
            Populates ``_imported_tables`` or routes a ``ValueError`` to
            ``view.show_error``.
        """
        logger.info("Importing all sources.")
        try:
            tables = self._service.import_sources(spec)
        except ValueError as error:
            logger.error("Import-all failed: %s", error)
            self._view.show_error(str(error))
            return
        self._imported_tables = dict(tables)
        for name in _IMPORT_KEYS:
            self._import_specs[name] = spec

    def can_run(self) -> bool:
        """Return whether Run is permitted (non-empty imports, not running).

        Returns:
            ``True`` when there are imported tables and no job is in flight.
        """
        # Run requires at least one imported table and no in-flight job; this is
        # the guard the view uses to enable/disable the Run control.
        return bool(self._imported_tables) and not self._is_running

    def make_run_task(self) -> Callable[[], dict[str, pd.DataFrame]]:
        """Return a zero-argument task that runs the pipeline on current imports.

        The returned callable is what the Phase 8 worker invokes off the UI
        thread; it captures the current imported tables and returns the derived
        dict. It performs no view updates (the worker's signals do).

        Returns:
            A ``Callable[[], dict[str, pd.DataFrame]]`` running the pipeline.
        """
        tables = dict(self._imported_tables)

        def _task() -> dict[str, pd.DataFrame]:
            return self._service.run_pipeline(tables)

        return _task

    def on_run(self) -> None:
        """Run the pipeline synchronously, guarding on non-empty imports.

        This is the in-presenter run path used when no worker is wired (and by
        tests). It sets the running state, calls the service, records the derived
        tables, and reports via the view.

        Returns:
            ``None``.

        Side effects:
            Updates ``_derived_tables`` and the view, or routes a ``ValueError``
            to ``view.show_error``. No-op when the Run guard is not satisfied.
        """
        # Guard: Run is unavailable until import completes or a DB is opened.
        if not self.can_run():
            logger.info("Run requested but unavailable (no imported tables).")
            self._view.show_error("Run is unavailable: import sources first.")
            return

        self._set_running(True)
        try:
            derived = self._service.run_pipeline(dict(self._imported_tables))
        except ValueError as error:
            logger.error("Pipeline run failed: %s", error)
            self._view.show_error(str(error))
            return
        finally:
            self._set_running(False)
        self.apply_run_result(derived)

    def apply_run_result(self, derived: dict[str, pd.DataFrame]) -> None:
        """Record a run result (from the worker or a sync run) and report it.

        Args:
            derived: The derived-table dict produced by the run.

        Returns:
            ``None``.

        Side effects:
            Updates ``_derived_tables`` and pushes a success summary to the view.
        """
        self._derived_tables = dict(derived)
        self._view.show_result(f"Run complete: {len(derived)} derived tables.")

    def on_save(self, path: str) -> None:
        """Persist the working tables to a SQLite database.

        The working set is the derived tables when a run has completed; otherwise
        the imported tables (so a save after open/import still persists).

        Args:
            path: Destination ``.db`` path.

        Returns:
            ``None``.

        Side effects:
            Calls the service to write the database, or routes a ``ValueError``
            to ``view.show_error``. Records the working DB path on success.
        """
        logger.info("Saving working tables to %r.", path)
        # Persist the derived set when present, else the imported set, so a save
        # works after either a run or just an import/open.
        working = (
            self._derived_tables if self._derived_tables else self._imported_tables
        )
        try:
            self._service.save_to_db(dict(working), path)
        except ValueError as error:
            logger.error("Save to %r failed: %s", path, error)
            self._view.show_error(str(error))
            return
        self._db_path = path
        self._view.show_result(f"Saved {len(working)} tables to {path}.")

    def on_open_db(self, path: str) -> None:
        """Load tables from an existing SQLite database into the working set.

        Args:
            path: Source ``.db`` path.

        Returns:
            ``None``.

        Side effects:
            Populates ``_imported_tables`` from the database and records the DB
            path, or routes a ``ValueError`` to ``view.show_error``.
        """
        logger.info("Opening database %r.", path)
        try:
            tables = self._service.open_db(path)
        except ValueError as error:
            logger.error("Open of %r failed: %s", path, error)
            self._view.show_error(str(error))
            return
        self._imported_tables = dict(tables)
        self._db_path = path
        self._view.show_result(f"Opened {len(tables)} tables from {path}.")

    def _set_running(self, is_running: bool) -> None:
        """Update the running flag and notify the view.

        Args:
            is_running: The new running state.

        Returns:
            ``None``.

        Side effects:
            Updates ``_is_running`` and calls ``view.set_running``.
        """
        self._is_running = is_running
        self._view.set_running(is_running)
