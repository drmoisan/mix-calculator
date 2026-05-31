"""Crash-visibility installer for the GUI process (issue #46).

This module installs the four crash hooks the GUI needs so a catastrophic
failure cannot disappear silently:

- ``faulthandler.enable(file=...)`` writes native-fault tracebacks to a
  per-user crash log.
- ``sys.excepthook`` writes a full Python traceback for any uncaught
  main-thread exception.
- ``threading.excepthook`` does the same for worker-thread exceptions.
- ``qInstallMessageHandler`` routes Qt categories (debug/info/warning/critical/
  system/fatal) through Python ``logging`` at the matching levels.

Responsibilities:
    - Provide :func:`install_crash_handlers` (composition-root entry point).
    - Provide :func:`resolve_log_dir` (pure platform-branch helper testable
      without filesystem touch).
    - Build the four hook callables and record an immutable
      :class:`CrashHandlerInstallation` describing what was installed.

Boundaries:
    - Hook installation is one-shot. A second call to
      :func:`install_crash_handlers` returns the prior installation unchanged
      and does not re-register hooks (AC-4).
    - The faulthandler file handle is held on a module-level singleton
      (:class:`_State`) so the handle stays open for the life of the process;
      without that anchor, garbage collection would close the file and the
      faulthandler output would silently drop.
    - I/O boundary functions (``_open_crash_log``, ``_ensure_log_dir``,
      ``_register_faulthandler``, ``_register_qt_message_handler``,
      ``_install_sys_excepthook``, ``_install_threading_excepthook``) are
      module-level names so tests can replace them via ``monkeypatch`` without
      touching the filesystem or process-wide hooks.
"""

from __future__ import annotations

import faulthandler
import logging
import sys
import threading
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

from PySide6.QtCore import QtMsgType, qInstallMessageHandler

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from types import TracebackType

__all__ = [
    "CrashHandlerInstallation",
    "install_crash_handlers",
    "make_qt_message_handler",
    "reset_for_tests",
    "resolve_log_dir",
]

logger = logging.getLogger(__name__)
_qt_logger = logging.getLogger(f"{__name__}.qt")

_APP_NAME_DEFAULT = "mix-calculator"

# The four hook names recorded in CrashHandlerInstallation. Kept as a module
# constant so the contract is in one place and the test assertions can compare
# against the same source of truth.
_INSTALLED_HOOK_NAMES: tuple[str, ...] = (
    "faulthandler",
    "sys.excepthook",
    "threading.excepthook",
    "qt.message_handler",
)


@dataclass(frozen=True)
class CrashHandlerInstallation:
    """Immutable record of what the installer registered.

    Purpose:
        Communicate the installation outcome to callers (composition root and
        tests) so they can verify the hooks are in place without inspecting
        process-global state.

    Attributes:
        log_dir: The directory the installer resolved for crash logs.
        crash_log_path: The full path to the per-process crash log file.
        installed_hooks: Stable tuple of hook names (``faulthandler``,
            ``sys.excepthook``, ``threading.excepthook``, ``qt.message_handler``).
            Empty tuple when the installer is called with ``enable=False``.
    """

    log_dir: Path
    crash_log_path: Path
    installed_hooks: tuple[str, ...]


@dataclass
class _State:
    """Module-level singleton holder for the live installation.

    Attributes:
        installation: The :class:`CrashHandlerInstallation` returned to callers.
        crash_log_stream: The open file handle ``faulthandler`` writes to.
            Held here so the handle is not garbage-collected before the process
            exits.
        previous_sys_excepthook: The previous ``sys.excepthook`` value so the
            new hook can chain to it when raising a non-test exception.
        previous_threading_excepthook: The previous ``threading.excepthook``
            value so the new hook can chain to it.
    """

    installation: CrashHandlerInstallation
    crash_log_stream: IO[bytes]
    previous_sys_excepthook: Callable[
        [type[BaseException], BaseException, TracebackType | None], None
    ]
    previous_threading_excepthook: Callable[[threading.ExceptHookArgs], object]


_state: _State | None = None


def resolve_log_dir(
    *, app_name: str, platform_system: str, env: Mapping[str, str]
) -> Path:
    """Resolve the per-user log directory without touching the filesystem.

    Branch order:

    - ``Windows`` -> ``env["LOCALAPPDATA"]`` if present, else
      ``Path.home() / "AppData" / "Local"``.
    - ``Darwin`` -> ``Path.home() / "Library" / "Logs"``.
    - everything else (treated as Linux/other) -> ``env["XDG_STATE_HOME"]`` if
      present, else ``Path.home() / ".local" / "state"``.

    Each branch then appends ``<app_name> / "logs"`` to the chosen base.

    Args:
        app_name: The application name; appended to the chosen base.
        platform_system: Value comparable to ``platform.system()`` output.
        env: An injected environment mapping; ``os.environ`` is not read.

    Returns:
        The resolved log directory as a ``Path``. The directory is not created
        here; that is the installer's responsibility.
    """
    # Branching is platform-driven so the per-user log location matches the
    # platform conventions developers expect when reading documentation.
    if platform_system == "Windows":
        # Windows: prefer LOCALAPPDATA so a roaming-profile user lands in the
        # same per-machine cache that other applications use; fall back to the
        # canonical AppData/Local path under the home directory.
        local_app_data = env.get("LOCALAPPDATA")
        base = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
    elif platform_system == "Darwin":
        # macOS: Apple convention for log files is ~/Library/Logs.
        base = Path.home() / "Library" / "Logs"
    else:
        # Linux and other Unix-like: prefer XDG_STATE_HOME so the log lives
        # alongside other state files; fall back to the canonical
        # ~/.local/state path defined by the XDG Base Directory specification.
        xdg_state_home = env.get("XDG_STATE_HOME")
        base = (
            Path(xdg_state_home) if xdg_state_home else Path.home() / ".local" / "state"
        )
    return base / app_name / "logs"


# I/O seams below. Each is a small helper that the installer calls so tests
# can replace it with a no-op via monkeypatch without touching the filesystem
# or rebinding process-wide hooks.


def _ensure_log_dir(path: Path) -> None:
    """Create the log directory (parents=True, exist_ok=True) for the installer.

    Args:
        path: The log directory the installer wants to write to.

    Side effects:
        Creates the directory tree on disk. Tests replace this with a no-op.
    """
    path.mkdir(parents=True, exist_ok=True)


def _open_crash_log(path: Path) -> IO[bytes]:
    """Open the crash-log file in append-binary mode for ``faulthandler``.

    Args:
        path: The crash-log file path.

    Returns:
        The opened file handle. The installer holds the handle on its
        singleton state so the file is not closed by garbage collection.
    """
    return path.open("ab", buffering=0)


def _register_faulthandler(stream: IO[bytes]) -> None:
    """Enable ``faulthandler`` against ``stream`` for native-fault capture."""
    faulthandler.enable(file=stream, all_threads=True)


def _install_sys_excepthook(
    hook: Callable[[type[BaseException], BaseException, TracebackType | None], None],
) -> None:
    """Install the Python uncaught-exception hook on ``sys``."""
    sys.excepthook = hook


def _install_threading_excepthook(
    hook: Callable[[threading.ExceptHookArgs], object],
) -> None:
    """Install the worker-thread uncaught-exception hook on ``threading``."""
    threading.excepthook = hook


def _register_qt_message_handler(
    handler: Callable[[QtMsgType, Any, str], None],
) -> None:
    """Install the Qt message handler so Qt diagnostics flow through ``logging``."""
    qInstallMessageHandler(handler)


def _make_sys_excepthook(
    crash_log_path: Path,
    previous: Callable[
        [type[BaseException], BaseException, TracebackType | None], None
    ],
) -> Callable[[type[BaseException], BaseException, TracebackType | None], None]:
    """Build the ``sys.excepthook`` callable.

    Args:
        crash_log_path: The crash-log file written to on each exception.
        previous: The prior ``sys.excepthook`` (chained for safety).

    Returns:
        A callable conforming to the ``sys.excepthook`` signature.
    """

    def _hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        """Write the traceback to the crash log, then call the previous hook."""
        _append_traceback(
            crash_log_path,
            source="sys.excepthook",
            exc_type=exc_type,
            exc_value=exc_value,
            exc_tb=exc_tb,
        )
        # Chain to the previous hook so any caller that already installed one
        # (e.g., pytest, IDE debugger) still observes the exception.
        previous(exc_type, exc_value, exc_tb)

    return _hook


def _make_threading_excepthook(
    crash_log_path: Path,
    previous: Callable[[threading.ExceptHookArgs], object],
) -> Callable[[threading.ExceptHookArgs], None]:
    """Build the ``threading.excepthook`` callable.

    Args:
        crash_log_path: The crash-log file written to on each worker exception.
        previous: The prior ``threading.excepthook`` value (chained). The
            standard-library return type is ``object`` (the previous hook may
            return any value); this hook always returns ``None``.

    Returns:
        A callable conforming to the ``threading.excepthook`` signature.
    """

    def _hook(args: threading.ExceptHookArgs) -> None:
        """Write the worker traceback, then call the previous hook."""
        # threading.ExceptHookArgs.exc_value may be None when an unusual
        # thread teardown delivers no exception instance; substitute a
        # synthetic BaseException so the formatter has something concrete
        # to render rather than silently dropping the record.
        exc_value = (
            args.exc_value
            if args.exc_value is not None
            else BaseException("threading.excepthook: no exception value")
        )
        _append_traceback(
            crash_log_path,
            source="threading.excepthook",
            exc_type=args.exc_type,
            exc_value=exc_value,
            exc_tb=args.exc_traceback,
            thread_name=args.thread.name if args.thread is not None else "unknown",
        )
        previous(args)

    return _hook


def make_qt_message_handler(
    target_logger: logging.Logger,
) -> Callable[[QtMsgType, Any, str], None]:
    """Build the Qt message handler that routes Qt categories to ``logging``.

    Routing table:
        - ``QtDebugMsg`` -> ``DEBUG``
        - ``QtInfoMsg`` -> ``INFO``
        - ``QtWarningMsg`` -> ``WARNING``
        - ``QtCriticalMsg`` -> ``ERROR``
        - ``QtSystemMsg`` -> ``ERROR``
        - ``QtFatalMsg`` -> ``CRITICAL``

    Args:
        target_logger: The logger the handler emits records on.

    Returns:
        A callable with the Qt message-handler signature.
    """
    # Routing table held as a closure so the handler does not re-compute it.
    # `QtSystemMsg` is mapped to ERROR (rather than INFO) because the Qt docs
    # describe it as a system-event message historically equivalent to a
    # critical condition; ERROR matches QtCriticalMsg per AC-7.
    level_table: dict[QtMsgType, int] = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtSystemMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }

    def _handler(msg_type: QtMsgType, _context: Any, message: str) -> None:
        """Route the Qt message to the matching Python logging level."""
        # Default to WARNING for any unknown Qt type so a future Qt addition
        # cannot silently drop messages.
        level = level_table.get(msg_type, logging.WARNING)
        target_logger.log(level, "Qt: %s", message)

    return _handler


def _append_traceback(
    crash_log_path: Path,
    *,
    source: str,
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
    thread_name: str = "main",
) -> None:
    """Append a formatted traceback record to the crash log.

    Args:
        crash_log_path: The crash-log file to append to.
        source: Which hook recorded the traceback (used as a header).
        exc_type: Exception class.
        exc_value: Exception instance.
        exc_tb: Traceback (may be ``None`` for synthesized exceptions).
        thread_name: Reporting thread name; defaults to "main".

    Side effects:
        Appends a text record to ``crash_log_path``. Errors during append are
        caught and reported via the module logger so a write failure does not
        cascade into a second crash.
    """
    timestamp = datetime.now(tz=UTC).isoformat()
    formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    record = f"--- {timestamp} {source} thread={thread_name} ---\n" f"{formatted}\n"
    # Append-safe: a write failure must not raise here because the hook is
    # already running inside a process that just had a failure.
    try:
        with crash_log_path.open("a", encoding="utf-8") as handle:
            handle.write(record)
    except OSError:
        logger.exception("Failed to append crash record to %s", crash_log_path)


def install_crash_handlers(
    *,
    app_name: str = _APP_NAME_DEFAULT,
    log_dir: Path | None = None,
    enable: bool = True,
) -> CrashHandlerInstallation:
    """Install the four crash hooks and return the resulting installation.

    Idempotency: if the installer has already run successfully, the prior
    :class:`CrashHandlerInstallation` is returned unchanged and no hook is
    re-registered.

    Args:
        app_name: Application name used by :func:`resolve_log_dir` to choose
            the per-user log directory. Defaults to ``"mix-calculator"``.
        log_dir: Optional override; when ``None`` the directory is resolved
            from the platform via :func:`resolve_log_dir` with
            ``platform_system=platform.system()`` and ``env=os.environ``.
        enable: When ``False``, returns a no-op installation with an empty
            ``installed_hooks`` tuple and no I/O. Provided so the composition
            root can disable the installer without code surgery (rollback
            hook per the spec).

    Returns:
        A :class:`CrashHandlerInstallation` describing the registered hooks.

    Side effects:
        Creates the resolved log directory (when enabled), opens the crash log
        in append-binary mode, enables ``faulthandler`` against that file,
        installs ``sys.excepthook`` and ``threading.excepthook`` (chained to
        their previous values), and registers the Qt message handler.
    """
    global _state

    # Disabled branch: no I/O, no hook installation, no singleton mutation.
    # Returns an installation whose installed_hooks tuple is empty so the
    # caller can still inspect log_dir / crash_log_path.
    if not enable:
        resolved_dir = log_dir if log_dir is not None else Path()
        return CrashHandlerInstallation(
            log_dir=resolved_dir,
            crash_log_path=resolved_dir / "crash-disabled.log",
            installed_hooks=(),
        )

    # Idempotency: a second call returns the prior installation unchanged.
    if _state is not None:
        return _state.installation

    # Resolve the log directory. The platform branch is in resolve_log_dir so
    # the resolution logic remains pure and testable; only this call site
    # reads the live process environment.
    import os
    import platform as platform_module

    resolved_log_dir = (
        log_dir
        if log_dir is not None
        else resolve_log_dir(
            app_name=app_name, platform_system=platform_module.system(), env=os.environ
        )
    )

    # Create the directory and open the crash log so faulthandler has a file
    # to write to. The handle is anchored on _State below so it stays open.
    _ensure_log_dir(resolved_log_dir)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S")
    crash_log_path = resolved_log_dir / f"crash-{os.getpid()}-{timestamp}.log"
    crash_log_stream = _open_crash_log(crash_log_path)

    # Build and install the four hooks. Each hook chains to its previous value
    # so the installer composes cleanly with anything that ran earlier.
    previous_sys_excepthook = sys.excepthook
    previous_threading_excepthook = threading.excepthook

    _register_faulthandler(crash_log_stream)
    _install_sys_excepthook(
        _make_sys_excepthook(crash_log_path, previous_sys_excepthook)
    )
    _install_threading_excepthook(
        _make_threading_excepthook(crash_log_path, previous_threading_excepthook)
    )
    _register_qt_message_handler(make_qt_message_handler(_qt_logger))

    installation = CrashHandlerInstallation(
        log_dir=resolved_log_dir,
        crash_log_path=crash_log_path,
        installed_hooks=_INSTALLED_HOOK_NAMES,
    )
    _state = _State(
        installation=installation,
        crash_log_stream=crash_log_stream,
        previous_sys_excepthook=previous_sys_excepthook,
        previous_threading_excepthook=previous_threading_excepthook,
    )
    return installation


# Test-only helpers. Not part of the public surface (not in __all__); referenced
# only by tests/gui/test_crash_handler.py via direct import.


def reset_for_tests() -> None:
    """Drop the singleton state so the next install runs from a clean slate.

    Tests call this between cases to avoid the idempotency branch shadowing
    the install-once behavior they want to exercise.
    """
    global _state
    _state = None
