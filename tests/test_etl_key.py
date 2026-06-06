"""Tests for KEY derivation and reconciliation (:mod:`src.etl_key`).

Covers the pure ``decide_key_action`` decision seam and ``resolve_key`` KEY
establishment (absent -> created; present-and-matching -> trusted;
present-and-diverging -> trust/overwrite/prompt resolution; non-TTY prompt ->
fail fast). Interactivity is injected via ``is_tty``/``prompt`` collaborators so
no real stdin is touched. All Excel fixtures are in-memory; no temporary files
are created on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from src import etl_key
from src.normalize_le import (
    SOURCE_COLUMNS,
    decide_key_action,
    load_source,
    resolve_key,
)
from tests.le_fixtures import (
    build_workbook,
    loaded_frame,
    make_row,
    source_header_without_key,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

# Reach into the module for the private example collector via
# ``vars(module)[name]`` so neither Pyright (reportPrivateUsage) nor Ruff flags
# the access. The cast documents the callable's signature for the test code.
_collect_diverging_examples = cast(
    "Callable[[list[str], list[str]], list[tuple[str, str]]]",
    vars(etl_key)["_collect_diverging_examples"],
)

# ---------------------------------------------------------------------------
# decide_key_action (pure decision seam)
# ---------------------------------------------------------------------------


def _unused_prompt(_message: str) -> str:
    """A prompt callable that fails if invoked (asserts no-prompt paths)."""
    raise AssertionError("prompt should not be invoked")


@pytest.mark.parametrize("policy", ["trust", "overwrite"])
def test_decide_key_action_direct_policy_returns_policy(policy: str) -> None:
    """A direct trust/overwrite policy returns itself without prompting."""
    # Act
    result = decide_key_action(policy, is_tty=False, prompt=_unused_prompt)

    # Assert
    assert result == policy


def test_decide_key_action_prompt_non_tty_raises_with_guidance() -> None:
    """A non-interactive prompt fails fast naming the --key-mismatch remedy."""
    # Act / Assert
    with pytest.raises(ValueError, match="--key-mismatch"):
        decide_key_action("prompt", is_tty=False, prompt=_unused_prompt)


@pytest.mark.parametrize("answer", ["trust", "overwrite"])
def test_decide_key_action_prompt_tty_returns_user_choice(answer: str) -> None:
    """An interactive prompt returns the user's trust/overwrite choice."""
    # Arrange
    replies = [answer]

    def _prompt(_message: str) -> str:
        return replies.pop(0)

    # Act
    result = decide_key_action("prompt", is_tty=True, prompt=_prompt)

    # Assert
    assert result == answer


def test_decide_key_action_prompt_retries_until_valid_answer() -> None:
    """An interactive prompt re-asks until the user gives an accepted answer."""
    # Arrange: first an invalid reply, then a valid one.
    replies = ["maybe", "OVERWRITE"]

    def _prompt(_message: str) -> str:
        return replies.pop(0)

    # Act
    result = decide_key_action("prompt", is_tty=True, prompt=_prompt)

    # Assert: the second (valid) reply resolves, case-insensitively.
    assert result == "overwrite"
    assert replies == []


def test_decide_key_action_unknown_policy_raises() -> None:
    """An unrecognized policy value raises ValueError."""
    # Act / Assert
    with pytest.raises(ValueError, match="Unknown"):
        decide_key_action("bogus", is_tty=True, prompt=_unused_prompt)


# ---------------------------------------------------------------------------
# resolve_key (KEY establishment on a resolved frame)
# ---------------------------------------------------------------------------


def _frame_without_key() -> pd.DataFrame:
    """Load a single-row frame from a source workbook that has no KEY column."""
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    buffer = build_workbook(rows, header=source_header_without_key())
    return load_source(buffer, "LE-8 + 4")


def test_resolve_key_absent_creates_from_pattern() -> None:
    """When the source has no KEY column, KEY is created from the pattern."""
    # Act
    frame = _frame_without_key()

    # Assert
    assert frame.iloc[0]["KEY"] == "CustA5GS"


def test_resolve_key_present_matching_is_trusted() -> None:
    """A present KEY whose values match the rebuilt pattern is trusted."""
    # Arrange: the workbook KEY equals the rebuilt pattern exactly.
    rows = [
        make_row(
            customer="CustA",
            sku=5,
            type_="GS",
            ppg="PX",
            months=[1.0] * 12,
            key="CustA5GS",
        )
    ]
    buffer = build_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    frame = load_source(buffer, "LE-8 + 4")

    # Assert
    assert frame.iloc[0]["KEY"] == "CustA5GS"


def test_resolve_key_present_diverging_trust_keeps_existing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A diverging KEY under 'trust' keeps existing values and warns."""
    # Arrange: a resolved frame whose KEY is forced to diverge from the pattern.
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    base = loaded_frame(rows)
    base["KEY"] = ["LEGACY_KEY"]

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        result = resolve_key(base, "trust", has_key_column=True, is_tty=lambda: False)

    # Assert
    assert result.iloc[0]["KEY"] == "LEGACY_KEY"
    assert any("trust" in record.message.lower() for record in caplog.records)


def test_resolve_key_present_diverging_overwrite_replaces(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A diverging KEY under 'overwrite' is replaced and warns."""
    # Arrange
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    base = loaded_frame(rows)
    base["KEY"] = ["LEGACY_KEY"]

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        result = resolve_key(
            base, "overwrite", has_key_column=True, is_tty=lambda: False
        )

    # Assert
    assert result.iloc[0]["KEY"] == "CustA5GS"
    assert any("overwrit" in record.message.lower() for record in caplog.records)


def test_resolve_key_present_diverging_prompt_non_tty_raises() -> None:
    """A diverging KEY under non-interactive 'prompt' fails fast."""
    # Arrange
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    base = loaded_frame(rows)
    base["KEY"] = ["LEGACY_KEY"]

    # Act / Assert
    with pytest.raises(ValueError, match="--key-mismatch"):
        resolve_key(base, "prompt", has_key_column=True, is_tty=lambda: False)


def test_resolve_key_present_diverging_prompt_tty_overwrite() -> None:
    """A diverging KEY under interactive 'prompt' honors the user's choice."""
    # Arrange
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    base = loaded_frame(rows)
    base["KEY"] = ["LEGACY_KEY"]

    # Act: simulate an interactive user choosing overwrite.
    result = resolve_key(
        base,
        "prompt",
        has_key_column=True,
        is_tty=lambda: True,
        prompt=lambda _message: "overwrite",
    )

    # Assert
    assert result.iloc[0]["KEY"] == "CustA5GS"


# ---------------------------------------------------------------------------
# _collect_diverging_examples (pure example collector, issue #52 / AC-2)
# ---------------------------------------------------------------------------


def test_collect_diverging_examples_returns_only_diverging_pairs_in_order() -> None:
    """Only positions where existing != rebuilt are returned, in index order."""
    # Arrange: indices 1 and 3 diverge; 0 and 2 match.
    existing = ["same0", "old1", "same2", "old3"]
    rebuilt = ["same0", "new1", "same2", "new3"]

    # Act
    pairs = _collect_diverging_examples(existing, rebuilt)

    # Assert: each pair carries (existing, rebuilt) for the diverging index only.
    assert pairs == [("old1", "new1"), ("old3", "new3")]


def test_collect_diverging_examples_truncates_to_limit_of_three() -> None:
    """At most three example pairs are collected even when more rows diverge."""
    # Arrange: five diverging rows; the default limit is three.
    existing = [f"old{i}" for i in range(5)]
    rebuilt = [f"new{i}" for i in range(5)]

    # Act
    pairs = _collect_diverging_examples(existing, rebuilt)

    # Assert: only the first three diverging pairs are returned, in order.
    assert pairs == [("old0", "new0"), ("old1", "new1"), ("old2", "new2")]


def test_collect_diverging_examples_empty_when_identical() -> None:
    """No pairs are returned when the two lists are identical."""
    # Arrange / Act
    pairs = _collect_diverging_examples(["a", "b"], ["a", "b"])

    # Assert
    assert pairs == []


# ---------------------------------------------------------------------------
# resolve_key with an injected example-aware resolver (issue #52 / AC-5/AC-6)
# ---------------------------------------------------------------------------


class _RecordingResolver:
    """Records the example pairs it receives and returns a fixed action.

    Purpose:
        Stand in for the GUI example-aware resolver so tests can assert both the
        exact example pairs forwarded and that the resolver is invoked only on a
        genuine divergence.

    Attributes:
        action: The action string returned on every call.
        calls: The example-pair lists received, one entry per invocation.
    """

    def __init__(self, action: str) -> None:
        """Initialize with the action to return and an empty call log."""
        self.action = action
        self.calls: list[list[tuple[str, str]]] = []

    def __call__(self, examples: list[tuple[str, str]]) -> str:
        """Record the examples and return the configured action."""
        self.calls.append(examples)
        return self.action


def _diverging_two_row_frame() -> pd.DataFrame:
    """Return a two-row loaded frame whose KEY diverges from the pattern."""
    rows = [
        make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12),
        make_row(customer="CustB", sku=7, type_="GS", ppg="PY", months=[2.0] * 12),
    ]
    base = loaded_frame(rows)
    base["KEY"] = ["LEGACY_A", "LEGACY_B"]
    return base


def test_resolve_key_invokes_resolver_only_on_divergence_with_examples() -> None:
    """The injected resolver is invoked on divergence with the exact pairs."""
    # Arrange: a frame whose two KEY values both diverge from the pattern.
    base = _diverging_two_row_frame()
    resolver = _RecordingResolver("trust")

    # Act
    resolve_key(base, "prompt", has_key_column=True, resolver=resolver)

    # Assert: invoked once, with the (existing, rebuilt) pairs for both rows.
    assert resolver.calls == [[("LEGACY_A", "CustA5GS"), ("LEGACY_B", "CustB7GS")]]


def test_resolve_key_resolver_trust_keeps_existing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A resolver returning 'trust' keeps existing KEY values and warns."""
    # Arrange
    base = _diverging_two_row_frame()
    resolver = _RecordingResolver("trust")

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        result = resolve_key(base, "prompt", has_key_column=True, resolver=resolver)

    # Assert
    assert list(result["KEY"]) == ["LEGACY_A", "LEGACY_B"]
    assert any("trust" in record.message.lower() for record in caplog.records)


def test_resolve_key_resolver_overwrite_replaces(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A resolver returning 'overwrite' replaces KEY with the pattern and warns."""
    # Arrange
    base = _diverging_two_row_frame()
    resolver = _RecordingResolver("overwrite")

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        result = resolve_key(base, "prompt", has_key_column=True, resolver=resolver)

    # Assert
    assert list(result["KEY"]) == ["CustA5GS", "CustB7GS"]
    assert any("overwrit" in record.message.lower() for record in caplog.records)


def test_resolve_key_resolver_not_invoked_when_matching() -> None:
    """The resolver is not invoked when the KEY matches the rebuilt pattern."""
    # Arrange: a frame whose KEY already equals the rebuilt pattern.
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    base = loaded_frame(rows)
    base["KEY"] = ["CustA5GS"]
    resolver = _RecordingResolver("overwrite")

    # Act
    result = resolve_key(base, "prompt", has_key_column=True, resolver=resolver)

    # Assert: matching KEY is trusted as-is; the resolver was never consulted.
    assert result.iloc[0]["KEY"] == "CustA5GS"
    assert resolver.calls == []


def test_resolve_key_resolver_not_invoked_when_no_key_column() -> None:
    """The resolver is not invoked when there is no source KEY column."""
    # Arrange: a frame with no source KEY column (created from the pattern).
    rows = [make_row(customer="CustA", sku=5, type_="GS", ppg="PX", months=[1.0] * 12)]
    base = loaded_frame(rows)
    resolver = _RecordingResolver("overwrite")

    # Act
    result = resolve_key(base, "prompt", has_key_column=False, resolver=resolver)

    # Assert: KEY is created from the pattern; the resolver was never consulted.
    assert result.iloc[0]["KEY"] == "CustA5GS"
    assert resolver.calls == []


def test_resolve_key_resolver_none_preserves_cli_path(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """With resolver=None the CLI policy/stdin path is unchanged (AC-6)."""
    # Arrange: a diverging frame resolved via the policy path (no resolver).
    base = _diverging_two_row_frame()

    # Act: the trust policy via the CLI path keeps existing values and warns.
    with caplog.at_level("WARNING", logger="src.etl_key"):
        result = resolve_key(
            base, "trust", has_key_column=True, is_tty=lambda: False, resolver=None
        )

    # Assert
    assert list(result["KEY"]) == ["LEGACY_A", "LEGACY_B"]
    assert any("trust" in record.message.lower() for record in caplog.records)
