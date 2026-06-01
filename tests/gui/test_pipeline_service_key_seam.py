"""WS1a KEY-mismatch seam tests for :class:`PipelineService` (issue #48).

Verifies the constructor-injectable ``key_mismatch_resolver`` seam: the default
resolver yields ``"trust"`` ("Keep existing") so the LE and AOP loaders never
reach the stdin ``input()`` path, and an injected resolver maps "Keep existing"
-> trust and "Rebuild" -> overwrite through to the loaders. All loader reads are
captured by recording stand-ins; no real stdin or workbook I/O occurs (AC-1,
AC-2 AOP half, AC-3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.gui._key_mismatch_seam import (
    default_key_mismatch_resolver,
    never_tty,
    no_stdin_prompt,
)
from src.gui.pipeline_service import ImportSpec, PipelineService

if TYPE_CHECKING:
    import pandas as pd


class _LoaderRecorder:
    """Records the KEY-related kwargs each loader receives.

    Purpose:
        Prove the service forwards the resolved policy and the no-stdin seams to
        the LE and AOP loaders without performing any real workbook or stdin I/O.

    Attributes:
        le_calls: Each LE-loader ``key_mismatch`` value, in call order.
        aop_calls: Each AOP-loader ``key_mismatch`` value, in call order.
        stdin_reached: Whether any loader invoked the injected prompt seam.
    """

    def __init__(self) -> None:
        """Initialize with no recorded calls."""
        self.le_calls: list[str] = []
        self.aop_calls: list[str] = []
        self.stdin_reached = False


def _install_recording_loaders(
    monkeypatch: pytest.MonkeyPatch, recorder: _LoaderRecorder
) -> None:
    """Patch the LE/AOP/SKU_LU loaders to record kwargs and return empty frames.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        recorder: The recorder capturing each loader's ``key_mismatch`` value.

    Returns:
        ``None``.

    Side effects:
        Replaces ``src.normalize_le.load_source``, ``src.load_aop.load_aop``, and
        ``src.load_skulu.load_skulu`` with recording stand-ins.
    """
    import pandas as pd

    def _fake_load_source(
        _path: str, _sheet: str, *, key_mismatch: str = "prompt", **_kwargs: object
    ) -> pd.DataFrame:
        recorder.le_calls.append(key_mismatch)
        return pd.DataFrame({"KEY": ["k1"]})

    def _fake_load_aop(
        _path: str,
        *,
        sheet: str = "AOP1",
        key_mismatch: str = "prompt",
        **_kwargs: object,
    ) -> pd.DataFrame:
        recorder.aop_calls.append(key_mismatch)
        return pd.DataFrame({"KEY": ["k1"]})

    def _fake_load_skulu(_path: str, *, sheet: str = "SKU_LU") -> pd.DataFrame:
        return pd.DataFrame({"SKU": ["s1"]})

    def _passthrough_normalize(source: pd.DataFrame) -> pd.DataFrame:
        # The LE import calls normalize/validate_tieouts after load_source; stub
        # them to pass-through so the seam test exercises only the policy
        # forwarding, not the LE transform math.
        return source

    def _noop_validate(_source: pd.DataFrame, _output: pd.DataFrame) -> None:
        return None

    monkeypatch.setattr("src.normalize_le.load_source", _fake_load_source)
    monkeypatch.setattr("src.normalize_le.normalize", _passthrough_normalize)
    monkeypatch.setattr("src.normalize_le.validate_tieouts", _noop_validate)
    monkeypatch.setattr("src.load_aop.load_aop", _fake_load_aop)
    monkeypatch.setattr("src.load_skulu.load_skulu", _fake_load_skulu)


def _no_stdin(monkeypatch: pytest.MonkeyPatch, recorder: _LoaderRecorder) -> None:
    """Patch the built-in ``input`` so any stdin read fails the test.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        recorder: The recorder whose ``stdin_reached`` flag is set on any call.

    Returns:
        ``None``.
    """

    def _input(_prompt: str = "") -> str:
        recorder.stdin_reached = True
        raise AssertionError("real stdin input() was reached in a GUI session")

    monkeypatch.setattr("builtins.input", _input)


def _spec() -> ImportSpec:
    """Return a trivial import spec for the seam tests."""
    return ImportSpec(
        le_path="le.xlsx",
        le_sheet="Sheet1",
        aop_path="aop.xlsx",
        aop_sheet="AOP1",
        skulu_path="skulu.xlsx",
        skulu_sheet="Sheet1",
    )


def test_default_resolver_yields_trust_and_never_reaches_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default resolver forwards 'trust' to the loaders and never hits stdin.

    Observed through the loader-forwarding behavior (the public surface) rather
    than reaching into private state: a default-constructed service forwards the
    "trust" ("Keep existing") policy to both LE and AOP, and no real stdin
    input() is consulted (AC-1).
    """
    # Arrange
    recorder = _LoaderRecorder()
    _install_recording_loaders(monkeypatch, recorder)
    _no_stdin(monkeypatch, recorder)
    service = PipelineService()

    # Act: import all sources through the default resolver.
    service.import_sources(_spec())

    # Assert: the loaders received the trust policy and no stdin was consulted.
    assert recorder.le_calls == ["trust"]
    assert recorder.aop_calls == ["trust"]
    assert recorder.stdin_reached is False


@pytest.mark.parametrize(
    ("selection", "expected_policy"),
    [
        ("Keep existing", "trust"),
        ("Rebuild", "overwrite"),
    ],
)
def test_injected_resolver_maps_selection_to_aop_policy(
    monkeypatch: pytest.MonkeyPatch, selection: str, expected_policy: str
) -> None:
    """An injected resolver maps the dialog selection to the AOP loader policy.

    "Keep existing" -> trust and "Rebuild" -> overwrite, forwarded to the AOP
    loader, with no stdin consulted (AC-1, AC-2 AOP half).
    """
    # Arrange: a resolver mapping the dialog selection to a loader policy.
    recorder = _LoaderRecorder()
    _install_recording_loaders(monkeypatch, recorder)
    _no_stdin(monkeypatch, recorder)
    policy_for = {"Keep existing": "trust", "Rebuild": "overwrite"}
    service = PipelineService(key_mismatch_resolver=lambda: policy_for[selection])

    # Act
    service.import_aop("aop.xlsx", "AOP1")

    # Assert: the AOP loader received the mapped policy and stdin was untouched.
    assert recorder.aop_calls == [expected_policy]
    assert recorder.stdin_reached is False


@pytest.mark.parametrize(
    ("selection", "expected_policy"),
    [
        ("Keep existing", "trust"),
        ("Rebuild", "overwrite"),
    ],
)
def test_injected_resolver_maps_selection_to_le_policy(
    monkeypatch: pytest.MonkeyPatch, selection: str, expected_policy: str
) -> None:
    """An injected resolver maps the dialog selection to the LE loader policy (AC-3).

    The LE path receives the same dialog-based handling as AOP and never reaches
    stdin.
    """
    # Arrange
    recorder = _LoaderRecorder()
    _install_recording_loaders(monkeypatch, recorder)
    _no_stdin(monkeypatch, recorder)
    policy_for = {"Keep existing": "trust", "Rebuild": "overwrite"}
    service = PipelineService(key_mismatch_resolver=lambda: policy_for[selection])

    # Act
    service.import_le("le.xlsx", "Sheet1")

    # Assert: the LE loader received the mapped policy and stdin was untouched.
    assert recorder.le_calls == [expected_policy]
    assert recorder.stdin_reached is False


def test_default_key_mismatch_resolver_returns_trust() -> None:
    """The default resolver returns the 'trust' ("Keep existing") policy."""
    # Act / Assert
    assert default_key_mismatch_resolver() == "trust"


def test_never_tty_returns_false() -> None:
    """The is_tty seam reports a non-interactive stdin so loaders never prompt."""
    # Act / Assert
    assert never_tty() is False


def test_no_stdin_prompt_raises() -> None:
    """The prompt seam fails fast if the interactive path is ever reached."""
    import pytest

    # Act / Assert: reaching the prompt seam is a defect in a GUI session.
    with pytest.raises(RuntimeError, match="reached stdin in a GUI session"):
        no_stdin_prompt("would you like to trust?")
