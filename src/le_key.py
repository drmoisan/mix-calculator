"""Business-key derivation and KEY-column reconciliation for the LE ETL.

The LE source workbook stores ``KEY`` as an Excel formula (``=C&E&F``), so a
loaded cell may hold the formula text, a stale cached value, or ``None``. This
module rebuilds the canonical business key from its components and reconciles a
present-but-diverging source ``KEY`` column against the rebuilt pattern.

Responsibilities:
    - ``coerce_sku`` / ``rebuild_key``: pure helpers that render the key exactly
      as the Excel concatenation does.
    - ``decide_key_action``: the pure decision seam for a diverging ``KEY`` under
      the ``--key-mismatch`` policy; interactivity is injected (no real stdin).
    - ``resolve_key``: establishes the canonical ``KEY`` column on a resolved
      source frame (create / trust / resolve).

The interactive decision is injectable via ``is_tty`` and ``prompt`` collaborators
so tests drive every branch deterministically without touching real stdin.
"""

from __future__ import annotations

import logging
import math
import sys
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

logger = logging.getLogger(__name__)


def coerce_sku(val: object) -> str:
    """Render a SKU value the way the source Excel key formula does.

    Excel concatenates the SKU into the KEY without decimal noise: whole-number
    SKUs render as plain integer strings and non-numeric codes are preserved
    verbatim. openpyxl may return an ``int``, a ``float`` (whole or fractional),
    a ``numpy`` scalar, ``NaN`` for an empty cell, or a string code.

    Args:
        val: The raw SKU cell value loaded from the workbook. May be an ``int``,
            ``float``, ``numpy`` integer/float, ``NaN``, ``None``, or ``str``.

    Returns:
        The SKU rendered as a string. ``NaN``/``None`` render as the empty
        string; integral numeric values render with no decimal point; other
        floats render via ``str``; any other value renders via ``str``.
    """
    # Empty cells arrive as None; the Excel formula yields an empty segment.
    if val is None:
        return ""

    # Normalize numpy scalars to their Python equivalents up front so the
    # remaining branches operate only on built-in int/float/str types. The
    # numpy ``.item()`` accessor returns a concrete Python scalar.
    if isinstance(val, np.integer):
        val = int(val.item())
    elif isinstance(val, np.floating):
        val = float(val.item())

    # bool is a subclass of int; treat it as a generic value, not a number.
    if isinstance(val, bool):
        return str(val)

    # Branch ordering matters: integer-typed values render directly, while
    # float values render as an integer only when they have no fractional part
    # (mirroring how Excel concatenates a whole number without a decimal).
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        if math.isnan(val):
            return ""
        if val.is_integer():
            return str(int(val))
        return str(val)

    # Non-numeric codes (e.g. "RGFBOWLCB") are preserved exactly as supplied.
    return str(val)


def rebuild_key(customer: str, sku: object, type_: str) -> str:
    """Rebuild the business KEY from its component fields.

    The source workbook stores ``KEY`` as the Excel formula ``=C&E&F``
    (``Customer & SKU # & Type``) with no separator. openpyxl may return the
    formula text, a stale cached value, or ``None``, so the key is always
    rebuilt from components rather than trusting the loaded cell.

    Args:
        customer: The ``Customer`` text segment.
        sku: The raw ``SKU #`` value; rendered via :func:`coerce_sku`.
        type_: The ``Type`` text segment.

    Returns:
        The concatenation ``customer + coerce_sku(sku) + type_`` with no
        separator between segments.
    """
    return f"{customer}{coerce_sku(sku)}{type_}"


def _rebuilt_key_series(frame: pd.DataFrame) -> list[str]:
    """Rebuild the KEY pattern for every row of a canonical-named frame.

    Args:
        frame: A frame with canonical ``Customer``, ``SKU #``, and ``Type``
            columns.

    Returns:
        A list of rebuilt keys (``Customer + coerce_sku(SKU #) + Type``) aligned
        to ``frame``'s row order.
    """
    # Rebuild one key per row from its components; the loaded KEY cell (when any)
    # is never trusted blindly and is reconciled against this pattern.
    return [
        rebuild_key(str(customer), sku, str(type_))
        for customer, sku, type_ in zip(
            frame["Customer"], frame["SKU #"], frame["Type"], strict=True
        )
    ]


def decide_key_action(
    policy: str,
    *,
    is_tty: bool,
    prompt: Callable[[str], str],
) -> str:
    """Decide whether to trust or overwrite a diverging source ``KEY`` column.

    This is the pure decision seam for KEY-mismatch resolution. It contains no
    DataFrame logic and no real stdin access; the ``is_tty`` flag and ``prompt``
    callable are injected so tests drive every branch deterministically.

    Decision table:
        - ``trust`` / ``overwrite``: return the policy verbatim.
        - ``prompt`` on a TTY: ask the user via ``prompt`` until they answer
          ``trust`` or ``overwrite``.
        - ``prompt`` without a TTY: raise (automation must not block on input).

    Args:
        policy: The ``--key-mismatch`` policy: ``"trust"``, ``"overwrite"``, or
            ``"prompt"``.
        is_tty: Whether stdin is an interactive terminal.
        prompt: A callable that displays a message and returns the user's reply;
            invoked only on the interactive ``prompt`` path.

    Returns:
        Either ``"trust"`` or ``"overwrite"``.

    Raises:
        ValueError: When ``policy`` is ``"prompt"`` and ``is_tty`` is ``False``
            (the run must fail fast with guidance), or when ``policy`` is not one
            of the three accepted values.
    """
    # Direct policies need no interaction; return them as the resolved action.
    if policy in ("trust", "overwrite"):
        return policy

    if policy != "prompt":
        raise ValueError(f"Unknown --key-mismatch policy: {policy!r}.")

    # Non-interactive prompt must never block automation: fail fast with the
    # exact remedy the caller should apply.
    if not is_tty:
        raise ValueError(
            "KEY column diverges from the rebuilt pattern and --key-mismatch is "
            "'prompt', but stdin is not interactive. Re-run with "
            "--key-mismatch trust or --key-mismatch overwrite."
        )

    # Interactive path: keep asking until the user gives an accepted answer so a
    # typo does not silently fall through to a default action.
    while True:
        answer = (
            prompt(
                "Source KEY column diverges from the rebuilt pattern. "
                "Type 'trust' to keep existing KEY values or 'overwrite' to "
                "replace them: "
            )
            .strip()
            .lower()
        )
        if answer in ("trust", "overwrite"):
            return answer


def resolve_key(
    frame: pd.DataFrame,
    policy: str,
    *,
    has_key_column: bool,
    is_tty: Callable[[], bool] = sys.stdin.isatty,
    prompt: Callable[[str], str] = input,
) -> pd.DataFrame:
    """Establish the canonical ``KEY`` column on a resolved source frame.

    Operates on a frame that has already been resolved/renamed to canonical
    names and had blank-``Customer`` rows dropped. The rebuilt pattern is
    ``Customer + coerce_sku(SKU #) + Type`` per row.

    Branches:
        - No source KEY column: set ``KEY`` to the rebuilt pattern.
        - Source KEY present and every value equals the rebuilt pattern: keep
          (trust) the existing column.
        - Source KEY present but one or more values diverge: resolve per
          ``policy`` using :func:`decide_key_action` (``trust`` keeps existing
          values and logs a warning; ``overwrite`` replaces with the rebuilt
          pattern and logs a warning; non-interactive ``prompt`` raises).

    Args:
        frame: The canonical-named source frame (mutated in place and returned).
        policy: The ``--key-mismatch`` policy for a diverging KEY.
        has_key_column: Whether the source supplied a ``KEY`` column.
        is_tty: Callable returning whether stdin is interactive (injectable for
            tests; defaults to ``sys.stdin.isatty``).
        prompt: Callable used to ask the user on the interactive prompt path
            (injectable for tests; defaults to the built-in ``input``).

    Returns:
        The same ``frame`` with a canonical ``KEY`` column established.

    Raises:
        ValueError: When ``policy`` is ``"prompt"`` and stdin is not interactive
            while the KEY diverges (propagated from :func:`decide_key_action`).

    Side effects:
        Emits ``logging`` warnings on ``trust``/``overwrite`` resolution.
    """
    rebuilt = _rebuilt_key_series(frame)

    # Absent KEY: nothing to reconcile, simply create the column.
    if not has_key_column:
        frame["KEY"] = rebuilt
        return frame

    # Present KEY: compare every existing value to the rebuilt pattern.
    existing = [str(value) for value in frame["KEY"]]
    if existing == rebuilt:
        # Matching KEY is trusted as-is.
        frame["KEY"] = existing
        return frame

    # Diverging KEY: resolve the conflict per the configured policy.
    action = decide_key_action(policy, is_tty=is_tty(), prompt=prompt)
    if action == "trust":
        logger.warning(
            "Source KEY column diverges from the rebuilt pattern; trusting the "
            "existing KEY values per --key-mismatch trust."
        )
        frame["KEY"] = existing
    else:
        logger.warning(
            "Source KEY column diverges from the rebuilt pattern; overwriting "
            "with the rebuilt pattern per --key-mismatch overwrite."
        )
        frame["KEY"] = rebuilt
    return frame
