"""Unit tests for :mod:`src.gui.exporters.registry`.

Covers ``register``/``get``/``available_formats`` with the ``FakeExporter``:
registration then retrieval by ``format_name``, listing registered names,
overwrite-on-re-registration, and the negative flow where ``get`` of an unknown
format raises the specific error. Also asserts ``FakeExporter`` and the base
contract are structurally compatible. Fabricated data only.
"""

from __future__ import annotations

import pytest

from src.gui.exporters.base import ExporterProtocol
from src.gui.exporters.registry import ExporterRegistry
from tests.gui.fakes.fake_exporters import FakeExporter


def test_register_then_get_returns_same_exporter() -> None:
    """An exporter registered by format_name is retrievable by that name."""
    # Arrange
    registry = ExporterRegistry()
    exporter = FakeExporter("Excel")

    # Act
    registry.register(exporter)

    # Assert
    assert registry.get("Excel") is exporter


def test_available_formats_lists_registered_names() -> None:
    """available_formats lists every registered format name."""
    # Arrange
    registry = ExporterRegistry()
    registry.register(FakeExporter("Excel"))
    registry.register(FakeExporter("CSV"))

    # Act
    formats = registry.available_formats()

    # Assert
    assert formats == ["Excel", "CSV"]


def test_re_register_same_name_overwrites() -> None:
    """Re-registering the same format name replaces the prior exporter."""
    # Arrange
    registry = ExporterRegistry()
    first = FakeExporter("Excel")
    second = FakeExporter("Excel")
    registry.register(first)

    # Act
    registry.register(second)

    # Assert: the second registration wins; only one entry remains.
    assert registry.get("Excel") is second
    assert registry.available_formats() == ["Excel"]


def test_get_unknown_format_raises_key_error() -> None:
    """Resolving an unregistered format raises a specific KeyError."""
    # Arrange
    registry = ExporterRegistry()

    # Act / Assert
    with pytest.raises(KeyError, match="No exporter registered"):
        registry.get("Unknown")


def test_fake_exporter_satisfies_protocol() -> None:
    """FakeExporter is a structural ExporterProtocol implementation."""
    # Arrange / Act
    exporter = FakeExporter("Excel")

    # Assert: the runtime-checkable Protocol confirms structural compatibility.
    assert isinstance(exporter, ExporterProtocol)
