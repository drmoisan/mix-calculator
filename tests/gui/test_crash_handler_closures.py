"""Closure-pinning tests for the crash-write closures and ``_append_traceback``.

Purpose:
    Exercise the crash-write closures returned by ``_make_sys_excepthook`` and
    ``_make_threading_excepthook`` plus the on-disk write helper
    ``_append_traceback`` defined in :mod:`src.gui._crash_handler`. Split from
    ``test_crash_handler.py`` to keep both files under the 500-line cap
    defined in ``.claude/rules/general-code-change.md``.

Responsibilities:
    - Direct-invoke the two excepthook closures via the private builders and
      assert that each writes the expected record into an in-memory sink.
    - Verify ``_append_traceback`` swallows ``OSError`` from the underlying
      ``Path.open`` and reports the failure via the module logger so a write
      failure cannot cascade into a second crash.

Determinism / isolation:
    No real filesystem access. The seam is a ``_FakePath`` whose ``.open()``
    returns a ``_FakeHandle`` backed by ``io.BytesIO``. The wrapper is passed
    in place of a real ``Path`` (via ``cast``) so ``_append_traceback`` can
    call ``crash_log_path.open("a", encoding="utf-8")`` and the test can
    inspect the captured bytes. Per the repository unit-test policy, no
    temporary files are created on disk.

Headless Qt is forced by ``tests/gui/conftest.py`` (QT_QPA_PLATFORM=offscreen).
"""

from __future__ import annotations

import logging
import threading
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast

from src.gui import _crash_handler as crash_handler

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest


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
