"""Pure resolution of the shared schema-registry directory.

This module resolves the directory in which schema definition JSON files live.
The directory is shared across databases (independent of any single ``.db``
path) and is resolved from injected seams only, so the logic is unit-testable
without touching the real filesystem or ``os.environ``.

Resolution order:
    - If the environment maps :data:`MIX_CALCULATOR_SCHEMA_DIR` to a non-empty
      value, that path wins.
    - Otherwise a per-user application-data default is used: a ``%APPDATA%``-based
      path on Windows (``<APPDATA>/mix-calculator/schemas``), and an XDG-style
      path otherwise (``$XDG_DATA_HOME/mix-calculator/schemas`` when set, else
      ``<home>/.local/share/mix-calculator/schemas``).

Responsibilities:
    - ``resolve_registry_dir``: compute the registry directory from injected
      environment, platform marker, and home directory.

Scope boundaries:
    - Pure path computation. No filesystem access, no ``os.environ`` reads, no
      directory creation. The registry (:mod:`src.schema_registry`) owns I/O.
    - Standard library only (``pathlib``, ``typing``).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

# Environment variable that overrides the default registry directory. Kept as a
# module constant so callers and tests reference the same name.
MIX_CALCULATOR_SCHEMA_DIR = "MIX_CALCULATOR_SCHEMA_DIR"

# Application sub-directory under the per-user data location.
_APP_DIR_NAME = "mix-calculator"
_SCHEMAS_DIR_NAME = "schemas"


def resolve_registry_dir(
    *,
    env: Mapping[str, str],
    platform: str,
    home: Path,
) -> Path:
    """Resolve the shared schema-registry directory from injected seams.

    Args:
        env: A mapping of environment variables (injected; not read from the
            process environment). The :data:`MIX_CALCULATOR_SCHEMA_DIR` key, when
            present and non-empty, overrides the default.
        platform: The platform marker (for example ``sys.platform``). A value of
            ``"win32"`` selects the Windows ``%APPDATA%`` default; any other
            value selects the XDG-style default.
        home: The user's home directory (injected; not read from the filesystem).
            Used for the XDG-style fallback and as the base when ``%APPDATA%`` is
            absent on Windows.

    Returns:
        The resolved registry directory as a ``Path``. The path is computed only;
        it is not created and its existence is not checked.

    Side effects:
        None. This function performs no filesystem or environment access beyond
        reading the injected ``env`` mapping.
    """
    # The explicit env override takes precedence over any per-user default so a
    # caller can point the registry at an arbitrary shared location.
    override = env.get(MIX_CALCULATOR_SCHEMA_DIR)
    if override:
        return Path(override)

    # Platform routing: Windows uses %APPDATA%; every other platform uses an
    # XDG-style data directory. The branch exists because the per-user data
    # convention differs between Windows and POSIX-like systems.
    if platform == "win32":
        return _windows_default(env=env, home=home)
    return _xdg_default(env=env, home=home)


def _windows_default(*, env: Mapping[str, str], home: Path) -> Path:
    """Compute the Windows per-user default registry directory.

    Args:
        env: The injected environment mapping; ``APPDATA`` is used when present.
        home: The home directory used as a base when ``APPDATA`` is absent.

    Returns:
        ``<APPDATA>/mix-calculator/schemas`` when ``APPDATA`` is set, otherwise
        ``<home>/AppData/Roaming/mix-calculator/schemas``.
    """
    # Prefer the standard %APPDATA% roaming location; fall back to its
    # conventional path under the home directory when the variable is absent so
    # resolution stays deterministic without environment access.
    appdata = env.get("APPDATA")
    base = Path(appdata) if appdata else home / "AppData" / "Roaming"
    return base / _APP_DIR_NAME / _SCHEMAS_DIR_NAME


def _xdg_default(*, env: Mapping[str, str], home: Path) -> Path:
    """Compute the XDG-style per-user default registry directory.

    Args:
        env: The injected environment mapping; ``XDG_DATA_HOME`` is used when set.
        home: The home directory used for the ``~/.local/share`` fallback.

    Returns:
        ``<XDG_DATA_HOME>/mix-calculator/schemas`` when ``XDG_DATA_HOME`` is set,
        otherwise ``<home>/.local/share/mix-calculator/schemas``.
    """
    # Honor XDG_DATA_HOME when present; otherwise use the XDG-specified default
    # of ~/.local/share so behavior matches platform conventions.
    xdg = env.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else home / ".local" / "share"
    return base / _APP_DIR_NAME / _SCHEMAS_DIR_NAME
