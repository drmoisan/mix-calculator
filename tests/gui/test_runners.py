"""Unit tests for :mod:`src.gui.runners` (RunnerProtocol implementations).

Covers the ``SynchronousRunner`` (test seam) success/error routing and a
structural check that ``ThreadedRunner`` satisfies the ``RunnerProtocol``
contract. The synchronous-runner tests run without a ``QApplication`` because
the seam is pure Python; the structural check is also pure Python and exercises
only ``isinstance`` against the runtime-checkable Protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.gui.runners import RunnerProtocol, SynchronousRunner, ThreadedRunner

if TYPE_CHECKING:
    import pandas as pd


def test_synchronous_runner_success_routes_to_on_success() -> None:
    """A normal-return task routes the result to ``on_success`` only."""
    # Arrange
    runner = SynchronousRunner()
    expected_result: dict[str, pd.DataFrame] = {}

    def task() -> dict[str, pd.DataFrame]:
        return expected_result

    success_calls: list[dict[str, pd.DataFrame]] = []
    error_calls: list[str] = []

    # Act
    runner.run(task, success_calls.append, error_calls.append)

    # Assert: success was invoked with the task's return value; error was not.
    assert success_calls == [expected_result]
    assert error_calls == []


def test_synchronous_runner_value_error_routes_to_on_error() -> None:
    """A ``ValueError`` raised by the task routes to ``on_error`` with its message."""
    # Arrange
    runner = SynchronousRunner()

    def task() -> dict[str, pd.DataFrame]:
        raise ValueError("boom")

    success_calls: list[dict[str, pd.DataFrame]] = []
    error_calls: list[str] = []

    # Act
    runner.run(task, success_calls.append, error_calls.append)

    # Assert: only on_error was called, with the stringified message.
    assert error_calls == ["boom"]
    assert success_calls == []


def test_synchronous_runner_non_value_error_routes_to_on_error() -> None:
    """A non-``ValueError`` exception still routes to ``on_error`` with str(exc)."""
    # Arrange: a RuntimeError carries the runner's failure boundary contract.
    runner = SynchronousRunner()

    def task() -> dict[str, pd.DataFrame]:
        raise RuntimeError("kaboom")

    success_calls: list[dict[str, pd.DataFrame]] = []
    error_calls: list[str] = []

    # Act
    runner.run(task, success_calls.append, error_calls.append)

    # Assert: on_error received the stringified RuntimeError message.
    assert error_calls == ["kaboom"]
    assert success_calls == []


def test_threaded_runner_implements_runner_protocol() -> None:
    """``ThreadedRunner`` structurally satisfies :class:`RunnerProtocol`."""
    # Arrange + Act
    runner = ThreadedRunner()

    # Assert: the runtime-checkable Protocol recognises the instance, and the
    # ``run`` attribute is callable (defensive double-check on the seam).
    assert isinstance(runner, RunnerProtocol)
    assert callable(runner.run)


def test_synchronous_runner_implements_runner_protocol() -> None:
    """``SynchronousRunner`` structurally satisfies :class:`RunnerProtocol`."""
    # Arrange + Act
    runner = SynchronousRunner()

    # Assert
    assert isinstance(runner, RunnerProtocol)
