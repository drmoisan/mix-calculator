"""Unit tests for :mod:`src.gui.services.db_service`.

Covers ``DbService.save_tables``/``open_tables``/``list_tables`` round-trips
using ``sqlite3.connect(":memory:")`` via the ``PersistentConnection`` /
``patch_connect`` pattern from ``tests.le_fixtures``. Asserts frame round-trip
equality, ``if_exists="replace"`` overwrite semantics, and a negative flow for an
empty/missing-table database. No temporary files are created. Fabricated data
only; no confidential values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.gui.services.db_service import DbService
from tests.le_fixtures import patch_connect

if TYPE_CHECKING:
    import pytest


def _fabricated_tables() -> dict[str, pd.DataFrame]:
    """Return a fabricated two-table working set for round-trip tests."""
    le = pd.DataFrame({"KEY": ["k1", "k2"], "FY": [10.0, 20.0]})
    mix = pd.DataFrame({"value": [42.0]})
    return {"LE": le, "mix_rollup_4": mix}


def test_save_then_open_round_trips_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    """save_tables then open_tables returns the same table set and content."""
    # Arrange: one shared in-memory connection for both the save and the open.
    con = patch_connect(monkeypatch)
    service = DbService()
    tables = _fabricated_tables()

    # Act
    service.save_tables(tables, "ignored.db")
    loaded = service.open_tables("ignored.db")

    # Assert: the same table names round-trip with equal content.
    assert set(loaded) == {"LE", "mix_rollup_4"}
    pd.testing.assert_frame_equal(loaded["LE"], tables["LE"])
    pd.testing.assert_frame_equal(loaded["mix_rollup_4"], tables["mix_rollup_4"])
    con.real_close()


def test_save_tables_replaces_existing_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """A second save with if_exists=replace overwrites prior table contents."""
    # Arrange
    con = patch_connect(monkeypatch)
    service = DbService()
    first = {"LE": pd.DataFrame({"KEY": ["old"], "FY": [1.0]})}
    second = {"LE": pd.DataFrame({"KEY": ["new-a", "new-b"], "FY": [2.0, 3.0]})}

    # Act: save twice; the second save must replace, not append.
    service.save_tables(first, "ignored.db")
    service.save_tables(second, "ignored.db")
    loaded = service.open_tables("ignored.db")

    # Assert: only the second save's rows remain.
    assert list(loaded["LE"]["KEY"]) == ["new-a", "new-b"]
    con.real_close()


def test_list_tables_excludes_sqlite_internal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """list_tables returns only user tables, sorted, excluding sqlite_* tables."""
    # Arrange
    con = patch_connect(monkeypatch)
    service = DbService()
    service.save_tables(_fabricated_tables(), "ignored.db")

    # Act
    names = service.list_tables(con)

    # Assert: the two user tables, sorted; no sqlite internal tables.
    assert names == ["LE", "mix_rollup_4"]
    con.real_close()


def test_open_tables_empty_database_returns_empty_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Opening a database with no user tables returns an empty dict."""
    # Arrange: a fresh in-memory connection with nothing written.
    con = patch_connect(monkeypatch)
    service = DbService()

    # Act
    loaded = service.open_tables("ignored.db")

    # Assert
    assert loaded == {}
    con.real_close()
