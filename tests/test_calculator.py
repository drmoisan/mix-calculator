"""Tests for :mod:`src.calculator`."""

import pytest

from src.calculator import mix_ratio


def test_mix_ratio_returns_fraction() -> None:
    """It returns the part divided by the total."""
    assert mix_ratio(1.0, 4.0) == 0.25


def test_mix_ratio_rejects_non_positive_total() -> None:
    """It raises ``ValueError`` when the total is not positive."""
    with pytest.raises(ValueError, match="greater than zero"):
        mix_ratio(1.0, 0.0)
