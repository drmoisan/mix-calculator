"""Tests for KEY derivation and reconciliation (:mod:`src.etl_key`).

Covers the pure ``decide_key_action`` decision seam and ``resolve_key`` KEY
establishment (absent -> created; present-and-matching -> trusted;
present-and-diverging -> trust/overwrite/prompt resolution; non-TTY prompt ->
fail fast). Interactivity is injected via ``is_tty``/``prompt`` collaborators so
no real stdin is touched. All Excel fixtures are in-memory; no temporary files
are created on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

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
    import pandas as pd

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
