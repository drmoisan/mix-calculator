"""Pure arithmetic primitives for the BottomsUp mix builders.

This module holds the side-effect-free helpers shared by the three BottomsUp
builders in :mod:`src.mix_bottomsup`, so that module stays under the 500-line
file limit. It depends only on ``numpy`` and ``pandas`` and imports nothing from
:mod:`src.mix_bottomsup`, so the builders can import these primitives without an
import cycle.

Primitives provided:
    - ``classify_from_lbs``: re-derive the Classification token from an aggregated
      ``Lbs - AOP`` / ``Lbs - LE`` pair using the Excel zero-test (used by the
      category and customer builders, whose Classification is not sourced upstream).
    - ``build_contribution_columns``: append the eight derived BottomsUp columns
      (Share - AOP/LE, Share Shift, Mix Rate, New/Disco/Normal Contribution, and
      SKU Mix) that are arithmetically identical across all three tables.

All column names and classification labels here are schema, not secret; only the
source data values are confidential and never appear in this module.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = ["build_contribution_columns", "classify_from_lbs"]


def classify_from_lbs(lbs_aop: float, lbs_le: float) -> str:
    """Re-derive the Classification token from aggregated AOP/LE Lbs.

    Reproduces the Excel ``L``/``K`` column zero-test used by the category and
    customer BottomsUp tabs, where Classification is not carried from an upstream
    table but recomputed from the group-summed ``Lbs - AOP`` / ``Lbs - LE`` pair.
    The ``"new"`` SKU-level token does not appear at this level; a zero-AOP /
    nonzero-LE group maps to ``"new distribution"`` per the same formula.

    Args:
        lbs_aop: The aggregated ``Lbs - AOP`` for the group. Compared exactly
            against ``0`` to match the Excel zero-test.
        lbs_le: The aggregated ``Lbs - LE`` for the group, compared exactly
            against ``0``.

    Returns:
        One of the lowercase tokens ``"eliminated"``, ``"new distribution"``,
        ``"lost distribution"``, or ``"normal"``.
    """
    # The four-branch routing table on the (AOP-zero, LE-zero) combination:
    #   AOP == 0 and LE == 0 -> "eliminated"      (no volume in either scenario)
    #   AOP == 0 and LE != 0 -> "new distribution" (volume appears only in LE)
    #   AOP != 0 and LE == 0 -> "lost distribution" (volume disappears by LE)
    #   AOP != 0 and LE != 0 -> "normal"           (volume in both scenarios)
    # The AOP-zero test is the outer discriminator because the new/eliminated
    # split is meaningful only when the AOP volume is absent.
    if lbs_aop == 0:
        return "eliminated" if lbs_le == 0 else "new distribution"
    return "lost distribution" if lbs_le == 0 else "normal"


# The lowercase Classification labels the contribution branches match against.
# Matching is case-sensitive against exactly these literals (the pipeline emits
# lowercase only); a case mismatch would silently route a row to the wrong branch.
_NEW_LABELS: frozenset[str] = frozenset({"new", "new distribution"})
_DISCO_LABELS: frozenset[str] = frozenset({"lost distribution", "eliminated"})
_NORMAL_LABEL: str = "normal"


def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    """Divide two series element-wise, returning 0.0 where the denominator is 0.

    Mirrors the ``_safe_div`` guard in :mod:`src._mix_transforms_helpers`: the
    BottomsUp share columns reproduce the Excel ``IF(denominator, num/den, 0)``
    pattern, so a zero denominator must yield ``0.0`` rather than ``NaN``/``inf``,
    which would otherwise pollute downstream sums and tie-outs.

    Args:
        num: The numerator series.
        den: The denominator series, aligned to ``num``.

    Returns:
        A float ``pd.Series`` aligned to ``num.index`` holding ``num / den`` where
        ``den != 0`` and ``0.0`` elsewhere.
    """
    # Compute the quotient under a nonzero-denominator mask so a zero denominator
    # yields 0.0. numpy.where evaluates both branches, so the division is wrapped
    # in an errstate that silences the harmless divide-by-zero warning the
    # masked-out quotient would otherwise emit.
    numerator = num.to_numpy()
    denominator = den.to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        quotient = np.where(denominator != 0, numerator / denominator, 0.0)
    return pd.Series(quotient, index=num.index, dtype="float64")


def build_contribution_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Append the eight derived BottomsUp columns to a prepared frame.

    Computes the share, share-shift, mix-rate, three classification-conditional
    contributions, and the ``SKU Mix`` total that are arithmetically identical
    across ``mix_2_sku_bottomsup``, ``mix_3_category_bottomsup``, and
    ``mix_4_customer_bottomsup``. The input frame must already carry the columns
    the formulas read: ``Classification``, ``Lbs - AOP``, ``Lbs - LE``,
    ``Net Rev Per Lb - AOP``, ``Net Rev Per Lb - LE``, ``Blended Rate - AOP``,
    ``Blended Rate - LE``, ``Lbs Subtotal - AOP``, and ``Lbs Subtotal - LE``.

    The function does not mutate its input; it returns a copy with the new columns
    appended. Every division is guarded to ``0.0`` via ``_safe_div`` (Excel ``IF``
    guard parity), and the conditional contributions use ``numpy.where`` so the
    inactive branches are exactly ``0.0``. ``SKU Mix`` is the sum of the three
    contribution columns, which makes the identity
    ``SKU Mix == New + Disco + Normal`` hold for every row.

    Args:
        frame: A prepared BottomsUp frame carrying the input columns listed above.
            Not mutated.

    Returns:
        A new DataFrame equal to ``frame`` with these eight columns appended in
        order: ``Share - AOP``, ``Share - LE``, ``Share Shift``, ``Mix Rate``,
        ``New Contribution``, ``Disco Contribution``, ``Normal Contribution``, and
        ``SKU Mix``.
    """
    # Work on a copy so the caller's frame is never mutated (pure-transform
    # contract); all derived columns are assigned onto this result.
    result = frame.copy()

    # Share columns reproduce Excel IF(subtotal, Lbs/subtotal, 0): the row's share
    # of its rollup group's Lbs, guarded to 0 when the subtotal is 0.
    result["Share - AOP"] = _safe_div(result["Lbs - AOP"], result["Lbs Subtotal - AOP"])
    result["Share - LE"] = _safe_div(result["Lbs - LE"], result["Lbs Subtotal - LE"])

    # Share Shift is the LE-minus-AOP movement in the row's mix share; Mix Rate is
    # the AOP per-Lb rate relative to the group blended rate.
    result["Share Shift"] = result["Share - LE"] - result["Share - AOP"]
    result["Mix Rate"] = result["Net Rev Per Lb - AOP"] - result["Blended Rate - AOP"]

    # Pre-compute the three classification masks once. Matching is case-sensitive
    # against the lowercase tokens; isin keeps the comparison vectorized.
    classification = result["Classification"]
    is_new = classification.isin(_NEW_LABELS).to_numpy()
    is_disco = classification.isin(_DISCO_LABELS).to_numpy()
    is_normal = (classification == _NORMAL_LABEL).to_numpy()

    # New Contribution applies only to new-distribution rows with a nonzero AOP
    # blended rate: the LE-rate-versus-AOP-rate gap scaled by LE volume. The
    # double guard (classification AND Blended Rate - AOP != 0) matches the Excel
    # IF; both branches of numpy.where are evaluated, so the masked-out rows are 0.
    blended_rate_aop = result["Blended Rate - AOP"].to_numpy()
    new_value = (result["Net Rev Per Lb - LE"].to_numpy() - blended_rate_aop) * result[
        "Lbs - LE"
    ].to_numpy()
    result["New Contribution"] = np.where(
        is_new & (blended_rate_aop != 0), new_value, 0.0
    )

    # Disco Contribution applies only to lost/eliminated rows with a nonzero AOP
    # subtotal: the negated AOP rate gap scaled by AOP volume and the LE/AOP
    # subtotal ratio. The subtotal guard avoids a divide-by-zero in the ratio.
    lbs_subtotal_aop = result["Lbs Subtotal - AOP"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        subtotal_ratio = np.where(
            lbs_subtotal_aop != 0,
            result["Lbs Subtotal - LE"].to_numpy() / lbs_subtotal_aop,
            0.0,
        )
    disco_value = (
        -(result["Net Rev Per Lb - AOP"].to_numpy() - blended_rate_aop)
        * result["Lbs - AOP"].to_numpy()
        * subtotal_ratio
    )
    result["Disco Contribution"] = np.where(
        is_disco & (lbs_subtotal_aop != 0), disco_value, 0.0
    )

    # Normal Contribution applies only to normal rows: the share shift times the
    # mix rate times the LE subtotal (the mix-driven net revenue movement).
    normal_value = (
        result["Share Shift"].to_numpy()
        * result["Mix Rate"].to_numpy()
        * result["Lbs Subtotal - LE"].to_numpy()
    )
    result["Normal Contribution"] = np.where(is_normal, normal_value, 0.0)

    # SKU Mix is the total of the three mutually-exclusive contribution branches;
    # this sum makes the SKU Mix == New + Disco + Normal identity hold per row.
    result["SKU Mix"] = (
        result["New Contribution"]
        + result["Disco Contribution"]
        + result["Normal Contribution"]
    )

    return result
