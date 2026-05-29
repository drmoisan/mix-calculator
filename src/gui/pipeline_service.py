"""Service seam over the existing mix-pipeline loaders and transforms.

This module is the single seam the GUI presenters use to import sources, run the
pure transform pipeline, and persist/load the SQLite result database. It reuses
the existing loaders (:mod:`src.normalize_le`, :mod:`src.load_aop`,
:mod:`src.load_skulu`) and the pure transform chain
(:mod:`src.mix_lookups`, :mod:`src.mix_transforms`, :mod:`src.mix_pipeline_run`)
exactly as the CLI ``mix_pipeline.main`` does; it re-implements none of that
logic. The CLI surface (:mod:`src.mix_pipeline`) is unchanged.

Responsibilities:
    - ``import_le``/``import_aop``/``import_skulu`` read one source via the
      reused loaders and return an in-memory frame (no disk write).
    - ``import_sources`` imports all three inputs from an :class:`ImportSpec`,
      defaulting the SKU_LU workbook to the LE/AOP workbook when unspecified
      (mirrors the CLI ``--skulu-input`` default).
    - ``run_pipeline`` runs the topological transform chain in memory and returns
      the full derived-table dict. It performs no I/O.
    - ``save_to_db``/``open_db`` delegate SQLite write/read to a
      :class:`~src.gui.services.db_service.DbService` (wired in a later phase).

Boundaries:
    - Excel reads route through the reused loaders (which use ``src.pandas_io``).
    - SQLite reads/writes route through the injected ``DbService`` (which uses
      ``src.pandas_io``).
    - ``run_pipeline`` is pure orchestration over the existing transforms.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from src import load_aop, load_skulu, normalize_le
from src.gui.services.db_service import DbService
from src.mix_lookups import (
    build_aop_norm,
    build_aop_vs_le,
    build_customer_lu,
    build_le_norm,
    build_mix_base,
)
from src.mix_pipeline_run import run_transforms
from src.mix_transforms import pivot_aop, pivot_le

if TYPE_CHECKING:
    import pandas as pd

__all__ = [
    "ImportSpec",
    "PipelineService",
    "PipelineServiceProtocol",
]

logger = logging.getLogger(__name__)

# The three import-table keys produced by import_sources, matching the SQLite
# table names the CLI writes (LE uppercase; aop and sku_lu lowercase).
_LE_KEY = "LE"
_AOP_KEY = "aop"
_SKULU_KEY = "sku_lu"


@dataclass(frozen=True)
class ImportSpec:
    """Immutable per-input file/sheet selection for an import.

    Purpose:
        Carry the user's per-input (LE, AOP, SKU_LU) workbook path and worksheet
        name from the source-selection presenter to the pipeline service.

    Attributes:
        le_path: Filesystem path to the LE workbook.
        le_sheet: LE worksheet name (default sheet ``"LE-8 + 4"``).
        aop_path: Filesystem path to the AOP workbook.
        aop_sheet: AOP worksheet name (default sheet ``"AOP1"``).
        skulu_path: Filesystem path to the SKU_LU workbook. When empty, the
            service defaults it to the LE/AOP workbook (mirrors the CLI
            ``--skulu-input`` default).
        skulu_sheet: SKU_LU worksheet name (default sheet ``"SKU_LU"``).
    """

    le_path: str
    le_sheet: str
    aop_path: str
    aop_sheet: str
    skulu_path: str
    skulu_sheet: str


class PipelineServiceProtocol(Protocol):
    """Contract for the GUI pipeline service seam.

    Purpose:
        Decouple presenters from the concrete service so tests can inject a fake.

    Responsibilities:
        Import sources, run the transform pipeline, and save/open the SQLite
        result database. Implementations perform the import/run/persist work; the
        Protocol carries only the call surface the presenters depend on.
    """

    def import_sources(self, spec: ImportSpec) -> dict[str, pd.DataFrame]:
        """Import all three inputs from a spec and return the import frames.

        Args:
            spec: The per-input file/sheet selection.

        Returns:
            A dict keyed ``"LE"``, ``"aop"``, ``"sku_lu"``.
        """
        ...

    def import_le(self, path: str, sheet: str) -> pd.DataFrame:
        """Import the LE source frame.

        Args:
            path: LE workbook path.
            sheet: LE worksheet name.

        Returns:
            The normalized, validated LE frame.
        """
        ...

    def import_aop(self, path: str, sheet: str) -> pd.DataFrame:
        """Import the AOP source frame.

        Args:
            path: AOP workbook path.
            sheet: AOP worksheet name.

        Returns:
            The validated AOP frame.
        """
        ...

    def import_skulu(self, path: str, sheet: str) -> pd.DataFrame:
        """Import the SKU_LU source frame.

        Args:
            path: SKU_LU workbook path.
            sheet: SKU_LU worksheet name.

        Returns:
            The cleaned SKU lookup frame.
        """
        ...

    def run_pipeline(self, tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Run the transform pipeline over imported frames.

        Args:
            tables: The imported frames keyed ``"LE"``, ``"aop"``, ``"sku_lu"``.

        Returns:
            The full derived-table dict.
        """
        ...

    def save_to_db(self, tables: dict[str, pd.DataFrame], db_path: str) -> None:
        """Persist every working table to a SQLite database.

        Args:
            tables: The working tables to persist.
            db_path: Destination ``.db`` path.

        Returns:
            ``None``.
        """
        ...

    def open_db(self, db_path: str) -> dict[str, pd.DataFrame]:
        """Load the known tables from an existing SQLite database.

        Args:
            db_path: Source ``.db`` path.

        Returns:
            The loaded tables keyed by table name.
        """
        ...


class PipelineService:
    """Concrete pipeline service over the reused loaders and transforms.

    Purpose:
        Provide the GUI's import/run/save/open operations by calling the existing
        loader and transform APIs directly, with no re-implementation.

    Responsibilities:
        Import the LE/AOP/SKU_LU frames in memory, orchestrate the pure transform
        chain identically to ``mix_pipeline.main`` steps 1-8 plus ``run_transforms``,
        and delegate SQLite persistence/loading to an injected ``DbService``.

    Usage:
        Constructed once at the composition root with an optional ``DbService``;
        presenters call its methods. Loader ``ValueError`` (column/KEY/tie-out
        failures) propagates unchanged for the presenter to surface. The SQLite
        ``save_to_db``/``open_db`` operations delegate to the injected
        ``DbService``.

    Attributes:
        _db_service: The SQLite read/write collaborator (constructor-injected).
    """

    def __init__(self, db_service: DbService | None = None) -> None:
        """Initialize the service with an optional DB collaborator.

        Args:
            db_service: The SQLite read/write service. When ``None`` a default
                :class:`DbService` is constructed so the production composition
                root need not supply one.
        """
        # Default to a plain DbService so callers that do not need to substitute
        # the SQLite boundary get a working service without extra wiring.
        self._db_service = db_service if db_service is not None else DbService()

    def import_le(self, path: str, sheet: str) -> pd.DataFrame:
        """Load, normalize, and validate the LE source, returning the frame.

        Mirrors the CLI import for LE: ``load_source`` -> ``normalize`` ->
        ``validate_tieouts``. No ``write_sqlite`` is performed; the frame is
        returned in memory.

        Args:
            path: Filesystem path to the LE workbook.
            sheet: LE worksheet name.

        Returns:
            The normalized, tie-out-validated LE DataFrame.

        Raises:
            ValueError: Propagated from the LE loader on a column-resolution,
                KEY-resolution, or tie-out failure.
        """
        logger.info("Importing LE source from sheet %r.", sheet)
        le_source = normalize_le.load_source(path, sheet)
        le_output = normalize_le.normalize(le_source)
        normalize_le.validate_tieouts(le_source, le_output)
        return le_output

    def import_aop(self, path: str, sheet: str) -> pd.DataFrame:
        """Load and validate the AOP source, returning the frame.

        Args:
            path: Filesystem path to the AOP workbook.
            sheet: AOP worksheet name.

        Returns:
            The validated AOP DataFrame.

        Raises:
            ValueError: Propagated from the AOP loader on a column/KEY/validation
                failure.
        """
        logger.info("Importing AOP source from sheet %r.", sheet)
        return load_aop.load_aop(path, sheet=sheet)

    def import_skulu(self, path: str, sheet: str) -> pd.DataFrame:
        """Load and clean the SKU_LU source, returning the frame.

        Args:
            path: Filesystem path to the SKU_LU workbook.
            sheet: SKU_LU worksheet name.

        Returns:
            The cleaned SKU lookup DataFrame.

        Raises:
            ValueError: Propagated from the SKU_LU loader on a column-resolution
                failure.
        """
        logger.info("Importing SKU_LU source from sheet %r.", sheet)
        return load_skulu.load_skulu(path, sheet=sheet)

    def import_sources(self, spec: ImportSpec) -> dict[str, pd.DataFrame]:
        """Import all three inputs from a spec and return the import frames.

        The SKU_LU workbook defaults to the LE/AOP workbook when ``skulu_path`` is
        empty, mirroring the CLI ``--skulu-input`` default where SKU_LU lives on
        the same workbook as the AOP/LE sheets.

        Args:
            spec: The per-input file/sheet selection.

        Returns:
            A dict keyed ``"LE"``, ``"aop"``, ``"sku_lu"`` of the imported frames.

        Raises:
            ValueError: Propagated unchanged from any of the three loaders.
        """
        # Default the SKU_LU workbook to the LE workbook when the user did not
        # select a separate SKU_LU file, matching the CLI default behavior.
        skulu_path = spec.skulu_path if spec.skulu_path else spec.le_path
        return {
            _LE_KEY: self.import_le(spec.le_path, spec.le_sheet),
            _AOP_KEY: self.import_aop(spec.aop_path, spec.aop_sheet),
            _SKULU_KEY: self.import_skulu(skulu_path, spec.skulu_sheet),
        }

    def run_pipeline(self, tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Run the topological transform pipeline over the imported frames.

        Mirrors ``mix_pipeline.main`` steps 1-8 (the source pivots, lookups,
        normalization, comparison, and the mix base) followed by
        :func:`run_transforms` (steps 9-19). Performs no I/O; every transform is
        a reused pure function.

        Args:
            tables: The imported frames keyed ``"LE"``, ``"aop"``, ``"sku_lu"``.

        Returns:
            A dict of every derived table, in evaluation order: the intermediate
            pivots/lookups (``le_wide``, ``aop_wide``, ``customer_lu``,
            ``aop_norm``, ``le_norm``, ``aop_vs_le``, ``mix_base``) merged with the
            rate-impact, rollup, detail, and Q1 tables from ``run_transforms``.

        Raises:
            KeyError: When a required import key is absent from ``tables``.
        """
        le_raw = tables[_LE_KEY]
        aop_raw = tables[_AOP_KEY]
        sku_lu = tables[_SKULU_KEY]

        # Steps 1-2: long-to-wide source pivots.
        le_wide = pivot_le(le_raw)
        aop_wide = pivot_aop(aop_raw)

        # Steps 3-8: lookups, normalization, comparison, and the mix base.
        customer_lu = build_customer_lu(aop_raw)
        aop_norm = build_aop_norm(aop_wide)
        le_norm = build_le_norm(le_wide)
        aop_vs_le = build_aop_vs_le(aop_norm, le_norm)
        mix_base = build_mix_base(aop_vs_le, sku_lu)

        # Steps 9-19: rate impacts, the rollup chain, the detail, and Q1.
        derived = run_transforms(aop_vs_le, sku_lu, mix_base, le_raw)

        # Assemble the full derived set in evaluation order; the intermediate
        # pivots/lookups are returned alongside the rollups, matching the CLI.
        return {
            "le_wide": le_wide,
            "aop_wide": aop_wide,
            "customer_lu": customer_lu,
            "aop_norm": aop_norm,
            "le_norm": le_norm,
            "aop_vs_le": aop_vs_le,
            "mix_base": mix_base,
            **derived,
        }

    def save_to_db(self, tables: dict[str, pd.DataFrame], db_path: str) -> None:
        """Persist every working table to a SQLite database.

        Delegates to the injected ``DbService`` so the SQLite write boundary is
        substitutable in tests.

        Args:
            tables: The working tables to persist (import frames and/or derived).
            db_path: Destination ``.db`` path.

        Returns:
            ``None``.

        Side effects:
            Writes the tables to ``db_path`` with replace semantics.
        """
        logger.info("Saving %d tables to %r.", len(tables), db_path)
        self._db_service.save_tables(tables, db_path)

    def open_db(self, db_path: str) -> dict[str, pd.DataFrame]:
        """Load the known tables from an existing SQLite database.

        Delegates to the injected ``DbService``.

        Args:
            db_path: Source ``.db`` path.

        Returns:
            The loaded tables keyed by table name.

        Side effects:
            Reads from ``db_path``.
        """
        logger.info("Opening database %r.", db_path)
        return self._db_service.open_tables(db_path)
