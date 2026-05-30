"""Unit tests for the registry-integrated match entry point (AC4).

These tests exercise :func:`src.schema_matching.find_best_match_in_registry`
through a :class:`src.schema_registry.SchemaRegistry` backed by an in-memory
``SchemaFileStore`` fake. No real disk, network, or temp files are used: schemas
are persisted into a dict-backed store and matched back out.
"""

from __future__ import annotations

from pathlib import Path

from src.schema_matching import find_best_match_in_registry
from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition
from src.schema_registry import SchemaRegistry


class InMemoryFileStore:
    """In-memory ``SchemaFileStore`` fake backed by a dict.

    Purpose:
        Provide a deterministic, disk-free implementation of the registry's
        file-I/O boundary so the registry-integrated match can be tested without
        touching the real filesystem. Files are keyed by their POSIX path string.

    Responsibilities:
        - Store written text in a dict and serve it back on read.
        - List the filenames whose parent directory matches a queried directory.

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
        # Return only entries directly under the queried directory; the stored
        # key is the full path, so strip the prefix to recover the filename.
        return [
            stored_path[len(prefix) :]
            for stored_path in self.files
            if stored_path.startswith(prefix) and "/" not in stored_path[len(prefix) :]
        ]

    def read_text(self, path: Path) -> str:
        """Return the stored text for ``path``.

        Args:
            path: The file path to read.

        Returns:
            The stored text content.

        Raises:
            KeyError: If the path was never written (callers guard with exists).
        """
        return self.files[path.as_posix()]

    def write_text(self, path: Path, text: str) -> None:
        """Store ``text`` for ``path`` in the in-memory dict."""
        self.files[path.as_posix()] = text

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` has been written to the store."""
        return path.as_posix() in self.files


def _schema(name: str, columns: tuple[ColumnSpec, ...]) -> SchemaDefinition:
    """Build a valid schema whose key references its first column.

    Args:
        name: The schema identity name (also its persisted filename stem).
        columns: The column specs in declaration order.

    Returns:
        A constructed :class:`SchemaDefinition` satisfying model invariants.
    """
    return SchemaDefinition(
        name=name,
        version="1",
        columns=columns,
        key=KeySpec(columns=(columns[0].canonical_name,)),
    )


def test_find_best_match_in_registry_selects_best_loaded_candidate() -> None:
    """The best-covering registry-loaded schema is selected."""
    # Arrange: seed the registry with a fully-covered and a partially-covered
    # schema, persisted through the in-memory store.
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store)
    full = _schema(
        "full",
        (
            ColumnSpec(canonical_name="sku", role="dimension"),
            ColumnSpec(canonical_name="region", role="dimension"),
        ),
    )
    partial = _schema(
        "partial",
        (
            ColumnSpec(canonical_name="sku", role="dimension"),
            ColumnSpec(canonical_name="region", role="dimension"),
            ColumnSpec(canonical_name="net sales", role="measure"),
        ),
    )
    registry.save(full)
    registry.save(partial)
    headers = ["SKU", "Region"]

    # Act
    result = find_best_match_in_registry(headers, registry)

    # Assert: the fully-covered schema is selected and scores 1.0. Schema identity
    # is compared by value because load() reconstructs a fresh object.
    assert result.schema == full
    assert result.score == 1.0


def test_find_best_match_in_registry_empty_registry_returns_none() -> None:
    """An empty registry yields schema=None and score 0.0."""
    # Arrange: a registry whose store holds no schema files.
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store)

    # Act
    result = find_best_match_in_registry(["SKU"], registry)

    # Assert
    assert result.schema is None
    assert result.score == 0.0
    assert result.report.unmatched_required == ()
