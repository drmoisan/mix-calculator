"""Schema service seam for the GUI presenters and import-flow wiring (Feature D).

This module provides the GUI's schema-coordination boundary. It wraps the
Feature A/B/C public surface (registry persistence, header-to-schema matching,
and the schema-driven loader) behind one injectable interface so the presenters
and the composition root depend on a small, Qt-free seam rather than on the
individual schema modules.

Responsibilities:
    - ``SchemaServiceProtocol``: the Qt-free call surface presenters and wiring
      depend on (list/load/save schemas, find the best header match, build a
      loader).
    - ``SchemaService``: the production implementation that delegates to the
      injected :class:`~src.schema_registry.SchemaRegistry`,
      :func:`~src.schema_matching.find_best_match_in_registry`, and
      :class:`~src.schema_loader.SchemaLoader`.
    - ``build_default_schema_service``: a composition-root factory that resolves
      the registry directory from injected ``env``/``platform``/``home`` seams
      and constructs a disk-backed service in one call.

Scope boundaries:
    - No Qt import, no direct disk access, and no transform logic. All
      persistence flows through the injected registry; all matching and loading
      flow through the Feature B/C public functions/classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from src.schema_loader import SchemaLoader
from src.schema_matching import find_best_match_in_registry
from src.schema_registry import DiskSchemaFileStore, SchemaRegistry
from src.schema_settings import resolve_registry_dir

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from src.schema_formula import FormulaEvaluator
    from src.schema_matching import MatchResult
    from src.schema_model import SchemaDefinition

__all__ = [
    "SchemaService",
    "SchemaServiceProtocol",
    "build_default_schema_service",
]


@runtime_checkable
class SchemaServiceProtocol(Protocol):
    """Qt-free schema-coordination surface for presenters and import wiring.

    Purpose:
        Define the minimal call surface the schema-builder and column-matching
        presenters and the composition root depend on, so those collaborators
        are testable with a plain-Python fake and never import Qt or the
        individual schema modules directly.

    Responsibilities:
        Enumerate, load, and persist schemas; find the best schema match for a
        set of source headers; and build a schema-driven loader. It performs no
        Qt work and no transform logic itself; implementations delegate to the
        Feature A/B/C surface.

    Usage:
        Construct the production :class:`SchemaService` at the composition root
        (via :func:`build_default_schema_service`) and inject it into the
        presenters. Tests inject a fake implementing this Protocol.
    """

    def list_schema_names(self) -> list[str]:
        """Return the names of the schemas available in the registry."""
        ...

    def load_schema(self, name: str) -> SchemaDefinition:
        """Load and return the named schema from the registry."""
        ...

    def save_schema(self, schema: SchemaDefinition) -> None:
        """Persist ``schema`` to the registry."""
        ...

    def find_best_match(self, headers: Sequence[str]) -> MatchResult:
        """Return the best schema match for the given source ``headers``."""
        ...

    def build_loader(self, schema: SchemaDefinition) -> SchemaLoader:
        """Build a schema-driven loader for ``schema``."""
        ...


class SchemaService:
    """Production schema service over the Feature A/B/C public surface.

    Purpose:
        Coordinate schema persistence, header matching, and loader construction
        for the GUI behind the Qt-free :class:`SchemaServiceProtocol`, delegating
        to the injected registry and the Feature B/C functions/classes.

    Responsibilities:
        Wrap :meth:`~src.schema_registry.SchemaRegistry.list_schemas`/``load``/
        ``save``, :func:`~src.schema_matching.find_best_match_in_registry`, and
        :class:`~src.schema_loader.SchemaLoader` construction. It performs no Qt
        work, no direct disk access, and no transform logic; persistence flows
        only through the injected registry.

    Usage:
        Construct with an injected :class:`~src.schema_registry.SchemaRegistry`
        and an optional :class:`~src.schema_formula.FormulaEvaluator`. The
        composition root uses :func:`build_default_schema_service`; tests inject
        a registry backed by an in-memory file store.

    Attributes:
        registry: The injected registry that owns all schema persistence.
        formula_evaluator: The evaluator passed to each built
            :class:`SchemaLoader`; ``None`` lets the loader create its own
            default evaluator.
    """

    def __init__(
        self,
        registry: SchemaRegistry,
        *,
        formula_evaluator: FormulaEvaluator | None = None,
    ) -> None:
        """Initialize the service with a registry and optional evaluator.

        Args:
            registry: The Feature A registry used for all schema persistence.
            formula_evaluator: An optional shared evaluator passed to each loader
                built by :meth:`build_loader`. When ``None``, each loader creates
                its own default :class:`~src.schema_formula.FormulaEvaluator`.
        """
        self.registry = registry
        self.formula_evaluator = formula_evaluator

    def list_schema_names(self) -> list[str]:
        """Return the names of the schemas saved in the registry.

        Returns:
            The schema names in the registry's sorted order.

        Side effects:
            Lists the registry directory via the registry's injected store.
        """
        return self.registry.list_schemas()

    def load_schema(self, name: str) -> SchemaDefinition:
        """Load and return the named schema from the registry.

        Args:
            name: The schema name (without the registry file suffix).

        Returns:
            The parsed :class:`~src.schema_model.SchemaDefinition`.

        Raises:
            SchemaRegistryError: If no schema is saved under ``name`` (propagated
                from the registry).

        Side effects:
            Reads the schema file via the registry's injected store.
        """
        return self.registry.load(name)

    def save_schema(self, schema: SchemaDefinition) -> None:
        """Persist ``schema`` to the registry.

        Args:
            schema: The schema to persist. The registry derives the file name
                from ``schema.name``.

        Returns:
            ``None``.

        Side effects:
            Writes the serialized schema via the registry's injected store.
        """
        self.registry.save(schema)

    def find_best_match(self, headers: Sequence[str]) -> MatchResult:
        """Return the best schema match for the given source ``headers``.

        Args:
            headers: The actual source headers, in source order.

        Returns:
            A :class:`~src.schema_matching.MatchResult` naming the highest-scoring
            registry schema, its coverage score, and the mismatch report. When the
            registry holds no schemas the result's ``schema`` is ``None``.

        Side effects:
            Loads every registry schema via the registry's injected store to score
            the candidates.
        """
        return find_best_match_in_registry(headers, self.registry)

    def build_loader(self, schema: SchemaDefinition) -> SchemaLoader:
        """Build a schema-driven loader for ``schema``.

        Args:
            schema: The schema the returned loader applies by default.

        Returns:
            A :class:`~src.schema_loader.SchemaLoader` constructed with ``schema``
            and this service's shared formula evaluator (or the loader's own
            default evaluator when none was injected).
        """
        return SchemaLoader(schema, formula_evaluator=self.formula_evaluator)


def build_default_schema_service(
    *,
    env: Mapping[str, str],
    platform: str,
    home: Path,
) -> SchemaService:
    """Build a disk-backed :class:`SchemaService` for the composition root.

    Resolves the shared registry directory from the injected seams (matching the
    Feature A resolver) and constructs a registry over a real-disk file store, so
    the composition root has a single call and tests can instead inject an
    in-memory-store-backed registry directly into :class:`SchemaService`.

    Args:
        env: The environment mapping used to resolve the registry directory
            (injected; not read from the process environment).
        platform: The platform marker (for example ``sys.platform``) used to
            select the per-user default directory convention.
        home: The user's home directory used for the default-directory fallback.

    Returns:
        A :class:`SchemaService` over a :class:`~src.schema_registry.SchemaRegistry`
        rooted at the resolved registry directory and backed by a
        :class:`~src.schema_registry.DiskSchemaFileStore`.

    Side effects:
        None at construction time; the returned service performs disk I/O only
        when its methods are called.
    """
    registry_dir = resolve_registry_dir(env=env, platform=platform, home=home)
    registry = SchemaRegistry(registry_dir, DiskSchemaFileStore())
    return SchemaService(registry)
