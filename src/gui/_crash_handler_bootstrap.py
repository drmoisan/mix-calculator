"""Crash-handler bootstrap for the GUI entry point.

Purpose:
    Encapsulate the single call site that wires the crash-visibility hooks
    into the GUI composition root. Issue #46 added a four-hook installer
    (`faulthandler`, `sys.excepthook`, `threading.excepthook`, and
    `qInstallMessageHandler`) that must run BEFORE ``QApplication`` is
    constructed. The original implementation embedded the installer call
    inline in ``src/gui/app.py``; this module extracts that call so
    ``app.py`` stays under the repository 500-line file-size cap (AC-12).

Responsibilities:
    - Invoke ``install_crash_handlers`` from ``src.gui._crash_handler`` with
      the canonical ``app_name="mix-calculator"``.
    - Anchor the returned ``CrashHandlerInstallation`` on a module-level
      private name so the faulthandler file descriptor cannot be released
      mid-process by garbage collection.

Rationale for the module-level anchor:
    The installer in ``_crash_handler`` already holds the
    ``CrashHandlerInstallation`` on its private process-wide ``_State``,
    which is sufficient to keep the underlying file handle alive. The
    module-level anchor here is functionally redundant but harmless and
    documents intent at the call site. It mirrors the prior inline pattern
    in ``app.py``::

        _crash_installation = install_crash_handlers(app_name="mix-calculator")
        del _crash_installation  # value is anchored on the installer's _State

    The ``del`` statement was a stylistic acknowledgement that the local
    name was no longer needed; here, we instead stash the value on a
    module-level name. Either form preserves the same observable behavior:
    the file handle stays open for the lifetime of the process.

Side effects:
    Mutates the process-wide ``_State`` inside ``src.gui._crash_handler`` on
    first call (subsequent calls are no-ops by installer contract).

Thread safety:
    Intended to be called once, from the main thread, before any other
    GUI code constructs a ``QApplication``.
"""

from __future__ import annotations

from src.gui._crash_handler import CrashHandlerInstallation, install_crash_handlers

__all__ = ["install_for_main"]


# Module-level anchor for the returned installation. The installer's
# own ``_State`` already retains the value; this name documents intent
# at the call site and mirrors the prior inline ``_crash_installation``
# variable from ``app.py``.
_installation: CrashHandlerInstallation | None = None


def install_for_main() -> None:
    """Install the four crash hooks for the GUI entry point.

    This is a thin wrapper around
    :func:`src.gui._crash_handler.install_crash_handlers` that exists so
    the GUI composition root in ``src/gui/app.py`` can wire the
    crash-visibility installer with a single import and a single call,
    keeping ``app.py`` under the repository 500-line file-size cap
    (AC-12 of issue #46).

    Args:
        None.

    Returns:
        None.

    Side effects:
        Calls ``install_crash_handlers(app_name="mix-calculator")``,
        which (on first call) registers ``faulthandler``,
        ``sys.excepthook``, ``threading.excepthook``, and
        ``qInstallMessageHandler``, and opens a crash-log file under the
        per-user log directory resolved by
        :func:`src.gui._crash_handler.resolve_log_dir`. Stores the
        returned :class:`CrashHandlerInstallation` on the module-level
        ``_installation`` private name so the faulthandler file
        descriptor is anchored beyond the call frame. The installer is
        idempotent: subsequent calls return the same installation and do
        not re-register hooks.
    """
    # Anchor the returned installation on a module-level name so the
    # faulthandler file handle has a strong reference for the lifetime
    # of the process. The installer's internal _State already holds
    # this value; the redundant module-level reference documents intent
    # at the call site and preserves parity with the prior inline
    # pattern in app.py.
    global _installation
    _installation = install_crash_handlers(app_name="mix-calculator")
