"""Shared fixtures for the SchemaLoader core and seam test modules (issue #58).

Holds the monthly-vector constants and the bundled-default loader helper used by
both ``tests.test_schema_loader_core`` and ``tests.test_schema_loader_seam``. The
module name is underscore-prefixed so these names remain test-private while being
importable across the two cohesive test modules without duplication. No temp
files, no network.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.schema_registry import DiskSchemaFileStore, SchemaRegistry

if TYPE_CHECKING:
    from src.schema_model import SchemaDefinition

__all__ = [
    "_MONTHS_A",
    "_MONTHS_B",
    "_load_default",
]

# Twelve monthly vectors reused across the core and seam tests.
_MONTHS_A: list[float] = [
    10.0,
    20.0,
    30.0,
    40.0,
    50.0,
    60.0,
    70.0,
    80.0,
    90.0,
    100.0,
    110.0,
    120.0,
]
_MONTHS_B: list[float] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]


def _load_default(name: str) -> SchemaDefinition:
    """Load a bundled default schema by name through a real disk store.

    Args:
        name: The bundled schema name (``"default_le"`` or ``"default_aop"``).

    Returns:
        The parsed :class:`SchemaDefinition`.
    """
    registry = SchemaRegistry(Path("."), DiskSchemaFileStore())
    return registry.load_bundled_default(name)
