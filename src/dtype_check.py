"""Pure dtype-coercion checking for the Columns-tab expected-type indicator.

This module decides whether a sample of source values coerces to a declared
expected data type and, when it does not, returns the first failing example value.
It is pure: given the same values and dtype it returns the same result with no I/O,
clock, or randomness. The Columns-tab presenter runs this against the masked
preview slice for each matched column and drives a passive pass/fail indicator.

Responsibilities:
    - ``check_dtype``: return a :class:`DtypeCheckResult` (coercible flag plus the
      first failing example) for a list of values against an expected dtype.

Coercion rules per dtype:
    - ``integer``/``float``: reuse :func:`pandas.to_numeric` (``float`` accepts any
      numeric; ``integer`` additionally requires a whole-number value).
    - ``date``: reuse :func:`pandas.to_datetime` per value.
    - ``bool``: accept a fixed set of truthy/falsey tokens (case-insensitive) plus
      real booleans.
    - ``string``: every non-null value is representable as a string, so a string
      column is always coercible.

Scope boundaries:
    - Pure functions over plain Python values. No Qt, no file/network I/O. Blank
      and null values are skipped (they carry no type signal).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pandas as pd

__all__ = [
    "DtypeCheckResult",
    "check_dtype",
]

# Tokens accepted as booleans (case-insensitive) in addition to real ``bool``
# values. Kept small and explicit so an unexpected token is reported as failing.
_BOOL_TRUE_TOKENS = frozenset({"true", "t", "yes", "y", "1"})
_BOOL_FALSE_TOKENS = frozenset({"false", "f", "no", "n", "0"})


@dataclass(frozen=True)
class DtypeCheckResult:
    """The outcome of checking sample values against an expected dtype.

    Attributes:
        coercible: ``True`` when every non-blank sample value coerces to the
            expected dtype; ``False`` when at least one value cannot.
        failing_example: The first sample value that failed to coerce, rendered as
            a string; ``None`` when ``coercible`` is ``True``.
    """

    coercible: bool
    failing_example: str | None


def _is_blank(value: object) -> bool:
    """Return whether a value carries no type signal (null or blank string).

    Args:
        value: The sample value to test.

    Returns:
        ``True`` when the value is ``None``, a pandas NA/NaN, or an
        all-whitespace string; such values are skipped by the check.
    """
    # Null-like values (None, NaN) carry no type to validate. The isna check is
    # guarded to scalar inputs and cast to a bool result so strict typing holds.
    if value is None:
        return True
    if isinstance(value, float) and bool(cast("bool", pd.isna(value))):
        return True
    # A whitespace-only string is treated as blank (no signal).
    return isinstance(value, str) and value.strip() == ""


def _coerces_numeric(value: object, *, require_integer: bool) -> bool:
    """Return whether a value coerces to a numeric (optionally whole) type.

    Args:
        value: The value to coerce.
        require_integer: When ``True``, the value must be a whole number to pass
            (the ``integer`` dtype); when ``False``, any numeric passes (``float``).

    Returns:
        ``True`` when the value parses as numeric and satisfies the integer
        constraint; ``False`` otherwise.
    """
    # Reuse pandas numeric parsing so the check matches the loader's coercion;
    # a non-numeric value yields NaN under coerce, which fails the check. The
    # value is rendered to a string first so the pandas overload is well-typed
    # and matches how a read cell would be parsed.
    parsed = pd.to_numeric(str(value), errors="coerce")
    if bool(cast("bool", pd.isna(parsed))):
        return False
    # An integer dtype additionally requires the parsed value to be whole.
    if require_integer:
        return float(parsed) == int(parsed)
    return True


def _coerces_date(value: object) -> bool:
    """Return whether a value parses as a date/datetime.

    Args:
        value: The value to parse.

    Returns:
        ``True`` when :func:`pandas.to_datetime` parses the value; ``False``
        when it cannot.
    """
    # to_datetime with coerce yields NaT for unparseable values; treat NaT as a
    # failure so the indicator reports the offending example. The value is
    # rendered to a string first so the pandas overload is well-typed.
    parsed = pd.to_datetime(str(value), errors="coerce")
    return not bool(cast("bool", pd.isna(parsed)))


def _coerces_bool(value: object) -> bool:
    """Return whether a value is a recognized boolean token or real bool.

    Args:
        value: The value to test.

    Returns:
        ``True`` for real ``bool`` values and the recognized truthy/falsey string
        tokens (case-insensitive); ``False`` otherwise.
    """
    # Real booleans always pass.
    if isinstance(value, bool):
        return True
    # Otherwise only the explicit token set is accepted, normalized to lower-case.
    token = str(value).strip().lower()
    return token in _BOOL_TRUE_TOKENS or token in _BOOL_FALSE_TOKENS


def _value_coerces(value: object, expected_dtype: str) -> bool:
    """Return whether one value coerces to the expected dtype.

    Routing table by ``expected_dtype``:
        - ``string`` → always coercible (any value renders as a string).
        - ``float`` → numeric without the whole-number constraint.
        - ``integer`` → numeric with the whole-number constraint.
        - ``date`` → parseable by ``pandas.to_datetime``.
        - ``bool`` → a real bool or a recognized token.

    Args:
        value: The value to coerce.
        expected_dtype: The target dtype (assumed a valid vocabulary value).

    Returns:
        ``True`` when the value coerces to ``expected_dtype``.
    """
    # Dispatch on the expected dtype; each branch delegates to a focused helper so
    # the routing stays readable and the per-type rules are isolated.
    if expected_dtype == "string":
        return True
    if expected_dtype == "float":
        return _coerces_numeric(value, require_integer=False)
    if expected_dtype == "integer":
        return _coerces_numeric(value, require_integer=True)
    if expected_dtype == "date":
        return _coerces_date(value)
    if expected_dtype == "bool":
        return _coerces_bool(value)
    # An unknown dtype is treated as non-coercible so a misconfiguration surfaces
    # rather than silently passing.
    return False


def check_dtype(values: list[object], expected_dtype: str) -> DtypeCheckResult:
    """Check whether sample values coerce to an expected dtype.

    Skips blank/null values (they carry no type signal) and tests every remaining
    value. Returns coercible with no example when all pass; otherwise returns
    not-coercible with the first failing value rendered as a string.

    Args:
        values: The sample values to check, in row order.
        expected_dtype: The expected dtype, one of ``string``, ``integer``,
            ``float``, ``date``, ``bool``.

    Returns:
        A :class:`DtypeCheckResult`. ``coercible`` is ``True`` when every
        non-blank value coerces; otherwise it is ``False`` and ``failing_example``
        is the first failing value as a string.
    """
    # Walk the sample values and stop at the first non-blank value that does not
    # coerce, recording it as the concrete failing example for the indicator.
    for value in values:
        if _is_blank(value):
            continue
        if not _value_coerces(value, expected_dtype):
            return DtypeCheckResult(coercible=False, failing_example=str(value))
    # Every non-blank value coerced (or there were no values to test).
    return DtypeCheckResult(coercible=True, failing_example=None)
