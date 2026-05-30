"""Shared schema registry: list, load, save, and bundled-default loading.

This module persists :class:`SchemaDefinition` objects as ``*.schema.json`` files
in a resolved registry directory, and loads the package's bundled default
schemas from ``src/schemas/``. All file access flows through an injectable
:class:`SchemaFileStore` ``Protocol`` so the registry's logic is unit-testable
with an in-memory fake and never touches the real filesystem in tests.

Responsibilities:
    - ``SchemaFileStore``: the minimal file-I/O boundary (list/read/write/exists).
    - ``DiskSchemaFileStore``: the default real-disk implementation, kept isolated
      from the pure registry logic.
    - ``SchemaRegistry``: list/load/save schemas in a directory plus
      ``load_bundled_default`` from the packaged ``src/schemas/`` directory.

Scope boundaries:
    - JSON parsing/serialization is delegated to :mod:`src.schema_serialization`.
    - The registry never calls ``open``/``pathlib`` I/O directly; every read and
      write goes through the injected store.
    - Standard library only (``pathlib``, ``typing``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from src.schema_serialization import schema_from_json, schema_to_json

if TYPE_CHECKING:
    from src.schema_model import SchemaDefinition

# Filename suffix for persisted schema files. A schema named "foo" persists as
# "foo.schema.json"; listing strips this suffix to recover the schema name.
SCHEMA_SUFFIX = ".schema.json"

# Packaged directory holding the bundled default schemas, resolved relative to
# this module so it works regardless of the process working directory.
_BUNDLED_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


class SchemaRegistryError(Exception):
    """Raised when a registry operation cannot be completed.

    Purpose:
        Signal a registry-level failure such as loading a schema name that does
        not exist in the registry directory, with a descriptive message naming
        the missing schema. Serialization/validation failures surface as their
        own exception types from :mod:`src.schema_serialization` and
        :mod:`src.schema_model`.
    """


class SchemaFileStore(Protocol):
    """Minimal file-I/O boundary used by :class:`SchemaRegistry`.

    Purpose:
        Abstract the file operations the registry needs so the registry's logic
        can be exercised against an in-memory fake without real disk access.

    Responsibilities:
        - ``list_files``: list filenames (not full paths) within a directory.
        - ``read_text``: read a file's full text.
        - ``write_text``: write a file's full text (creating or replacing it).
        - ``exists``: report whether a path exists.

    Usage:
        The registry receives an implementation via constructor injection. The
        default real-disk implementation is :class:`DiskSchemaFileStore`; tests
        supply an in-memory dict-backed fake.
    """

    def list_files(self, directory: Path) -> list[str]:
        """Return the filenames directly within ``directory``."""
        ...

    def read_text(self, path: Path) -> str:
        """Return the full text content of the file at ``path``."""
        ...

    def write_text(self, path: Path, text: str) -> None:
        """Write ``text`` to ``path``, creating or replacing the file."""
        ...

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists."""
        ...


class DiskSchemaFileStore:
    """Default real-disk implementation of :class:`SchemaFileStore`.

    Purpose:
        Provide the production file-I/O behavior for the registry by delegating
        to ``pathlib``. This class is the single isolated place where real disk
        access occurs; the registry logic never touches the filesystem directly.

    Responsibilities:
        - List files in a directory, read/write UTF-8 text, and test existence.

    Side effects:
        Reads from and writes to the real filesystem. ``write_text`` creates the
        parent directory if it does not yet exist.
    """

    def list_files(self, directory: Path) -> list[str]:
        """Return the filenames directly within ``directory``.

        Args:
            directory: The directory to list.

        Returns:
            The names (not full paths) of the entries that are files. Returns an
            empty list when the directory does not exist.

        Side effects:
            Reads directory entries from the filesystem.
        """
        # A missing directory is treated as empty so a first-run registry with no
        # saved schemas lists nothing rather than raising.
        if not directory.is_dir():
            return []
        # Collect only regular files; sub-directories are not schema files.
        return [entry.name for entry in directory.iterdir() if entry.is_file()]

    def read_text(self, path: Path) -> str:
        """Read and return the UTF-8 text content of ``path``.

        Args:
            path: The file to read.

        Returns:
            The file's full text.

        Side effects:
            Reads from the filesystem.
        """
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, text: str) -> None:
        """Write ``text`` to ``path`` as UTF-8, creating parents as needed.

        Args:
            path: The destination file path.
            text: The text content to write.

        Side effects:
            Creates the parent directory if absent and writes to the filesystem.
        """
        # Ensure the registry directory exists before the first save so callers
        # do not need to pre-create it.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists on the filesystem."""
        return path.exists()


class SchemaRegistry:
    """List, load, and save schema definitions in a shared registry directory.

    Purpose:
        Coordinate persistence of :class:`SchemaDefinition` objects as JSON files
        in a resolved registry directory, and load the package's bundled default
        schemas. JSON parsing/serialization is delegated to
        :mod:`src.schema_serialization`.

    Usage:
        Construct with the resolved registry directory (see
        :func:`src.schema_settings.resolve_registry_dir`) and a
        :class:`SchemaFileStore` implementation. In production pass a
        :class:`DiskSchemaFileStore`; in tests pass an in-memory fake.

    High-level flow:
        - ``list_schemas`` lists ``*.schema.json`` files and strips the suffix.
        - ``load`` reads a named file and parses it.
        - ``save`` serializes a schema and writes ``<name>.schema.json``.
        - ``load_bundled_default`` reads from the packaged ``src/schemas/`` dir
          through the same injected store.

    Key invariants:
        - All file access flows through the injected ``store``; the registry
          never opens files directly.

    Attributes:
        registry_dir: The directory holding user-saved schema files.
        store: The injected file-I/O boundary.
        bundled_dir: The packaged directory holding bundled default schemas.
    """

    def __init__(
        self,
        registry_dir: Path,
        store: SchemaFileStore,
        *,
        bundled_dir: Path = _BUNDLED_SCHEMAS_DIR,
    ) -> None:
        """Initialize the registry with its directory and file store.

        Args:
            registry_dir: The directory holding user-saved schema files.
            store: The :class:`SchemaFileStore` used for all file access.
            bundled_dir: The packaged bundled-defaults directory. Defaults to the
                ``src/schemas/`` directory beside this module; injectable so tests
                can serve bundled fixtures through the same store.
        """
        self.registry_dir = registry_dir
        self.store = store
        self.bundled_dir = bundled_dir

    def list_schemas(self) -> list[str]:
        """Return the names of schemas saved in the registry directory.

        Returns:
            The schema names (filename with the :data:`SCHEMA_SUFFIX` stripped)
            for every ``*.schema.json`` file in the registry directory, sorted
            for a deterministic order.

        Side effects:
            Lists the registry directory via the injected store.
        """
        # Recover each schema name by stripping the suffix; non-schema files in
        # the directory are ignored so unrelated files do not appear as schemas.
        names = [
            filename[: -len(SCHEMA_SUFFIX)]
            for filename in self.store.list_files(self.registry_dir)
            if filename.endswith(SCHEMA_SUFFIX)
        ]
        return sorted(names)

    def load(self, name: str) -> SchemaDefinition:
        """Load and parse a named schema from the registry directory.

        Args:
            name: The schema name (without the ``.schema.json`` suffix).

        Returns:
            The parsed ``SchemaDefinition``.

        Raises:
            SchemaRegistryError: If no file exists for ``name`` in the registry.
            SchemaSerializationError: If the file contents are not valid schema
                JSON (propagated from :mod:`src.schema_serialization`).

        Side effects:
            Reads the schema file via the injected store.
        """
        path = self._path_for(self.registry_dir, name)
        if not self.store.exists(path):
            raise SchemaRegistryError(
                f"schema '{name}' not found in registry '{self.registry_dir}'"
            )
        return schema_from_json(self.store.read_text(path))

    def save(self, schema: SchemaDefinition) -> None:
        """Serialize and persist a schema to the registry directory.

        Args:
            schema: The schema to persist. The file is named
                ``<schema.name>.schema.json``.

        Side effects:
            Writes the serialized schema via the injected store.
        """
        path = self._path_for(self.registry_dir, schema.name)
        self.store.write_text(path, schema_to_json(schema))

    def load_bundled_default(self, name: str) -> SchemaDefinition:
        """Load a bundled default schema from the packaged schemas directory.

        Args:
            name: The bundled schema name (without the ``.schema.json`` suffix),
                for example ``"default_aop"`` or ``"default_le"``.

        Returns:
            The parsed ``SchemaDefinition``.

        Raises:
            SchemaRegistryError: If no bundled file exists for ``name``.
            SchemaSerializationError: If the bundled file is not valid schema JSON.

        Side effects:
            Reads the bundled schema file via the injected store.
        """
        path = self._path_for(self.bundled_dir, name)
        if not self.store.exists(path):
            raise SchemaRegistryError(
                f"bundled default schema '{name}' not found in '{self.bundled_dir}'"
            )
        return schema_from_json(self.store.read_text(path))

    def _path_for(self, directory: Path, name: str) -> Path:
        """Return the file path for schema ``name`` within ``directory``.

        Args:
            directory: The directory the schema file lives in.
            name: The schema name without the suffix.

        Returns:
            ``<directory>/<name>.schema.json``.
        """
        return directory / f"{name}{SCHEMA_SUFFIX}"
