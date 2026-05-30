"""Fake service implementations for the GUI presenter test suite.

Each fake implements one of the service Protocols, returns controlled data, and
can be configured to raise for negative-flow tests. The fakes let presenter
tests run without real Excel/SQLite I/O and without a ``QApplication``.

ARG002 suppressions are used only where a Protocol method legitimately ignores a
parameter in the fake, per the pre-authorized mock-signature pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.schema_loader import SchemaLoader

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pandas as pd

    from src.gui.pipeline_service import ImportSpec
    from src.schema_matching import MatchResult
    from src.schema_model import SchemaDefinition


class FakeWorkbookReader:
    """Fake :class:`WorkbookReaderProtocol` returning controlled tab/preview data.

    Attributes:
        sheet_names: The names ``get_sheet_names`` returns.
        preview_rows: The rows ``read_sheet_preview`` returns (before max_rows).
        raise_on_get: When set, ``get_sheet_names`` raises this error.
        raise_on_preview: When set, ``read_sheet_preview`` raises this error.
        preview_calls: Recorded ``(path, sheet_name, max_rows)`` preview calls.
    """

    def __init__(
        self,
        sheet_names: list[str] | None = None,
        preview_rows: list[list[str]] | None = None,
    ) -> None:
        """Initialize the fake with controlled return data.

        Args:
            sheet_names: The names ``get_sheet_names`` returns (default empty).
            preview_rows: The rows ``read_sheet_preview`` returns (default empty).
        """
        self.sheet_names: list[str] = list(sheet_names) if sheet_names else []
        self.preview_rows: list[list[str]] = (
            [list(row) for row in preview_rows] if preview_rows else []
        )
        self.raise_on_get: Exception | None = None
        self.raise_on_preview: Exception | None = None
        self.preview_calls: list[tuple[str, str, int]] = []

    def get_sheet_names(
        self, path: str
    ) -> list[str]:  # noqa: ARG002 - match WorkbookReaderProtocol API
        """Return the configured sheet names or raise the configured error.

        Args:
            path: Ignored by the fake (signature matches the Protocol).

        Returns:
            The configured sheet names.

        Raises:
            Exception: The configured ``raise_on_get`` error, when set.
        """
        if self.raise_on_get is not None:
            raise self.raise_on_get
        return list(self.sheet_names)

    def read_sheet_preview(
        self, path: str, sheet_name: str, max_rows: int = 200
    ) -> list[list[str]]:
        """Return the configured preview rows bounded by ``max_rows``.

        Args:
            path: The workbook path (recorded).
            sheet_name: The worksheet name (recorded).
            max_rows: The row cap (recorded and applied).

        Returns:
            The configured rows truncated to ``max_rows``.

        Raises:
            Exception: The configured ``raise_on_preview`` error, when set.
        """
        self.preview_calls.append((path, sheet_name, max_rows))
        if self.raise_on_preview is not None:
            raise self.raise_on_preview
        return [list(row) for row in self.preview_rows[:max_rows]]


class FakePipelineService:
    """Fake :class:`PipelineServiceProtocol` returning controlled frames.

    Attributes:
        import_result: The dict ``import_sources`` returns.
        run_result: The dict ``run_pipeline`` returns.
        open_result: The dict ``open_db`` returns.
        raise_on_run: When set, ``run_pipeline`` raises this error.
        raise_on_save: When set, ``save_to_db`` raises this error.
        raise_on_open: When set, ``open_db`` raises this error.
        saved: Recorded ``(tables, db_path)`` save calls.
        run_calls: Recorded ``run_pipeline`` table-key sets.
    """

    def __init__(
        self,
        import_result: dict[str, pd.DataFrame] | None = None,
        run_result: dict[str, pd.DataFrame] | None = None,
        open_result: dict[str, pd.DataFrame] | None = None,
    ) -> None:
        """Initialize the fake with controlled return data.

        Args:
            import_result: The dict ``import_sources`` returns.
            run_result: The dict ``run_pipeline`` returns.
            open_result: The dict ``open_db`` returns.
        """
        self.import_result: dict[str, pd.DataFrame] = import_result or {}
        self.run_result: dict[str, pd.DataFrame] = run_result or {}
        self.open_result: dict[str, pd.DataFrame] = open_result or {}
        self.raise_on_run: Exception | None = None
        self.raise_on_save: Exception | None = None
        self.raise_on_open: Exception | None = None
        self.raise_on_import: Exception | None = None
        self.saved: list[tuple[list[str], str]] = []
        self.run_calls: list[list[str]] = []
        self.import_calls: list[tuple[str, str, str]] = []

    def import_sources(
        self, spec: ImportSpec
    ) -> dict[str, pd.DataFrame]:  # noqa: ARG002 - match PipelineServiceProtocol API
        """Return the configured import frames or raise the configured error.

        Args:
            spec: Ignored by the fake (signature matches the Protocol).

        Returns:
            The configured import result.

        Raises:
            Exception: The configured ``raise_on_import`` error, when set.
        """
        if self.raise_on_import is not None:
            raise self.raise_on_import
        return dict(self.import_result)

    def import_le(
        self, path: str, sheet: str
    ) -> pd.DataFrame:  # noqa: ARG002 - match PipelineServiceProtocol API
        """Return the LE frame from the configured import result.

        Args:
            path: Ignored by the fake.
            sheet: Ignored by the fake.

        Returns:
            The ``"LE"`` frame from the import result.

        Raises:
            Exception: The configured ``raise_on_import`` error, when set.
        """
        if self.raise_on_import is not None:
            raise self.raise_on_import
        return self.import_result["LE"]

    def import_aop(
        self, path: str, sheet: str
    ) -> pd.DataFrame:  # noqa: ARG002 - match PipelineServiceProtocol API
        """Return the AOP frame from the configured import result.

        Args:
            path: Ignored by the fake.
            sheet: Ignored by the fake.

        Returns:
            The ``"aop"`` frame from the import result.
        """
        return self.import_result["aop"]

    def import_skulu(self, path: str, sheet: str) -> pd.DataFrame:
        """Return the SKU_LU frame, recording the resolved path and sheet.

        Args:
            path: The SKU_LU workbook path (recorded so the default can be
                asserted).
            sheet: The SKU_LU worksheet name (recorded).

        Returns:
            The ``"sku_lu"`` frame from the import result.
        """
        self.import_calls.append(("sku_lu", path, sheet))
        return self.import_result["sku_lu"]

    def import_with_schema(
        self, raw: pd.DataFrame, schema: SchemaDefinition
    ) -> pd.DataFrame:
        """Import a raw frame through a real schema-driven loader.

        Args:
            raw: The raw source frame.
            schema: The schema whose loader transforms ``raw``.

        Returns:
            The schema's canonical output frame from a real
            :class:`~src.schema_loader.SchemaLoader`.
        """
        return SchemaLoader(schema).load(raw)

    def run_pipeline(self, tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        """Return the configured run result or raise the configured error.

        Args:
            tables: The imported tables (the key set is recorded).

        Returns:
            The configured run result.

        Raises:
            Exception: The configured ``raise_on_run`` error, when set.
        """
        self.run_calls.append(list(tables))
        if self.raise_on_run is not None:
            raise self.raise_on_run
        return dict(self.run_result)

    def save_to_db(self, tables: dict[str, pd.DataFrame], db_path: str) -> None:
        """Record a save call or raise the configured error.

        Args:
            tables: The tables to persist (key set recorded).
            db_path: The destination path (recorded).

        Returns:
            ``None``.

        Raises:
            Exception: The configured ``raise_on_save`` error, when set.
        """
        if self.raise_on_save is not None:
            raise self.raise_on_save
        self.saved.append((list(tables), db_path))

    def open_db(
        self, db_path: str
    ) -> dict[str, pd.DataFrame]:  # noqa: ARG002 - match PipelineServiceProtocol API
        """Return the configured open result or raise the configured error.

        Args:
            db_path: Ignored by the fake (signature matches the Protocol).

        Returns:
            The configured open result.

        Raises:
            Exception: The configured ``raise_on_open`` error, when set.
        """
        if self.raise_on_open is not None:
            raise self.raise_on_open
        return dict(self.open_result)


class FakeDbService:
    """Fake DB service recording saves and returning controlled open data.

    Attributes:
        open_result: The dict ``open_tables`` returns.
        saved: Recorded ``(table_keys, db_path)`` save calls.
    """

    def __init__(self, open_result: dict[str, pd.DataFrame] | None = None) -> None:
        """Initialize the fake with controlled open data.

        Args:
            open_result: The dict ``open_tables`` returns (default empty).
        """
        self.open_result: dict[str, pd.DataFrame] = open_result or {}
        self.saved: list[tuple[list[str], str]] = []

    def save_tables(self, tables: dict[str, pd.DataFrame], db_path: str) -> None:
        """Record a save call.

        Args:
            tables: The tables to persist (key set recorded).
            db_path: The destination path (recorded).

        Returns:
            ``None``.
        """
        self.saved.append((list(tables), db_path))

    def open_tables(
        self, db_path: str
    ) -> dict[str, pd.DataFrame]:  # noqa: ARG002 - match DbService API
        """Return the configured open result.

        Args:
            db_path: Ignored by the fake.

        Returns:
            The configured open result.
        """
        return dict(self.open_result)


class FakeSchemaService:
    """Fake :class:`SchemaServiceProtocol` returning controlled schema data.

    Purpose:
        Let presenter and wiring tests exercise the schema-coordination seam with
        controlled return data and recorded calls, without real disk access or a
        ``QApplication``.

    Responsibilities:
        Return configured schema names and a configured
        :class:`~src.schema_matching.MatchResult`, look up stored schemas by name,
        record every ``save_schema`` call, and build a real
        :class:`~src.schema_loader.SchemaLoader` for the requested schema.

    Attributes:
        schema_names: The names ``list_schema_names`` returns.
        schemas: Mapping of name to schema served by ``load_schema``.
        match_result: The :class:`MatchResult` ``find_best_match`` returns.
        saved: Recorded schemas passed to ``save_schema``, in call order.
        match_calls: Recorded header sequences passed to ``find_best_match``.
    """

    def __init__(
        self,
        schema_names: list[str] | None = None,
        schemas: dict[str, SchemaDefinition] | None = None,
        match_result: MatchResult | None = None,
    ) -> None:
        """Initialize the fake with controlled schema data.

        Args:
            schema_names: The names ``list_schema_names`` returns (default empty).
            schemas: Mapping of name to schema served by ``load_schema`` (default
                empty).
            match_result: The result ``find_best_match`` returns. When ``None``,
                ``find_best_match`` raises if called, so tests that exercise
                matching must supply one.
        """
        self.schema_names: list[str] = list(schema_names) if schema_names else []
        self.schemas: dict[str, SchemaDefinition] = dict(schemas) if schemas else {}
        self.match_result: MatchResult | None = match_result
        self.saved: list[SchemaDefinition] = []
        self.match_calls: list[list[str]] = []

    def list_schema_names(self) -> list[str]:
        """Return the configured schema names.

        Returns:
            The configured schema names.
        """
        return list(self.schema_names)

    def load_schema(self, name: str) -> SchemaDefinition:
        """Return the stored schema for ``name``.

        Args:
            name: The schema name to look up.

        Returns:
            The configured schema registered under ``name``.

        Raises:
            KeyError: If no schema was configured for ``name``.
        """
        return self.schemas[name]

    def save_schema(self, schema: SchemaDefinition) -> None:
        """Record a ``save_schema`` call.

        Args:
            schema: The schema being persisted (recorded).

        Returns:
            ``None``.
        """
        self.saved.append(schema)

    def find_best_match(self, headers: Sequence[str]) -> MatchResult:
        """Return the configured match result, recording the headers.

        Args:
            headers: The source headers (recorded).

        Returns:
            The configured :class:`MatchResult`.

        Raises:
            AssertionError: If no ``match_result`` was configured.
        """
        self.match_calls.append(list(headers))
        assert self.match_result is not None, "FakeSchemaService.match_result not set"
        return self.match_result

    def build_loader(self, schema: SchemaDefinition) -> SchemaLoader:
        """Return a real :class:`SchemaLoader` for ``schema``.

        Args:
            schema: The schema the returned loader applies.

        Returns:
            A real :class:`~src.schema_loader.SchemaLoader` over ``schema`` so the
            preview path exercises genuine load behavior.
        """
        return SchemaLoader(schema)
