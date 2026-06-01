"""KEY-reconcile branch tests for the AOP loader (split from test_load_aop.py).

Covers the create / trust / overwrite / non-TTY-prompt branches of the AOP
wiring of ``resolve_key``. Split into its own module so neither file exceeds the
repository's 500-line cap. All fixtures are in-memory; no temp files, no real
stdin.
"""

from __future__ import annotations

import pytest

from src.load_aop import SOURCE_COLUMNS, load_aop
from tests.aop_fixtures import build_aop_workbook, loaded_aop_frame, make_aop_row


def test_key_absent_create_branch() -> None:
    """With no KEY column, KEY is created from the rebuilt pattern."""
    # Arrange / Act
    frame = loaded_aop_frame(
        [make_aop_row(customer="Cust", sku=7, type_="GS", months=[1.0] * 12)]
    )

    # Assert
    assert frame.iloc[0]["KEY"] == "Cust7GS"


def test_key_present_matching_trust_branch() -> None:
    """A present KEY equal to the rebuilt pattern is trusted as-is."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="Cust7GS"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    frame = load_aop(buffer, sheet="AOP1")

    # Assert
    assert frame.iloc[0]["KEY"] == "Cust7GS"


def test_key_diverging_trust_branch_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A diverging KEY under 'trust' keeps the existing value and warns."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="LEGACY"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        frame = load_aop(buffer, sheet="AOP1", key_mismatch="trust")

    # Assert
    assert frame.iloc[0]["KEY"] == "LEGACY"
    assert any("trust" in r.message.lower() for r in caplog.records)


def test_key_diverging_overwrite_branch_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A diverging KEY under 'overwrite' is replaced and warns."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="LEGACY"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act
    with caplog.at_level("WARNING", logger="src.etl_key"):
        frame = load_aop(buffer, sheet="AOP1", key_mismatch="overwrite")

    # Assert
    assert frame.iloc[0]["KEY"] == "Cust7GS"
    assert any("overwrit" in r.message.lower() for r in caplog.records)


def test_key_diverging_prompt_non_tty_raises() -> None:
    """A diverging KEY under default 'prompt' on non-TTY stdin raises ValueError."""
    # Arrange
    rows = [
        make_aop_row(
            customer="Cust", sku=7, type_="GS", months=[1.0] * 12, key="LEGACY"
        )
    ]
    buffer = build_aop_workbook(rows, header=SOURCE_COLUMNS)

    # Act / Assert: non-interactive prompt fails fast naming the remedy flag.
    with pytest.raises(ValueError, match="--key-mismatch"):
        load_aop(buffer, sheet="AOP1", key_mismatch="prompt", is_tty=lambda: False)
