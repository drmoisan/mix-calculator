"""KEY-mismatch resolver-forwarding tests for :class:`PipelineService` (#52).

Verifies the constructor-injectable ``key_mismatch_resolver`` seam under the
example-aware contract (issue #52): ``import_le`` and ``import_aop`` forward the
resolver CALLABLE (not its result) to the loaders as the divergence-only
``resolver`` argument, so the resolver is invoked only when the loader reports a
genuine divergence and never eagerly on every import. The default resolver
yields ``"trust"`` ("Keep existing"). All loader reads are captured by recording
stand-ins; no real stdin or workbook I/O occurs (AC-3, AC-5; reinforces AC-6).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.gui import pipeline_service as pipeline_service_module
from src.gui._key_mismatch_seam import (
    default_key_mismatch_resolver,
    never_tty,
    no_stdin_prompt,
)
from src.gui.pipeline_service import ImportSpec, PipelineService

if TYPE_CHECKING:
    import pandas as pd


class _LoaderRecorder:
    """Records the resolver callable each loader receives.

    Purpose:
        Prove the service forwards the resolver CALLABLE (not its result) and the
        no-stdin seams to the LE and AOP loaders without performing any real
        workbook or stdin I/O, and that the resolver is not invoked when the
        loader reports no divergence.

    Attributes:
        le_resolvers: Each LE-loader ``resolver`` value, in call order.
        aop_resolvers: Each AOP-loader ``resolver`` value, in call order.
        stdin_reached: Whether any loader invoked the injected prompt seam.
    """

    def __init__(self) -> None:
        """Initialize with no recorded calls."""
        self.le_resolvers: list[object] = []
        self.aop_resolvers: list[object] = []
        self.stdin_reached = False


def _install_recording_loaders(
    monkeypatch: pytest.MonkeyPatch, recorder: _LoaderRecorder
) -> None:
    """Patch the LE/AOP/SKU_LU loaders to record the resolver and return frames.

    The recording loaders model the no-divergence path: they capture the
    forwarded ``resolver`` but never invoke it, mirroring a loader whose source
    KEY matches the rebuilt pattern (so the resolver/dialog must not fire).

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        recorder: The recorder capturing each loader's ``resolver`` value.

    Returns:
        ``None``.

    Side effects:
        Replaces ``src.normalize_le.load_source``, ``src.load_aop.load_aop``, and
        ``src.load_skulu.load_skulu`` with recording stand-ins.
    """
    import pandas as pd

    def _fake_load_source(
        _path: str,
        _sheet: str,
        *,
        resolver: object = None,
        **_kwargs: object,
    ) -> pd.DataFrame:
        recorder.le_resolvers.append(resolver)
        return pd.DataFrame({"KEY": ["k1"]})

    def _fake_load_aop(
        _path: str,
        *,
        sheet: str = "AOP1",
        resolver: object = None,
        **_kwargs: object,
    ) -> pd.DataFrame:
        recorder.aop_resolvers.append(resolver)
        return pd.DataFrame({"KEY": ["k1"]})

    def _fake_load_skulu(_path: str, *, sheet: str = "SKU_LU") -> pd.DataFrame:
        return pd.DataFrame({"SKU": ["s1"]})

    def _passthrough_normalize(source: pd.DataFrame) -> pd.DataFrame:
        # The LE import calls normalize/validate_tieouts after load_source; stub
        # them to pass-through so the seam test exercises only the resolver
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


class _RecordingResolver:
    """An example-aware resolver that records every invocation.

    Purpose:
        Let a test assert both that the service forwards this exact object as the
        loaders' ``resolver`` and that the loaders do not invoke it on a
        no-divergence path (call count stays zero).

    Attributes:
        action: The action string returned when invoked.
        calls: The example-pair lists received, one entry per invocation.
    """

    def __init__(self, action: str = "trust") -> None:
        """Initialize with the action to return and an empty call log."""
        self.action = action
        self.calls: list[list[tuple[str, str]]] = []

    def __call__(self, examples: list[tuple[str, str]]) -> str:
        """Record the examples and return the configured action."""
        self.calls.append(examples)
        return self.action


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


def test_default_resolver_forwarded_as_callable_and_never_reaches_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The default resolver is forwarded as a callable and stdin is untouched.

    A default-constructed service forwards the
    :func:`default_key_mismatch_resolver` CALLABLE (its result is not eagerly
    computed) to both LE and AOP, and no real stdin input() is consulted (AC-5,
    AC-6).
    """
    # Arrange
    recorder = _LoaderRecorder()
    _install_recording_loaders(monkeypatch, recorder)
    _no_stdin(monkeypatch, recorder)
    service = PipelineService()

    # Act: import all sources through the default resolver.
    service.import_sources(_spec())

    # Assert: the loaders received the resolver callable itself (the function
    # object), not its "trust" result, and no stdin was consulted.
    assert recorder.le_resolvers == [default_key_mismatch_resolver]
    assert recorder.aop_resolvers == [default_key_mismatch_resolver]
    assert recorder.stdin_reached is False


def test_import_le_forwards_injected_resolver_callable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_le forwards the injected resolver object as the loader's resolver."""
    # Arrange
    recorder = _LoaderRecorder()
    _install_recording_loaders(monkeypatch, recorder)
    _no_stdin(monkeypatch, recorder)
    resolver = _RecordingResolver()
    service = PipelineService(key_mismatch_resolver=resolver)

    # Act
    service.import_le("le.xlsx", "Sheet1")

    # Assert: the LE loader received the same resolver object (not its result),
    # the resolver was NOT invoked on this no-divergence path, and stdin was
    # untouched.
    assert recorder.le_resolvers == [resolver]
    assert resolver.calls == []
    assert recorder.stdin_reached is False


def test_import_aop_forwards_injected_resolver_callable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """import_aop forwards the injected resolver object as the loader's resolver."""
    # Arrange
    recorder = _LoaderRecorder()
    _install_recording_loaders(monkeypatch, recorder)
    _no_stdin(monkeypatch, recorder)
    resolver = _RecordingResolver()
    service = PipelineService(key_mismatch_resolver=resolver)

    # Act
    service.import_aop("aop.xlsx", "AOP1")

    # Assert: the AOP loader received the same resolver object (not its result),
    # the resolver was NOT invoked on this no-divergence path, and stdin was
    # untouched.
    assert recorder.aop_resolvers == [resolver]
    assert resolver.calls == []
    assert recorder.stdin_reached is False


def test_resolver_module_import_location_is_patchable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The loaders are patchable at their import location in pipeline_service.

    Documents that ``normalize_le`` and ``load_aop`` are imported into the
    service module so tests patch them where used; this guards the forwarding
    tests above against silently patching the wrong symbol.
    """
    # Arrange / Assert: the service module references both loader modules.
    assert hasattr(pipeline_service_module, "normalize_le")
    assert hasattr(pipeline_service_module, "load_aop")


def test_default_key_mismatch_resolver_returns_trust() -> None:
    """The default resolver returns the 'trust' ("Keep existing") policy."""
    # Act / Assert: the example-aware default ignores its examples and trusts.
    assert default_key_mismatch_resolver([("old", "new")]) == "trust"


def test_never_tty_returns_false() -> None:
    """The is_tty seam reports a non-interactive stdin so loaders never prompt."""
    # Act / Assert
    assert never_tty() is False


def test_no_stdin_prompt_raises() -> None:
    """The prompt seam fails fast if the interactive path is ever reached."""
    # Act / Assert: reaching the prompt seam is a defect in a GUI session.
    with pytest.raises(RuntimeError, match="reached stdin in a GUI session"):
        no_stdin_prompt("would you like to trust?")
