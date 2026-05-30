"""Unit tests for :mod:`src.schema_settings` registry-directory resolution.

All seams (environment mapping, platform marker, home directory) are injected;
no test mutates ``os.environ``, reads the real filesystem, or creates temp files.
Each test follows Arrange-Act-Assert.
"""

from __future__ import annotations

from pathlib import Path

from src.schema_settings import (
    MIX_CALCULATOR_SCHEMA_DIR,
    resolve_registry_dir,
)


def test_env_override_wins() -> None:
    """An explicit env override is returned verbatim regardless of platform."""
    # Arrange
    override = "D:/shared/schemas"
    env = {MIX_CALCULATOR_SCHEMA_DIR: override}

    # Act
    resolved = resolve_registry_dir(
        env=env, platform="win32", home=Path("C:/Users/dev")
    )

    # Assert
    assert resolved == Path(override)


def test_windows_default_uses_injected_appdata() -> None:
    """On Windows without an override, the injected %APPDATA% is the base."""
    # Arrange
    env = {"APPDATA": "C:/Users/dev/AppData/Roaming"}

    # Act
    resolved = resolve_registry_dir(
        env=env, platform="win32", home=Path("C:/Users/dev")
    )

    # Assert
    assert resolved == Path("C:/Users/dev/AppData/Roaming/mix-calculator/schemas")


def test_windows_default_falls_back_to_home_when_no_appdata() -> None:
    """On Windows with no %APPDATA%, the home-based roaming path is used."""
    # Arrange
    env: dict[str, str] = {}

    # Act
    resolved = resolve_registry_dir(
        env=env, platform="win32", home=Path("C:/Users/dev")
    )

    # Assert
    assert resolved == Path("C:/Users/dev/AppData/Roaming/mix-calculator/schemas")


def test_non_windows_default_uses_xdg_data_home() -> None:
    """On non-Windows, an injected XDG_DATA_HOME is the base."""
    # Arrange
    env = {"XDG_DATA_HOME": "/home/dev/.xdg"}

    # Act
    resolved = resolve_registry_dir(env=env, platform="linux", home=Path("/home/dev"))

    # Assert
    assert resolved == Path("/home/dev/.xdg/mix-calculator/schemas")


def test_non_windows_default_falls_back_to_local_share() -> None:
    """On non-Windows with no XDG_DATA_HOME, ~/.local/share is the base."""
    # Arrange
    env: dict[str, str] = {}

    # Act
    resolved = resolve_registry_dir(env=env, platform="darwin", home=Path("/Users/dev"))

    # Assert
    assert resolved == Path("/Users/dev/.local/share/mix-calculator/schemas")


def test_resolution_is_independent_of_database_path() -> None:
    """A database-like path in the environment does not affect resolution."""
    # Arrange: an unrelated DB path key must be ignored by resolution.
    env = {"MIX_CALCULATOR_DB": "/data/mix.db", "XDG_DATA_HOME": "/home/dev/.xdg"}

    # Act
    resolved = resolve_registry_dir(env=env, platform="linux", home=Path("/home/dev"))

    # Assert
    assert resolved == Path("/home/dev/.xdg/mix-calculator/schemas")
    assert "mix.db" not in str(resolved)
