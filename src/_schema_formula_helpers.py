"""Pure helpers for the schema formula engine (Issue #43, Feature C).

Purpose:
    House the whitelisted pure functions and the column-alias utilities used by
    :mod:`src.schema_formula` so that module stays under the 500-line file limit.
    Every function here is pure: a deterministic function of its inputs with no
    I/O, wall-clock, or randomness.

Contents:
    - :func:`safe_div`: the division primitive (scalar and vectorized).
    - :func:`formula_sum`: the whitelisted variadic ``sum`` (scalar and
      vectorized, dtype-preserving).
    - :func:`alias_for` / :func:`build_alias_map`: deterministic identifier-alias
      mapping for column names that may contain spaces or special characters.
"""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, cast

import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Sequence


def safe_div(num: object, den: object) -> object:
    """Divide ``num`` by ``den``; yield ``0.0`` for a missing/non-positive denominator.

    Purpose:
        Provide the division primitive every ratio/per-unit/%-of-sales derived
        column uses, with the as-built rule that a denominator that is ``None``,
        ``NaN``, or ``<= 0`` yields ``0.0`` rather than raising or producing
        ``inf``/``NaN``.

    The function is polymorphic so it serves both scalar formula evaluation and
    the vectorized derived-column path: when ``num``/``den`` are pandas Series
    the division and the zero-substitution are applied element-wise, which lets
    the loader recompute a ratio column from summed dollars/volume while
    preserving pandas dtype parity with the protected loaders.

    Args:
        num: The numerator: a scalar number or a pandas Series.
        den: The denominator: a scalar number or a pandas Series. Treated as
            invalid where it is ``None``, ``NaN``, or ``<= 0``; those positions
            yield ``0.0``.

    Returns:
        ``num / den`` where ``den`` is positive and finite; ``0.0`` elsewhere.
        Scalars return a ``float``; Series inputs return an element-wise Series.

    Raises:
        Never raises for numeric/Series inputs; invalid denominators yield 0.
    """
    # Vectorized path: when either operand is a Series, divide element-wise and
    # replace invalid-denominator positions with 0.0, preserving pandas semantics.
    if isinstance(num, pd.Series) or isinstance(den, pd.Series):
        return _safe_div_series(cast("object", num), cast("object", den))

    # Scalar path: a missing denominator (None) has no base to divide by -> 0.0.
    if den is None:
        return 0.0
    den_value = float(cast("float", den))
    # NaN or non-positive denominators are not a meaningful base; the as-built
    # behavior collapses them to 0.0 instead of producing inf/NaN.
    if math.isnan(den_value) or den_value <= 0.0:
        return 0.0
    return float(cast("float", num)) / den_value


def _safe_div_series(num: object, den: object) -> pd.Series[float]:
    """Element-wise safe division for the vectorized derived-column path.

    Args:
        num: The numerator, a pandas Series or a scalar broadcast across ``den``.
        den: The denominator, a pandas Series or a scalar. Positions where the
            denominator is null or ``<= 0`` yield ``0.0``.

    Returns:
        A float Series of element-wise ``num / den`` with invalid-denominator
        positions set to ``0.0``.
    """
    # Normalize both operands to float Series so the arithmetic and the masked
    # zero-substitution are fully typed and element-wise.
    den_series: pd.Series[float] = (
        cast("pd.Series[float]", den)
        if isinstance(den, pd.Series)
        else pd.Series(float(cast("float", den)))
    )
    num_series: pd.Series[float] = (
        cast("pd.Series[float]", num)
        if isinstance(num, pd.Series)
        else pd.Series(float(cast("float", num)), index=den_series.index)
    )
    # A position is valid only when the denominator is non-null and strictly > 0.
    valid: pd.Series[bool] = den_series.notna() & (den_series > 0.0)
    quotient: pd.Series[float] = num_series / den_series.where(valid)
    return quotient.where(valid, 0.0)


def formula_sum(*args: object) -> object:
    """Sum numeric arguments, accepting either varargs or a single iterable.

    Purpose:
        Provide the whitelisted ``sum`` a formula may call. Unlike the builtin
        ``sum`` (which takes an iterable plus an optional start), this accepts
        multiple positional arguments — for example ``sum(May, Jun, ..., Dec)`` —
        so the as-built LE ``YTG`` expression that lists each month positionally
        evaluates as a plain total, matching ``normalize_le.compute_ytg``. A
        single iterable argument (for example ``sum([May, Jun])``) is also
        supported.

    The accumulation starts from the first value rather than a ``0.0`` seed so a
    sum of integer pandas Series stays an integer Series, preserving dtype parity
    with the protected loaders' vectorized derived columns.

    Args:
        *args: Either one iterable of values, or two or more individual values.
            Each value is a scalar number or a pandas Series. ``None`` scalars
            are skipped so a missing measure contributes nothing.

    Returns:
        The total of the supplied values. The result type follows the inputs (a
        Series sum returns a Series; a scalar sum returns a float).

    Raises:
        TypeError: If a single non-sequence, non-numeric argument is supplied.
    """
    # A single non-numeric argument is treated as an iterable to sum (the
    # sum([...]) form); multiple arguments are the positional sum(a, b, ...) form.
    if len(args) == 1 and not isinstance(args[0], (int, float, pd.Series)):
        candidate = args[0]
        if not isinstance(candidate, (list, tuple)):
            raise TypeError(f"sum() received a non-numeric argument: {candidate!r}")
        values: tuple[object, ...] = tuple(cast("tuple[object, ...]", candidate))
    else:
        values = args

    # Accumulate starting from the first non-None value (not a float seed) so an
    # all-integer Series sum keeps its integer dtype; None scalars are skipped.
    total: object = None
    for value in values:
        if value is None:
            continue
        total = value if total is None else _add(total, value)
    # An empty sum (all None / no args) is 0.0, matching pandas' NaN-as-0 fill.
    return 0.0 if total is None else total


def _add(left: object, right: object) -> object:
    """Add two formula values (scalars or pandas Series), preserving dtype.

    Args:
        left: The running total (a number or a pandas Series).
        right: The next value (a number or a pandas Series).

    Returns:
        ``left + right``. A Series operand yields a Series result; two scalars
        yield a numeric result.

    Raises:
        TypeError: If a non-numeric, non-Series operand is supplied.
    """
    # A Series on either side drives an element-wise Series addition; cast both
    # operands to float Series (or scalar) so the addition is fully typed.
    if isinstance(left, pd.Series) or isinstance(right, pd.Series):
        left_operand: pd.Series[float] | float = (
            cast("pd.Series[float]", left)
            if isinstance(left, pd.Series)
            else float(cast("float", left))
        )
        right_operand: pd.Series[float] | float = (
            cast("pd.Series[float]", right)
            if isinstance(right, pd.Series)
            else float(cast("float", right))
        )
        # At least one operand is a Series, so the sum is a Series; return it as
        # object since the static union also admits the float-float branch.
        return left_operand + right_operand
    # Two scalars: both must be real numbers to add.
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        raise TypeError(f"sum() received a non-numeric argument: {left!r}, {right!r}")
    return left + right


def alias_for(name: str) -> str:
    """Return a deterministic Python-identifier alias for a column ``name``.

    Purpose:
        Map an arbitrary column name (which may contain spaces or special
        characters) to a stable, valid Python identifier so it can be referenced
        directly inside a formula expression.

    Args:
        name: The exact column name, for example ``"SKU #"`` or ``"Off Invoice $"``.

    Returns:
        A valid Python identifier formed by replacing every run of non-identifier
        characters with ``"_"`` and prefixing a leading digit with ``"c_"``. The
        mapping is deterministic: the same name always yields the same alias.
    """
    # Replace any character that is not an ASCII letter, digit, or underscore
    # with "_". Using an explicit ASCII class (rather than \W) excludes Unicode
    # "word" characters that are not valid in a Python identifier, guaranteeing
    # the alias is always identifier-safe.
    sanitized = re.sub(r"[^0-9A-Za-z_]", "_", name)
    # Python identifiers may not begin with a digit; prefix those so the alias
    # is always syntactically valid.
    if sanitized and sanitized[0].isdigit():
        sanitized = f"c_{sanitized}"
    if not sanitized:
        sanitized = "c_"
    return sanitized


def build_alias_map(known_columns: Sequence[str]) -> dict[str, str]:
    """Build a deterministic alias-to-column map for ``known_columns``.

    Purpose:
        Produce the identifier aliases a formula may reference, resolving
        collisions deterministically by appending a numeric suffix in column
        order so two distinct columns never share one alias.

    Args:
        known_columns: The canonical column names in their schema order.

    Returns:
        A mapping from identifier alias to the exact column name. Identifier-safe
        column names map from themselves; non-identifier names map from their
        sanitized alias. Collisions are disambiguated with a ``_2``/``_3`` suffix.

    Raises:
        Never raises; collision handling guarantees a unique alias per column.
    """
    alias_map: dict[str, str] = {}
    # Walk columns in schema order so alias assignment (and any collision
    # suffixing) is deterministic regardless of dict iteration quirks.
    for column in known_columns:
        candidate = alias_for(column)
        # Disambiguate a collision (two different columns sanitizing to the same
        # identifier) by appending an incrementing suffix until the alias is free.
        if candidate in alias_map and alias_map[candidate] != column:
            suffix = 2
            while f"{candidate}_{suffix}" in alias_map:
                suffix += 1
            candidate = f"{candidate}_{suffix}"
        alias_map[candidate] = column
    return alias_map
