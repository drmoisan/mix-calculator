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
        _last_imported_path: Per-input last successful import path (or the
            ``"db:<path>"`` sentinel when an Open populated the key). Tracked
            so :meth:`on_file_path_changed` can re-enable the import button on
            a new selection without flipping it for the same path.
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
        # Per-spec section 2: track the last successfully-imported (or opened)
        # source path for each input. on_file_path_changed compares the new
        # path against this state to decide whether to re-enable the button.
        self._last_imported_path: dict[str, str | None] = {
            name: None for name in _IMPORT_KEYS
        }

    @property
    def imported_tables(self) -> dict[str, pd.DataFrame]:
        """Return the current in-memory imported frames."""
        return self._imported_tables

    @property
    def derived_tables(self) -> dict[str, pd.DataFrame]:
        """Return the derived frames from the last successful run."""
        return self._derived_tables

    @property
    def last_imported_path(self) -> dict[str, str | None]:
        """Return the per-key last successfully-imported path map.

        For keys loaded via :meth:`on_open_db`, the value is the
        ``"db:<path>"`` sentinel rather than a workbook path.
        """
        return dict(self._last_imported_path)

    def set_last_imported_path_for_test(self, key: str, path: str | None) -> None:
        """Test-only seam: set the per-key last-imported path directly.

        Exposed so the property-based test for :meth:`on_file_path_changed`
        can seed an exact initial state without reaching into private state.
        """
        self._last_imported_path[key] = path

    @property
    def working_tables(self) -> dict[str, pd.DataFrame]:
        """Return the working-table set: derived frames when present, else imports.

        Per spec section "working_tables property": Run, Save, and Export all
        operate on this set so a save-after-import or export-after-import still
        works, while a run promotes the derived frames to the working set.
        """
        return self._derived_tables if self._derived_tables else self._imported_tables

    @property
    def db_path(self) -> str | None:
        """Return the current working DB path, or ``None``."""
        return self._db_path

    @property
    def is_running(self) -> bool:
        """Return whether a pipeline or import job is in flight."""
        return self._is_running

    def _resolve_path_for_key(self, key: str, spec: ImportSpec) -> str:
        """Return the source path the spec carries for an import key.

        Args:
            key: ``"LE"``, ``"aop"``, or ``"sku_lu"``.
            spec: The per-input file/sheet selection.

        Returns:
            The path that the matching loader will read. For ``"sku_lu"`` the
            spec may carry an empty ``skulu_path`` in which case the LE path is
            substituted, matching :meth:`_import_one_frame`.
        """
        if key == "LE":
            return spec.le_path
        if key == "aop":
            return spec.aop_path
        if key == "sku_lu":
            return spec.skulu_path if spec.skulu_path else spec.le_path
        raise KeyError(f"Unknown import key {key!r}.")

    def on_file_path_changed(self, key: str, path: str) -> None:
        """Re-enable the keyed import button when the user picks a new source.

        Per spec section 2: a user-selected path that differs from the last
        successfully-imported path for the same key re-enables that key's
        Import button. A no-op when the path equals the last-imported value
        (including the ``"db:<path>"`` sentinel set by :meth:`on_open_db`).

        Args:
            key: The import key whose source changed.
            path: The newly-selected source path.

        Returns:
            ``None``.

        Side effects:
            Calls ``view.set_import_button_enabled(key, True)`` when
            ``path != self._last_imported_path[key]``; otherwise no-op.
        """
        if path != self._last_imported_path.get(key):
            self._view.set_import_button_enabled(key, True)

    def _push_action_enabled_states(self) -> None:
        """Push Save/Export enabled flags based on the working-table set.

        Save and Export are enabled iff there is at least one working table
        (imports or derived). Run uses ``can_run()`` which is pushed from the
        per-import success path so a partial import enables Run.
        """
        has_working = bool(self.working_tables)
        self._view.set_save_button_enabled(has_working)
        self._view.set_export_button_enabled(has_working)

    def on_import_one(self, name: str, spec: ImportSpec) -> None:
        """Import one selected input and record its frame.

        Args:
            name: The import key (``"LE"``, ``"aop"``, or ``"sku_lu"``).
            spec: The per-input file/sheet selection.

        Returns:
            ``None``.

        Side effects:
            Populates ``_imported_tables[name]`` or routes a ``ValueError`` to
            ``view.show_error``. On success: invalidates ``_derived_tables`` per
            spec "Derived-table invalidation rule", records the path, disables
            the import button, and recomputes Run/Save/Export enable states.
        """
        logger.info("Importing one source: %r.", name)
        # Route only the matching loader for the requested key. A loader
        # ValueError is a user-facing condition shown via the view; the import
        # button stays enabled so the user can retry.
        try:
            frame = self._import_one_frame(name, spec)
        except ValueError as error:
            logger.error("Import of %r failed: %s", name, error)
            self._view.show_error(str(error))
            return
        self._imported_tables[name] = frame
        self._import_specs[name] = spec
        self._last_imported_path[name] = self._resolve_path_for_key(name, spec)
        # Derived-table invalidation rule: a successful re-import invalidates
        # the prior derived set so a downstream run rebuilds.
        self._derived_tables = {}
        self._view.set_import_button_enabled(name, False)
        self._view.set_run_button_enabled(self.can_run())
        self._push_action_enabled_states()

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

        On full success every keyed import button is disabled and Run is
        enabled. A bulk-service ``ValueError`` surfaces via
        ``view.show_error`` and leaves the prior state in place (button states
        are not flipped).

        Args:
            spec: The per-input file/sheet selection.

        Returns:
            ``None``.

        Side effects:
            Populates ``_imported_tables`` on full success, records per-key
            last-imported paths, disables imported-key buttons, invalidates
            derived tables, and pushes Run/Save/Export states.
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
            self._last_imported_path[name] = self._resolve_path_for_key(name, spec)
            self._view.set_import_button_enabled(name, False)
        # Derived-table invalidation rule applies to import-all as well.
        self._derived_tables = {}
        self._view.set_run_button_enabled(self.can_run())
        self._push_action_enabled_states()

    def can_run(self) -> bool:
        """Return whether Run is permitted (non-empty working set, not running).

        Per spec section 4: a successful Open populates the working set even
        without a fresh import, so Run becomes available after Open too.

        Returns:
            ``True`` when the working-table set is non-empty and no job is
            in flight.
        """
        return bool(self.working_tables) and not self._is_running

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
            Updates ``_derived_tables``, pushes a success summary to the view,
            and recomputes Save/Export enabled states for the new working set.
        """
        self._derived_tables = dict(derived)
        self._view.show_result(f"Run complete: {len(derived)} derived tables.")
        self._push_action_enabled_states()

    def on_run_success(self, derived: dict[str, pd.DataFrame]) -> None:
        """Handle a successful worker run; record result and re-enable Run.

        Per spec section 4 / research Q6: the worker reports success on the UI
        thread through this slot. It delegates to :meth:`apply_run_result` and
        re-enables the Run button after the run completes.

        Args:
            derived: The derived-table dict the worker emitted.

        Returns:
            ``None``.

        Side effects:
            Records the derived set and pushes Run/Save/Export enabled states.
        """
        self.apply_run_result(derived)
        self._set_running(False)
        self._view.set_run_button_enabled(True)

    def on_run_error(self, message: str) -> None:
        """Handle a worker run failure; surface the error and re-enable Run.

        Args:
            message: The error message emitted by the worker.

        Returns:
            ``None``.

        Side effects:
            Calls ``view.show_error``, clears the running flag, and re-enables
            the Run button so the user can retry.
        """
        self._view.show_error(message)
        self._set_running(False)
        self._view.set_run_button_enabled(True)

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
        working = self.working_tables
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
            Populates ``_imported_tables`` from the database, records the DB
            path, and sets the ``"db:<path>"`` sentinel for each loaded key
            (per research Q4) so a fresh user file selection re-enables that
            import button. On success disables imported-key buttons, enables
            Run, and pushes Save/Export enabled states.
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
        sentinel = f"db:{path}"
        # For each known import key that the database loaded, record the
        # sentinel and disable the matching import button. A later
        # on_file_path_changed for that key with a real workbook path will
        # differ from the sentinel and re-enable the button.
        for key in _IMPORT_KEYS:
            if key in tables:
                self._last_imported_path[key] = sentinel
                self._view.set_import_button_enabled(key, False)
        self._view.show_result(f"Opened {len(tables)} tables from {path}.")
        self._view.set_run_button_enabled(self.can_run())
        self._push_action_enabled_states()

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
