"""Tests for :mod:`src.gui._crash_handler` (crash-visibility installer).

These tests cover AC-1..AC-4 and AC-7 of issue #46:

- AC-1: the module exposes ``install_crash_handlers``, ``CrashHandlerInstallation``,
  and the pure ``resolve_log_dir`` helper.
- AC-2: ``install_crash_handlers`` installs all four hooks and records them in
  the returned value (``faulthandler``, ``sys.excepthook``,
  ``threading.excepthook``, ``qt.message_handler``).
- AC-3: ``resolve_log_dir`` is pure and tested with injected ``env`` mappings
  for Windows / Darwin / Linux. Tests assert against the returned ``Path``
  without touching the filesystem (no ``tempfile``).
- AC-4: a second call to ``install_crash_handlers`` is idempotent.
- AC-7: the Qt message handler routes each Qt category to the matching Python
  ``logging`` level.

Determinism / isolation:
    The installer opens a real crash-log file and registers process-wide hooks
    (``sys.excepthook``, ``threading.excepthook``, faulthandler file, Qt message
    handler). Per the repository unit-test policy ("Creation and use of temporary
    files in tests is strictly prohibited"), the tests patch the installer's I/O
    seams via ``monkeypatch`` (``mkdir``, file opener, ``faulthandler.enable``,
    ``qInstallMessageHandler``) so no file is created on disk and no
    process-wide hook is swapped for the real installer. The hooks are recorded
    in the installer's returned value so the test can verify the recorded
    contract via the public surface.

Headless Qt is forced by ``tests/gui/conftest.py`` (QT_QPA_PLATFORM=offscreen).
"""

from __future__ import annotations

import logging
import sys
import threading
from io import BytesIO
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, cast

import pytest

from src.gui import _crash_handler as crash_handler
from src.gui._crash_handler import (
    CrashHandlerInstallation,
    install_crash_handlers,
    make_qt_message_handler,
    reset_for_tests,
    resolve_log_dir,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping


# Typed no-op seams used by the tests so the patched module-level helpers carry
# concrete signatures and Pyright strict mode does not see Unknown lambdas.


def _noop_open_crash_log(_path: Path) -> IO[bytes]:
    """Stand-in for `_open_crash_log` that returns an in-memory stream."""
    return BytesIO()


def _noop_path(_path: Path) -> None:
    """Stand-in for a void Path-consuming helper (`_ensure_log_dir`)."""


def _noop_stream(_stream: IO[bytes]) -> None:
    """Stand-in for `_register_faulthandler` that ignores the stream."""


def _noop_handler(_handler: Callable[..., Any]) -> None:
    """Stand-in for `_register_qt_message_handler` that ignores the handler."""


def _noop_sys_excepthook(_hook: Callable[..., Any]) -> None:
    """Stand-in for `_install_sys_excepthook` that ignores the hook."""


def _noop_threading_excepthook(_hook: Callable[..., Any]) -> None:
    """Stand-in for `_install_threading_excepthook` that ignores the hook."""


def _patch_io_seams(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace every I/O seam in the crash-handler module with typed no-ops.

    Args:
        monkeypatch: The test's ``monkeypatch`` fixture.

    Side effects:
        Rebinds the six module-level I/O helpers to the typed no-ops defined
        above so the installer can be exercised without touching the
        filesystem or rebinding process-wide hooks.
    """
    monkeypatch.setattr(crash_handler, "_open_crash_log", _noop_open_crash_log)
    monkeypatch.setattr(crash_handler, "_ensure_log_dir", _noop_path)
    monkeypatch.setattr(crash_handler, "_register_faulthandler", _noop_stream)
    monkeypatch.setattr(crash_handler, "_register_qt_message_handler", _noop_handler)
    monkeypatch.setattr(crash_handler, "_install_sys_excepthook", _noop_sys_excepthook)
    monkeypatch.setattr(
        crash_handler, "_install_threading_excepthook", _noop_threading_excepthook
    )


@pytest.fixture(autouse=True)
def reset_crash_handler_state() -> Iterator[None]:
    """Reset the crash-handler singleton between tests for isolation.

    Autouse fixture so every test in this module starts with a fresh
    installer singleton. The fixture is registered by name in pytest's
    fixture cache; the function body is the cache value, not consumed by
    explicit references in tests.
    """
    # Pre-test reset (idempotent if state has not been set yet).
    reset_for_tests()
    yield
    # Post-test reset so the next test starts with a clean singleton.
    reset_for_tests()


# AC-1: module exposes the documented public surface.


def test_module_exposes_documented_public_surface() -> None:
    """The crash-handler module exposes the symbols enumerated in the spec.

    Importing the module at top level already exercises name resolution; this
    extra assertion documents the contract and keeps a regression test next to
    the contract.
    """
    # Arrange / Act / Assert: each symbol is bound to a callable or class.
    assert callable(install_crash_handlers)
    assert isinstance(CrashHandlerInstallation, type)
    assert callable(resolve_log_dir)


# AC-3: resolve_log_dir platform branches (pure; no filesystem touch).


@pytest.mark.parametrize(
    ("platform_system", "env", "expected"),
    [
        (
            "Windows",
            {"LOCALAPPDATA": "C:/Users/test/AppData/Local"},
            Path("C:/Users/test/AppData/Local") / "mix-calculator" / "logs",
        ),
        (
            "Windows",
            {},
            Path.home() / "AppData" / "Local" / "mix-calculator" / "logs",
        ),
        (
            "Darwin",
            {},
            Path.home() / "Library" / "Logs" / "mix-calculator" / "logs",
        ),
        (
            "Linux",
            {"XDG_STATE_HOME": "/var/lib/state"},
            Path("/var/lib/state") / "mix-calculator" / "logs",
        ),
        (
            "Linux",
            {},
            Path.home() / ".local" / "state" / "mix-calculator" / "logs",
        ),
    ],
)
def test_resolve_log_dir_branches(
    platform_system: str,
    env: Mapping[str, str],
    expected: Path,
) -> None:
    """`resolve_log_dir` returns the spec-mandated Path for each platform branch.

    Args:
        platform_system: Value comparable to ``platform.system()`` output.
        env: An injected environment mapping; nothing is read from
            ``os.environ``.
        expected: The Path the resolver must produce. Assertions use ``Path``
            equality only — the filesystem is never touched.
    """
    # Arrange / Act
    resolved = resolve_log_dir(
        app_name="mix-calculator", platform_system=platform_system, env=env
    )

    # Assert: returned Path equals the expected segments exactly.
    assert resolved == expected


# AC-2: install_crash_handlers installs all four hooks and records them.


def test_install_crash_handlers_installs_all_four_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The installer reports the four hook names in ``installed_hooks``.

    The installer's I/O is patched so no file is created and the process-wide
    hooks are not actually rebound; the assertion is over the recorded contract
    in the returned ``CrashHandlerInstallation``.
    """
    # Arrange
    _patch_io_seams(monkeypatch)
    log_dir = Path("C:/fake/crash/dir")

    # Act
    install = install_crash_handlers(
        app_name="mix-calculator", log_dir=log_dir, enable=True
    )

    # Assert: the returned value is a CrashHandlerInstallation and the four
    # hook names are present, in a stable order so a future regression is
    # easy to spot.
    assert isinstance(install, CrashHandlerInstallation)
    assert install.installed_hooks == (
        "faulthandler",
        "sys.excepthook",
        "threading.excepthook",
        "qt.message_handler",
    )
    assert install.log_dir == log_dir
    assert install.crash_log_path.parent == log_dir


def test_install_crash_handlers_disabled_returns_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``enable=False`` returns an installation with no recorded hooks.

    Documents the feature-flag rollback hook described in the spec; the
    installer must not install any hooks when disabled.
    """
    # Arrange: still patch the seams so even if a regression switches the
    # disabled branch, no file is created.
    _patch_io_seams(monkeypatch)
    log_dir = Path("C:/fake/crash/dir")

    # Act
    install = install_crash_handlers(
        app_name="mix-calculator", log_dir=log_dir, enable=False
    )

    # Assert
    assert install.installed_hooks == ()


# AC-4: install is idempotent.


def test_install_crash_handlers_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling the installer twice returns the same value without re-hooking.

    Idempotency is verified by comparing the recorded ``CrashHandlerInstallation``
    after the first call to the second call's return value. The pre-call
    ``sys.excepthook`` / ``threading.excepthook`` identities are recorded and
    compared after the second call to confirm no rebind occurred (the seams
    are patched, so the real hooks are never touched).
    """
    # Arrange
    _patch_io_seams(monkeypatch)
    log_dir = Path("C:/fake/crash/dir")
    sys_hook_before = sys.excepthook
    threading_hook_before = threading.excepthook

    # Act 1: first install records the contract.
    first = install_crash_handlers(
        app_name="mix-calculator", log_dir=log_dir, enable=True
    )

    # Act 2: second install must be a no-op for hooks.
    second = install_crash_handlers(
        app_name="mix-calculator", log_dir=log_dir, enable=True
    )

    # Assert: equivalent values and unchanged process hooks.
    assert second.installed_hooks == first.installed_hooks
    assert second.log_dir == first.log_dir
    assert second.crash_log_path == first.crash_log_path
    assert second is first or second == first
    assert sys.excepthook is sys_hook_before
    assert threading.excepthook is threading_hook_before


# AC-7: Qt message handler routes categories to matching logging levels.


def test_qt_message_handler_routes_categories_to_logging_levels(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Each Qt category routes to the matching Python ``logging`` level.

    Invokes the handler directly with each Qt message type. The installer is
    driven first so the handler-factory helper has been imported, but the
    process Qt hook is not actually rebound (the seam is patched).
    """
    # Arrange: drive the installer in-memory then build the handler directly.
    from PySide6.QtCore import QtMsgType

    _patch_io_seams(monkeypatch)
    install_crash_handlers(
        app_name="mix-calculator", log_dir=Path("C:/fake/crash/dir"), enable=True
    )

    handler_logger = logging.getLogger("src.gui._crash_handler.qt")
    handler = make_qt_message_handler(handler_logger)

    # Routing table: each entry is (Qt category, expected logging level).
    cases = [
        (QtMsgType.QtDebugMsg, logging.DEBUG),
        (QtMsgType.QtInfoMsg, logging.INFO),
        (QtMsgType.QtWarningMsg, logging.WARNING),
        (QtMsgType.QtCriticalMsg, logging.ERROR),
        (QtMsgType.QtSystemMsg, logging.ERROR),
        (QtMsgType.QtFatalMsg, logging.CRITICAL),
    ]

    # Act / Assert: drive each category and verify the matching level appears.
    for qt_type, expected_level in cases:
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="src.gui._crash_handler.qt"):
            handler(qt_type, None, f"msg-{qt_type}")
        level_seen = [r.levelno for r in caplog.records]
        assert expected_level in level_seen, (
            f"Qt category {qt_type!r} did not route to level "
            f"{expected_level}: observed {level_seen}"
        )


# R4: Direct-invocation tests for the crash-write closures and `_append_traceback`.
#
# These tests exercise the previously-uncovered closure bodies (lines 254-263,
# 290-303) and the on-disk write helper (`_append_traceback`, lines 374-383)
# without touching the real filesystem. The seam used here is a `_FakePath`
# wrapper whose ``.open()`` returns a ``BytesIO`` sink. The wrapper is passed
# in place of a real ``Path`` (via ``cast``) so ``_append_traceback`` can call
# ``crash_log_path.open("a", encoding="utf-8")`` and the test can inspect the
# captured bytes.


class _FakePath:
    """In-memory stand-in for ``pathlib.Path`` exposing only ``.open()``.

    Purpose:
        Provide a duck-typed substitute for the ``crash_log_path`` argument
        passed to the crash-write closures and ``_append_traceback`` so the
        write call lands in a ``BytesIO`` buffer instead of on disk.

    Responsibilities:
        - Hold a single ``BytesIO`` sink.
        - Return that sink whenever ``.open()`` is called, regardless of mode.
        - Surface the captured bytes to the test via :attr:`sink`.

    Side effects:
        None beyond mutating the in-memory ``BytesIO`` sink when callers
        write to the file-like returned by :meth:`open`.
    """

    def __init__(self) -> None:
        """Initialize the wrapper with an empty in-memory sink."""
        self.sink: BytesIO = BytesIO()

    def open(self, _mode: str = "r", encoding: str | None = None) -> Any:
        """Return a context-manager-friendly wrapper around the sink.

        Args:
            _mode: File open mode (ignored; accepted for ``Path.open``
                signature compatibility).
            encoding: Text encoding requested by the caller. When set, the
                wrapper presents a text-mode interface that re-encodes
                written strings into the underlying byte sink so
                ``_append_traceback``'s ``encoding="utf-8"`` call works.

        Returns:
            A duck-typed file-like wrapper. Typed as ``Any`` because the
            production code uses only the ``write`` and context-manager
            protocol; matching the full ``IO[Any]`` Protocol would require
            stubbing twenty unused methods.
        """
        return _FakeHandle(self.sink, encoding=encoding)


class _FakeHandle:
    """File-like wrapper that writes through to an underlying ``BytesIO``.

    Purpose:
        Allow ``_append_traceback``'s ``with crash_log_path.open(...) as h:``
        block to write text without a real file descriptor.

    Responsibilities:
        - Behave as a context manager (``__enter__`` / ``__exit__``).
        - Accept either ``str`` (text mode) or ``bytes`` (binary mode) writes.

    Side effects:
        Mutates the wrapped ``BytesIO`` sink on every ``write`` call.
    """

    def __init__(self, sink: BytesIO, encoding: str | None) -> None:
        """Hold the sink and encoding used to re-encode text writes."""
        self._sink: BytesIO = sink
        self._encoding: str = encoding or "utf-8"

    def __enter__(self) -> _FakeHandle:
        """Return self so the ``with`` block has the writable handle."""
        return self

    def __exit__(self, *_args: object) -> None:
        """Close is a no-op; the sink stays readable for assertions."""

    def write(self, data: str | bytes) -> int:
        """Append ``data`` to the sink, encoding text to bytes if needed.

        Args:
            data: Either a ``str`` (re-encoded via ``self._encoding``) or
                pre-encoded ``bytes``.

        Returns:
            The number of bytes written.
        """
        # Decision-logic: ``_append_traceback`` opens the file in text mode
        # ("a") with utf-8 encoding, so the production path writes ``str``.
        # The branch covers the bytes case for defensive completeness.
        if isinstance(data, str):
            payload = data.encode(self._encoding)
        else:
            payload = data
        return self._sink.write(payload)


def test_sys_excepthook_appends_traceback_record() -> None:
    """AC-10 (informational): exercises the ``sys.excepthook`` closure built by
    ``_make_sys_excepthook`` end-to-end, ensuring ``_append_traceback`` is
    invoked and writes the expected record.
    """
    # Arrange: build an in-memory path stand-in; capture chain calls.
    fake_path = _FakePath()
    chain_calls: list[tuple[type[BaseException], BaseException, Any]] = []

    def _record_previous(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: object,
    ) -> None:
        """Stand-in previous sys.excepthook that records each call."""
        chain_calls.append((exc_type, exc_value, exc_tb))

    # Reach into the module for the private builder via ``vars(module)[name]``
    # so neither Pyright (reportPrivateUsage) nor Ruff (B009) flags the
    # access. The cast documents the callable's signature.
    make_sys_hook = cast(
        "Callable[..., Callable[[type[BaseException], BaseException, Any], None]]",
        vars(crash_handler)["_make_sys_excepthook"],
    )
    hook = make_sys_hook(cast("Path", fake_path), _record_previous)

    # Act: invoke the hook with a synthesized exception triple.
    hook(ValueError, ValueError("boom"), None)

    # Assert: the sink captured the expected record and the chain fired.
    captured = fake_path.sink.getvalue().decode("utf-8")
    assert "sys.excepthook" in captured
    assert "ValueError" in captured
    assert "boom" in captured
    assert len(chain_calls) == 1
    assert chain_calls[0][0] is ValueError


def test_threading_excepthook_appends_traceback_record() -> None:
    """AC-10 (informational): exercises the ``threading.excepthook`` closure
    built by ``_make_threading_excepthook``.
    """
    # Arrange: in-memory sink, a named worker thread, and a chain recorder.
    fake_path = _FakePath()
    chain_calls: list[threading.ExceptHookArgs] = []

    def _record_previous(args: threading.ExceptHookArgs) -> None:
        """Stand-in previous threading.excepthook that records each call."""
        chain_calls.append(args)

    make_threading_hook = cast(
        "Callable[..., Callable[[threading.ExceptHookArgs], None]]",
        vars(crash_handler)["_make_threading_excepthook"],
    )
    hook = make_threading_hook(cast("Path", fake_path), _record_previous)

    worker = threading.Thread(name="test-worker")
    # ``threading.ExceptHookArgs`` is the named-tuple shape passed to the
    # platform hook; constructing it directly keeps the test in-process and
    # avoids spawning a real exception in a background thread.
    hook_args = threading.ExceptHookArgs([ValueError, ValueError("boom"), None, worker])

    # Act: invoke the hook once with the synthesized args.
    hook(hook_args)

    # Assert: the sink captured the worker name, exception type/message,
    # the source header, and the chain was invoked exactly once.
    captured = fake_path.sink.getvalue().decode("utf-8")
    assert "threading.excepthook" in captured
    assert "ValueError" in captured
    assert "boom" in captured
    assert "test-worker" in captured
    assert len(chain_calls) == 1
    assert chain_calls[0] is hook_args


def test_append_traceback_swallows_oserror(caplog: pytest.LogCaptureFixture) -> None:
    """AC-10 (informational): ``_append_traceback`` swallows ``OSError`` from the
    log open and reports it through the module logger so a write failure cannot
    cascade into a second crash.
    """

    # Arrange: build a Path-like wrapper whose .open raises OSError.
    class _RaisingPath:
        """``Path``-shaped wrapper whose ``open`` raises ``OSError``."""

        def open(self, _mode: str = "r", encoding: str | None = None) -> Any:
            """Always raise ``OSError`` to exercise the catch branch."""
            del encoding  # unused; signature parity with Path.open
            raise OSError("disk full")

    raising_path = cast("Path", _RaisingPath())

    append_traceback = cast(
        "Callable[..., None]",
        vars(crash_handler)["_append_traceback"],
    )

    # Act: call with caplog capturing ERROR-level records from the module
    # logger. The hook must NOT propagate the OSError.
    with caplog.at_level(logging.ERROR, logger="src.gui._crash_handler"):
        append_traceback(
            raising_path,
            source="sys.excepthook",
            exc_type=ValueError,
            exc_value=ValueError("boom"),
            exc_tb=None,
        )

    # Assert: at least one ERROR-level record cites the failure cause and no
    # exception bubbled out of the call (the test would have errored
    # otherwise).
    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert error_records, "Expected at least one ERROR-level log record"
    assert any("Failed to append crash record" in r.getMessage() for r in error_records)
