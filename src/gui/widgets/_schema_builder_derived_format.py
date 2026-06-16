"""Display/storage format translation for derived-column expressions (D-1).

This helper isolates the bracketed-reference display convention for derived
expressions. The schema builder shows column references as ``[Name]`` so the
user can compose formulas by double-clicking columns, but the stored and
validated form is the bare ``col("Name")`` call the
:class:`~src.schema_formula.FormulaEvaluator` accepts. Translating between the two
forms lives here, entirely outside the formula engine: ``src/schema_formula.py``
and the evaluator grammar are not modified (D-1).

Responsibilities:
    - ``strip_brackets``: convert the display form ``[Name]`` to the stored form
      ``col("Name")`` before an expression reaches storage or validation.
    - ``add_brackets``: convert the stored form ``col("Name")`` back to ``[Name]``
      for display, only for references whose names are currently declared.

Scope boundaries:
    - Pure string transformation. No Qt, no evaluator import, no I/O.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PySide6.QtWidgets import QPlainTextEdit

__all__ = [
    "add_brackets",
    "parse_derived_lines",
    "read_derived_editor",
    "render_derived_lines",
    "render_derived_editor",
    "strip_brackets",
]

# A bracketed reference is ``[`` followed by any run of characters that are not a
# closing bracket, then ``]``. The inner text is the column name verbatim, so
# names with spaces and special characters round-trip through the quoted col()
# form. A non-greedy class avoids spanning across adjacent references.
_BRACKET_PATTERN = re.compile(r"\[([^\]]+)\]")


def _col_pattern_for(name: str) -> re.Pattern[str]:
    """Build a regex matching the exact ``col("<name>")`` call for one name.

    The name is matched literally (escaped) inside double quotes, tolerating
    optional whitespace around the inner string so reasonable formatting of the
    stored expression still re-brackets. Single-quoted ``col('...')`` is also
    accepted because the evaluator treats both quote styles identically.

    Args:
        name: The exact column name to match inside the ``col(...)`` call.

    Returns:
        A compiled pattern matching ``col("name")`` (or single-quoted) for the
        given name only.
    """
    escaped = re.escape(name)
    # Match col( "name" ) and col( 'name' ) with optional surrounding spaces so a
    # stored expression whose spacing differs slightly still re-brackets.
    return re.compile(r"""col\(\s*['"]""" + escaped + r"""['"]\s*\)""")


def strip_brackets(expr: str) -> str:
    """Convert display-form ``[Name]`` references to stored-form ``col("Name")``.

    Each ``[Name]`` token is replaced with ``col("Name")`` so the resulting
    expression is valid input to the existing
    :class:`~src.schema_formula.FormulaEvaluator`. The inner name is preserved
    verbatim (including spaces and special characters); the quoted ``col()`` form
    handles names that are not valid Python identifiers. Text outside brackets is
    left unchanged, so an already-stripped expression passes through untouched.

    Args:
        expr: The display expression, possibly containing ``[Name]`` references.

    Returns:
        The expression with every ``[Name]`` rewritten as ``col("Name")``. Inner
        double quotes in a name are escaped so the produced ``col("...")`` is still
        a single string literal.
    """

    def _replace(match: re.Match[str]) -> str:
        """Rewrite one ``[Name]`` match as a double-quoted ``col("Name")`` call.

        Args:
            match: The bracket match whose group 1 is the verbatim column name.

        Returns:
            The ``col("Name")`` replacement string with inner double quotes
            escaped so the result is a single valid string literal.
        """
        name = match.group(1)
        # Escape embedded double quotes so a name containing a quote still yields a
        # single, valid double-quoted string literal for the evaluator.
        safe = name.replace('"', '\\"')
        return f'col("{safe}")'

    return _BRACKET_PATTERN.sub(_replace, expr)


def add_brackets(expr: str, known_names: Iterable[str]) -> str:
    """Convert stored-form ``col("Name")`` references to display-form ``[Name]``.

    Only references whose names are in ``known_names`` are re-bracketed, so a
    ``col("...")`` naming an undeclared column is left as-is rather than implying a
    column exists. Longer names are processed first so a name that is a prefix of
    another does not partially match. The comma separator between references is
    outside the brackets (e.g. ``[col a], [col b]``) because only the ``col(...)``
    calls themselves are rewritten.

    Args:
        expr: The stored expression containing ``col("Name")`` calls.
        known_names: The declared column names eligible for re-bracketing.

    Returns:
        The expression with each known ``col("Name")`` rewritten as ``[Name]``;
        unknown references and all other text are unchanged.
    """
    result = expr
    # Replace longer names first so a shorter name that is a substring of a longer
    # declared name cannot pre-empt the longer match.
    for name in sorted(set(known_names), key=len, reverse=True):
        result = _col_pattern_for(name).sub(f"[{name}]", result)
    return result


def render_derived_lines(
    rows: Iterable[tuple[str, str]], known_names: Iterable[str]
) -> str:
    """Render derived rows as ``name = expression`` lines with bracketed display.

    Each row's stored expression has its known ``col("Name")`` references
    re-bracketed to ``[Name]`` for display (AC-4), then is joined to its name with
    the ``=`` separator (AC-3). Rows are newline-joined in order.

    Args:
        rows: The ``(name, stored_expression)`` pairs to render, in order.
        known_names: The declared column names eligible for re-bracketing.

    Returns:
        The multi-line editor text, one ``name = display_expression`` per row.
    """
    declared = list(known_names)
    # Re-bracket each stored expression for display, then join with the ``=``
    # separator so the editor shows the friendly bracketed form (AC-3, AC-4).
    lines = [
        f"{name} = {add_brackets(expression, declared)}" for name, expression in rows
    ]
    return "\n".join(lines)


def parse_derived_lines(text: str) -> list[tuple[str, str]]:
    """Parse editor text into stored ``(name, expression)`` rows.

    Each non-blank line is split on the first ``=`` (AC-3); the expression's
    bracketed references are stripped to the stored ``col("Name")`` form (AC-4,
    D-1) so nothing bracketed reaches the formula engine. Blank lines are skipped.

    Args:
        text: The raw editor text, one ``name = expression`` per line.

    Returns:
        One ``(name, stored_expression)`` tuple per non-blank line, with names and
        expressions trimmed of surrounding whitespace.
    """
    rows: list[tuple[str, str]] = []
    # Parse each non-blank line: split on the first ``=`` so an expression may
    # contain ``=``, then strip display brackets to the stored col() form.
    for line in text.splitlines():
        if not line.strip():
            continue
        name, _, expression = line.partition(" = ")
        rows.append((name.strip(), strip_brackets(expression.strip())))
    return rows


def render_derived_editor(
    editor: QPlainTextEdit,
    rows: Iterable[tuple[str, str]],
    known_names: Iterable[str],
) -> None:
    """Render derived rows into the editor with bracketed display (AC-3/AC-4).

    Sets the editor text to one ``name = display_expression`` line per row, with
    known ``col("Name")`` references re-bracketed to ``[Name]`` for display. The
    stored form is unchanged (D-1).

    Args:
        editor: The Derived-tab plain-text editor to populate.
        rows: One ``(name, stored_expression)`` tuple per derived column.
        known_names: The declared column names eligible for re-bracketing.

    Returns:
        ``None``.

    Side effects:
        Replaces the editor's plain text.
    """
    editor.setPlainText(render_derived_lines(rows, known_names))


def read_derived_editor(editor: QPlainTextEdit) -> list[tuple[str, str]]:
    """Parse the editor text into stored ``(name, expression)`` rows (AC-4, D-1).

    Display ``[Name]`` references are stripped to the stored ``col("Name")`` form so
    nothing bracketed reaches the formula engine.

    Args:
        editor: The Derived-tab plain-text editor to read.

    Returns:
        One ``(name, stored_expression)`` tuple per non-empty editor line.
    """
    return parse_derived_lines(editor.toPlainText())
