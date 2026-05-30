"""Unit tests for :mod:`src.schema_registry`.

Exercises ``SchemaRegistry`` against an in-memory file-store fake backed by an
in-process dict, so no real files, temp files, or network access occur. Covers
save/load round-trips, listing, the missing-name error, and bundled-default
loading served by the fake. Each test follows Arrange-Act-Assert.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from src.schema_model import ColumnSpec, KeySpec, SchemaDefinition
from src.schema_registry import (
    SCHEMA_SUFFIX,
    DiskSchemaFileStore,
    SchemaRegistry,
    SchemaRegistryError,
)
from src.schema_serialization import schema_to_json

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest as _pytest


class InMemoryFileStore:
    """In-memory :class:`SchemaFileStore` fake backed by a dict.

    Purpose:
        Provide a deterministic, disk-free implementation of the registry's
        file-I/O boundary for unit tests. Files are keyed by their POSIX path
        string so directory listing can match on path prefixes.

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
        # Return only entries that live directly under the queried directory;
        # the stored key is the full path, so strip the prefix to get the name.
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
            KeyError: If the path was never written (tests guard with ``exists``).
        """
        return self.files[path.as_posix()]

    def write_text(self, path: Path, text: str) -> None:
        """Store ``text`` for ``path`` in the in-memory dict."""
        self.files[path.as_posix()] = text

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` has been written to the store."""
        return path.as_posix() in self.files


def _sample_schema(name: str = "sample") -> SchemaDefinition:
    """Return a small valid schema for registry round-trip tests.

    Args:
        name: The schema name to use.

    Returns:
        A minimal valid ``SchemaDefinition``.
    """
    return SchemaDefinition(
        name=name,
        version="1.0",
        columns=(ColumnSpec(canonical_name="Customer", role="dimension"),),
        key=KeySpec(columns=("Customer",)),
    )


def test_save_then_load_round_trips() -> None:
    """A saved schema loads back equal to the original."""
    # Arrange
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store)
    schema = _sample_schema()

    # Act
    registry.save(schema)
    loaded = registry.load("sample")

    # Assert
    assert loaded == schema


def test_list_schemas_returns_saved_names() -> None:
    """list_schemas returns the names of saved schemas in sorted order."""
    # Arrange
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store)
    registry.save(_sample_schema("beta"))
    registry.save(_sample_schema("alpha"))

    # Act
    names = registry.list_schemas()

    # Assert
    assert names == ["alpha", "beta"]


def test_load_missing_schema_raises_descriptive_error() -> None:
    """Loading an unknown schema name raises a registry error naming it."""
    # Arrange
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store)

    # Act / Assert
    with pytest.raises(SchemaRegistryError, match="schema 'ghost' not found"):
        registry.load("ghost")


def test_load_bundled_default_reads_from_bundled_dir() -> None:
    """load_bundled_default reads a fixture served by the fake store."""
    # Arrange: seed the fake at the bundled path the registry will query.
    store = InMemoryFileStore()
    bundled_dir = Path("/bundled")
    registry = SchemaRegistry(Path("/reg"), store, bundled_dir=bundled_dir)
    fixture = _sample_schema("default_aop")
    store.write_text(
        bundled_dir / f"default_aop{SCHEMA_SUFFIX}", schema_to_json(fixture)
    )

    # Act
    loaded = registry.load_bundled_default("default_aop")

    # Assert
    assert loaded == fixture


def test_load_bundled_default_missing_raises() -> None:
    """A missing bundled default raises a descriptive registry error."""
    # Arrange
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store, bundled_dir=Path("/bundled"))

    # Act / Assert
    with pytest.raises(SchemaRegistryError, match="bundled default schema 'nope'"):
        registry.load_bundled_default("nope")


def test_list_schemas_ignores_non_schema_files() -> None:
    """Files without the schema suffix are not reported as schemas."""
    # Arrange
    store = InMemoryFileStore()
    registry = SchemaRegistry(Path("/reg"), store)
    registry.save(_sample_schema("real"))
    store.write_text(Path("/reg/readme.txt"), "not a schema")

    # Act
    names = registry.list_schemas()

    # Assert
    assert names == ["real"]


# --- DiskSchemaFileStore (real-disk implementation, exercised via a typed seam) ---
#
# These tests cover the production file store without touching the real
# filesystem. ``DiskSchemaFileStore`` only calls a small set of ``Path`` methods,
# so each test substitutes those methods with typed module-level replacements via
# ``monkeypatch.setattr``. No temp files or real I/O are created.


def _patch_path(
    monkeypatch: _pytest.MonkeyPatch, name: str, replacement: object
) -> None:
    """Replace ``Path.<name>`` with a typed callable for the test's duration.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        name: The ``Path`` method name to replace.
        replacement: The typed callable to install in its place.
    """
    monkeypatch.setattr(Path, name, replacement)


def test_disk_store_list_files_returns_empty_for_missing_dir(
    monkeypatch: _pytest.MonkeyPatch,
) -> None:
    """list_files returns an empty list when the directory does not exist."""

    # Arrange: a directory that reports it is not a directory.
    def fake_is_dir(_self: Path) -> bool:
        return False

    _patch_path(monkeypatch, "is_dir", fake_is_dir)
    store = DiskSchemaFileStore()

    # Act
    result = store.list_files(Path("/nope"))

    # Assert
    assert result == []


def test_disk_store_list_files_returns_file_names(
    monkeypatch: _pytest.MonkeyPatch,
) -> None:
    """list_files returns the names of regular files in the directory."""
    # Arrange: a directory with one file entry and one sub-directory entry.
    file_entry = Path("/dir/a.schema.json")
    dir_entry = Path("/dir/sub")

    def fake_is_dir(self: Path) -> bool:
        return self in {Path("/dir"), dir_entry}

    def fake_iterdir(_self: Path) -> Iterator[Path]:
        return iter([file_entry, dir_entry])

    def fake_is_file(self: Path) -> bool:
        return self == file_entry

    _patch_path(monkeypatch, "is_dir", fake_is_dir)
    _patch_path(monkeypatch, "iterdir", fake_iterdir)
    _patch_path(monkeypatch, "is_file", fake_is_file)
    store = DiskSchemaFileStore()

    # Act
    result = store.list_files(Path("/dir"))

    # Assert
    assert result == ["a.schema.json"]


def test_disk_store_read_text_delegates_to_path(
    monkeypatch: _pytest.MonkeyPatch,
) -> None:
    """read_text returns the text produced by Path.read_text."""

    # Arrange: the store calls read_text(encoding="utf-8"), so the replacement
    # must accept the keyword argument by name. The captured encoding is asserted
    # so the parameter is used and the call contract is verified.
    captured: dict[str, str] = {}

    def fake_read_text(_self: Path, encoding: str) -> str:
        captured["encoding"] = encoding
        return "content"

    _patch_path(monkeypatch, "read_text", fake_read_text)
    store = DiskSchemaFileStore()

    # Act
    result = store.read_text(Path("/dir/a.json"))

    # Assert
    assert result == "content"
    assert captured["encoding"] == "utf-8"


def test_disk_store_write_text_creates_parent_and_writes(
    monkeypatch: _pytest.MonkeyPatch,
) -> None:
    """write_text creates the parent directory and writes the text."""
    # Arrange: record the mkdir and write_text calls instead of touching disk.
    calls: dict[str, tuple[object, object]] = {}

    def fake_mkdir(_self: Path, parents: bool, exist_ok: bool) -> None:
        calls["mkdir"] = (parents, exist_ok)

    def fake_write_text(_self: Path, text: str, encoding: str) -> None:
        calls["write"] = (text, encoding)

    _patch_path(monkeypatch, "mkdir", fake_mkdir)
    _patch_path(monkeypatch, "write_text", fake_write_text)
    store = DiskSchemaFileStore()

    # Act
    store.write_text(Path("/dir/a.json"), "payload")

    # Assert
    assert calls["mkdir"] == (True, True)
    assert calls["write"] == ("payload", "utf-8")


def test_disk_store_exists_delegates_to_path(
    monkeypatch: _pytest.MonkeyPatch,
) -> None:
    """exists returns the boolean produced by Path.exists."""

    # Arrange
    def fake_exists(_self: Path) -> bool:
        return True

    _patch_path(monkeypatch, "exists", fake_exists)
    store = DiskSchemaFileStore()

    # Act / Assert
    assert store.exists(Path("/dir/a.json")) is True
