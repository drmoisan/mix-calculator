"""Unit tests for the GUI :class:`SchemaService` seam (Feature D, Phase 1).

These tests exercise the schema-coordination service against a registry backed
by an in-memory file store, so they run without real disk access, without a
network, and without a ``QApplication``. They verify that the service delegates
persistence to the injected registry, returns the registry best match for a set
of headers (positive and negative flows), builds a loader that applies the
schema, and that the composition-root factory resolves a registry from injected
``env``/``platform``/``home`` seams.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.gui.services.schema_service import (
    SchemaService,
    build_default_schema_service,
)
from src.schema_loader import SchemaLoader
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition
from src.schema_registry import SchemaRegistry

# Registry directory used by the in-memory-store-backed tests. The store is a
# dict keyed by POSIX path, so the directory only needs to be a stable prefix.
_REGISTRY_DIR = Path("/registry")


class InMemoryFileStore:
    """In-memory :class:`SchemaFileStore` fake backed by a dict.

    Purpose:
        Provide a deterministic, disk-free implementation of the registry's
        file-I/O boundary so :class:`SchemaService` can be unit-tested through a
        real :class:`~src.schema_registry.SchemaRegistry` without touching disk.

    Responsibilities:
        Store written text in a dict keyed by POSIX path and serve it back; list
        the filenames directly under a queried directory.

    Attributes:
        files: Mapping of POSIX path string to file text content.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory file store."""
        self.files: dict[str, str] = {}

    def list_files(self, directory: Path) -> list[str]:
        """Return filenames whose parent directory equals ``directory``.

        Args:
            directory: The directory to list.

        Returns:
            The filenames (not full paths) of stored files directly under
            ``directory``.
        """
        prefix = directory.as_posix().rstrip("/") + "/"
        # Return only entries directly under the queried directory; keys are full
        # paths, so strip the prefix and exclude anything in a sub-directory.
        return [
            stored_path[len(prefix) :]
            for stored_path in self.files
            if stored_path.startswith(prefix) and "/" not in stored_path[len(prefix) :]
        ]

    def read_text(self, path: Path) -> str:
        """Return the stored text for ``path``."""
        return self.files[path.as_posix()]

    def write_text(self, path: Path, text: str) -> None:
        """Store ``text`` for ``path`` in the in-memory dict."""
        self.files[path.as_posix()] = text

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` has been written to the store."""
        return path.as_posix() in self.files


def _aop_like_schema(name: str = "aop_like") -> SchemaDefinition:
    """Return a small valid schema with two required columns.

    Args:
        name: The schema name to use.

    Returns:
        A minimal valid :class:`SchemaDefinition` with a ``Customer`` dimension
        and a ``Sales`` measure, keyed on ``Customer``.
    """
    return SchemaDefinition(
        name=name,
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(columns=("Customer",)),
    )


def _registry_with_store() -> tuple[SchemaRegistry, InMemoryFileStore]:
    """Build a registry over a fresh in-memory store.

    Returns:
        A ``(registry, store)`` pair sharing the in-memory store so tests can
        assert on persisted files directly.
    """
    store = InMemoryFileStore()
    return SchemaRegistry(_REGISTRY_DIR, store), store


def test_list_schema_names_delegates_to_registry() -> None:
    """list_schema_names returns the registry's saved schema names."""
    # Arrange: a registry holding two saved schemas.
    registry, _store = _registry_with_store()
    registry.save(_aop_like_schema("alpha"))
    registry.save(_aop_like_schema("beta"))
    service = SchemaService(registry)

    # Act
    names = service.list_schema_names()

    # Assert: sorted names match what was saved.
    assert names == ["alpha", "beta"]


def test_load_schema_delegates_to_registry() -> None:
    """load_schema returns the schema previously saved under that name."""
    # Arrange
    registry, _store = _registry_with_store()
    registry.save(_aop_like_schema("alpha"))
    service = SchemaService(registry)

    # Act
    loaded = service.load_schema("alpha")

    # Assert: the round-tripped schema preserves identity and columns.
    assert loaded.name == "alpha"
    assert tuple(c.canonical_name for c in loaded.columns) == ("Customer", "Sales")


def test_save_schema_persists_through_registry() -> None:
    """save_schema writes the schema so the registry can list and load it."""
    # Arrange
    registry, store = _registry_with_store()
    service = SchemaService(registry)
    schema = _aop_like_schema("gamma")

    # Act
    service.save_schema(schema)

    # Assert: a file was written and the schema is now discoverable.
    assert any("gamma" in path for path in store.files)
    assert service.list_schema_names() == ["gamma"]


def test_find_best_match_returns_registry_best_match() -> None:
    """find_best_match selects the registry schema that covers the headers."""
    # Arrange: a registry with one schema and headers that match it exactly.
    registry, _store = _registry_with_store()
    registry.save(_aop_like_schema("aop_like"))
    service = SchemaService(registry)

    # Act
    result = service.find_best_match(["Customer", "Sales"])

    # Assert: full coverage selects the schema with no unmatched required columns.
    assert result.schema is not None
    assert result.schema.name == "aop_like"
    assert result.score == 1.0
    assert result.report.unmatched_required == ()


def test_find_best_match_reports_mismatch_for_unmatched_headers() -> None:
    """find_best_match yields a report naming an unmatched required column."""
    # Arrange: headers that omit the required ``Sales`` measure.
    registry, _store = _registry_with_store()
    registry.save(_aop_like_schema("aop_like"))
    service = SchemaService(registry)

    # Act
    result = service.find_best_match(["Customer"])

    # Assert: partial coverage still selects the schema but reports the gap.
    assert result.schema is not None
    assert result.score < 1.0
    unmatched = [c.canonical_name for c in result.report.unmatched_required]
    assert "Sales" in unmatched


def _keyable_schema(name: str = "keyable") -> SchemaDefinition:
    """Return a schema whose columns support the loader's KEY rebuild.

    The schema-driven loader rebuilds the business KEY from ``Customer``,
    ``SKU #``, and ``Type`` columns, so a schema exercised through ``load`` must
    declare them. The output emits these columns plus a numeric measure.

    Args:
        name: The schema name to use.

    Returns:
        A valid :class:`SchemaDefinition` whose canonical columns include the
        KEY components and a ``Sales`` measure, keyed on ``Customer``.
    """
    return SchemaDefinition(
        name=name,
        version="1.0",
        columns=(
            ColumnSpec(canonical_name="Customer", role="dimension"),
            ColumnSpec(canonical_name="SKU #", role="dimension"),
            ColumnSpec(canonical_name="Type", role="dimension"),
            ColumnSpec(canonical_name="Sales", role="measure", numeric=True),
        ),
        key=KeySpec(columns=("Customer", "SKU #", "Type")),
    )


def test_build_loader_returns_loader_that_applies_schema() -> None:
    """build_loader returns a SchemaLoader whose load applies the schema."""
    # Arrange: a registry-backed service and a raw frame for the schema columns.
    registry, _store = _registry_with_store()
    service = SchemaService(registry)
    schema = _keyable_schema("keyable")
    raw = pd.DataFrame(
        {
            "Customer": ["A", "B"],
            "SKU #": [1, 2],
            "Type": ["X", "Y"],
            "Sales": [10.0, 20.0],
        }
    )

    # Act
    loader = service.build_loader(schema)
    out = loader.load(raw)

    # Assert: a real loader is returned and it emits the schema's canonical
    # columns (the loader also appends the rebuilt KEY column).
    assert isinstance(loader, SchemaLoader)
    assert set(out.columns) >= {"Customer", "SKU #", "Type", "Sales"}
    assert out["Sales"].tolist() == [10.0, 20.0]


def test_build_default_schema_service_resolves_registry_from_seams() -> None:
    """build_default_schema_service builds a service from injected seams."""
    # Arrange: an explicit override directory via the documented env key.
    override_dir = "/data/schemas-under-test"  # noqa: S108 - test fixture path
    env = {"MIX_CALCULATOR_SCHEMA_DIR": override_dir}

    # Act: resolve through the factory using injected platform/home seams.
    service = build_default_schema_service(
        env=env, platform="linux", home=Path("/home/tester")
    )

    # Assert: the resolved registry directory honors the env override.
    assert isinstance(service, SchemaService)
    assert service.registry.registry_dir == Path(override_dir)
