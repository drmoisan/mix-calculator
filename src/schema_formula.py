"""Sandboxed formula engine for configurable-schema derived columns (Issue #43).

Purpose:
    Provide a safe, deterministic expression engine that schema-defined derived
    columns use to compute values from other columns. Two pieces make up the
    public surface:

    - :func:`safe_div` and the :func:`col` accessor: the whitelisted pure helpers
      exposed inside every formula's symbol table.
    - :class:`FormulaEvaluator`: a typed adapter over ``asteval.Interpreter`` that
      validates an expression against a known-column set and evaluates it against
      a per-row context, constraining the symbol table to row/column values plus
      the whitelisted function set.

Safety model:
    Expressions are validated with Python's :mod:`ast` before evaluation. The
    validator rejects imports, attribute access, subscripting, comprehensions,
    lambdas, and calls to any name outside the whitelist, and rejects references
    to names that are neither a known column (or its identifier alias) nor a
    whitelisted function. Evaluation then runs through ``asteval`` with a symbol
    table limited to the column values and the whitelisted callables, so a
    rejected construct can never reach the interpreter.

Column-name strategy:
    Source columns may contain spaces or special characters (for example
    ``"SKU #"`` or ``"Off Invoice $"``) that are not valid Python identifiers.
    Two reference styles are supported, both covered by tests:

    - the :func:`col` callable: ``col("Off Invoice $")`` resolves the exact name.
    - a deterministic identifier-alias map: each column name is mapped to a safe
      identifier (for example ``Off Invoice $`` -> ``Off_Invoice__``) that the
      expression may reference directly.

Determinism:
    Validation and evaluation are pure functions of their inputs. No wall-clock,
    no randomness, no I/O. The alias map is built deterministically from the
    column order so the same columns always yield the same aliases.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from asteval import Interpreter

from src._schema_formula_helpers import (
    alias_for,
    build_alias_map,
    formula_sum,
    safe_div,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

# Re-export the pure helpers so callers and tests can import them from this
# module as well as from ``src._schema_formula_helpers`` (the helpers live in the
# private module so this file stays under the 500-line limit).
__all__ = [
    "FormulaError",
    "FormulaEvaluator",
    "alias_for",
    "build_alias_map",
    "formula_sum",
    "safe_div",
]


class FormulaError(Exception):
    """Raised when a formula expression is invalid, unsafe, or fails to evaluate.

    Purpose:
        Signal every failure mode of the formula engine with a descriptive
        message that names the offending construct or column. Callers treat this
        as the single contract-level exception of the engine.
    """


# The names a formula may call. ``col`` is bound per-evaluation to the current
# context; ``safe_div`` and ``sum`` are pure and context-independent.
WHITELISTED_FUNCTIONS: frozenset[str] = frozenset({"safe_div", "sum", "col"})

# AST node types that are never allowed inside a formula expression. Each maps to
# a human-readable label used in the rejection message.
_FORBIDDEN_NODES: dict[type[ast.AST], str] = {
    ast.Import: "import statement",
    ast.ImportFrom: "import statement",
    ast.Attribute: "attribute access",
    ast.Subscript: "subscripting",
    ast.ListComp: "comprehension",
    ast.SetComp: "comprehension",
    ast.DictComp: "comprehension",
    ast.GeneratorExp: "comprehension",
    ast.Lambda: "lambda",
    ast.Assign: "assignment",
    ast.NamedExpr: "assignment",
    ast.Starred: "starred expression",
}


class FormulaEvaluator:
    """Validate and evaluate sandboxed schema formula expressions.

    Purpose:
        Wrap ``asteval.Interpreter`` behind a typed adapter that (a) validates an
        expression against a known-column set, rejecting unsafe or unknown
        references with a descriptive :class:`FormulaError`, and (b) evaluates a
        validated expression against a per-row context with a symbol table
        limited to the supplied column values plus the whitelisted functions.

    Responsibilities:
        - Reject syntactically invalid expressions.
        - Reject disallowed constructs (imports, attribute access, subscripting,
          comprehensions, lambdas, calls to non-whitelisted names).
        - Reject references to names that are neither a known column, a known
          column's identifier alias, nor a whitelisted function.
        - Evaluate a validated expression deterministically and surface any
          interpreter-side error as a :class:`FormulaError`.

    Usage:
        Construct once (no per-row state is retained), call :meth:`validate` once
        per expression against the known column set, then call :meth:`evaluate`
        per row with that row's column values.

    High-level flow:
        ``validate`` -> parse with :mod:`ast`, walk the tree, reject forbidden
        nodes and unknown names. ``evaluate`` -> build a fresh symbol table from
        the context plus whitelisted callables, run the interpreter, inspect its
        error list, and return the value.

    Key invariants:
        - The symbol table handed to the interpreter contains only the
          whitelisted callables, the provided column values, and their aliases.
        - Evaluation is side-effect free and deterministic.

    Side effects:
        None. The evaluator performs no I/O and mutates none of its inputs.
    """

    def validate(self, expression: str, known_columns: Sequence[str]) -> None:
        """Validate ``expression`` against ``known_columns``, raising on any problem.

        Args:
            expression: The formula source to validate.
            known_columns: The canonical column names the expression may reference
                (directly when identifier-safe, or via their identifier alias).

        Returns:
            ``None`` when the expression is valid.

        Raises:
            FormulaError: If the expression is syntactically invalid, uses a
                disallowed construct (naming the construct), calls a
                non-whitelisted function (naming it), or references an unknown
                column/name (naming it).
        """
        # Parse in eval mode so only a single expression (no statements) is legal;
        # a SyntaxError here means the formula text itself is malformed.
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise FormulaError(
                f"invalid formula syntax: {expression!r} ({exc.msg})"
            ) from exc

        alias_map = build_alias_map(known_columns)
        # Allowed bare names are the whitelisted functions plus every column alias
        # (identifier-safe columns alias to themselves).
        allowed_names = set(WHITELISTED_FUNCTIONS) | set(alias_map)
        self._reject_forbidden_nodes(tree, expression)
        self._reject_unknown_names(tree, allowed_names)

    def _reject_forbidden_nodes(self, tree: ast.AST, expression: str) -> None:
        """Reject any forbidden construct and any call to a non-whitelisted name.

        Args:
            tree: The parsed expression AST.
            expression: The original source, included in error messages.

        Returns:
            ``None`` when no forbidden construct is present.

        Raises:
            FormulaError: Naming the first forbidden construct found, or the first
                non-whitelisted callable.
        """
        # Walk every node so a forbidden construct nested anywhere is caught.
        for node in ast.walk(tree):
            # Reject structurally unsafe constructs (imports, attribute access,
            # subscripting, comprehensions, lambdas, assignments, starring).
            label = _FORBIDDEN_NODES.get(type(node))
            if label is not None:
                raise FormulaError(
                    f"formula uses a disallowed construct ({label}): {expression!r}"
                )
            # A call is only allowed when its callee is a bare whitelisted name;
            # any other callee (including computed callees) is rejected.
            if isinstance(node, ast.Call):
                func = node.func
                if (
                    not isinstance(func, ast.Name)
                    or func.id not in WHITELISTED_FUNCTIONS
                ):
                    name = func.id if isinstance(func, ast.Name) else "<expression>"
                    raise FormulaError(
                        f"formula calls a non-whitelisted function "
                        f"({name}); allowed: {sorted(WHITELISTED_FUNCTIONS)}"
                    )

    def _reject_unknown_names(self, tree: ast.AST, allowed_names: set[str]) -> None:
        """Reject any loaded bare name that is not an allowed column or function.

        Args:
            tree: The parsed expression AST.
            allowed_names: The set of permitted bare names (whitelisted functions
                plus column aliases).

        Returns:
            ``None`` when every referenced name is allowed.

        Raises:
            FormulaError: Naming the first unknown referenced name.
        """
        # Only loaded names (reads) matter; the validator already forbade stores.
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                if node.id not in allowed_names:
                    raise FormulaError(
                        f"formula references unknown column or name {node.id!r}"
                    )

    def evaluate(self, expression: str, context: Mapping[str, object]) -> object:
        """Evaluate ``expression`` against the row ``context`` and return its value.

        Args:
            expression: The validated formula source. Callers should call
                :meth:`validate` first; ``evaluate`` still confines the symbol
                table so an un-validated expression cannot reach unsafe state.
            context: A mapping of exact column name to that row's value. Each key
                is exposed both under its identifier alias and via ``col(name)``.

        Returns:
            The evaluated value (typically ``float`` for arithmetic formulas).

        Raises:
            FormulaError: If the interpreter reports any evaluation error.
        """
        symtable = self._build_symtable(context)
        interpreter = Interpreter(
            symtable=symtable,
            use_numpy=False,
            minimal=True,
            no_print=True,
        )
        result = interpreter(expression)
        # asteval accumulates errors rather than raising; surface the first one as
        # a descriptive FormulaError so callers see a single failure contract.
        if interpreter.error:
            messages = [entry.get_error()[1] for entry in interpreter.error]
            raise FormulaError(
                f"failed to evaluate formula {expression!r}: {'; '.join(messages)}"
            )
        return result

    def _build_symtable(self, context: Mapping[str, object]) -> dict[str, object]:
        """Build the constrained symbol table for one evaluation.

        Args:
            context: The exact-name-to-value mapping for the current row.

        Returns:
            A dict containing only the whitelisted callables, every column value
            keyed by its identifier alias, and a ``col`` accessor bound to the
            exact-name context. The whitelisted callables are bound last so a
            column whose identifier alias collides with ``col``/``sum``/
            ``safe_div`` cannot shadow the helper; ``col`` still reads from the
            closed-over context, so ``col("col")`` returns the column value.

        Raises:
            Never raises.
        """
        alias_map = build_alias_map(list(context))

        def col(name: str) -> object:
            """Return the context value for the exact column ``name``.

            Args:
                name: The exact column name, including spaces/special characters.

            Returns:
                The value bound to ``name`` in the current row context.

            Raises:
                FormulaError: If ``name`` is not present in the context.
            """
            if name not in context:
                raise FormulaError(f"col() references unknown column {name!r}")
            return context[name]

        # Bind each column value under its identifier alias first so identifier-safe
        # and special-char columns alike are reachable directly; col() covers
        # exact-name access. Populate the aliases before the whitelisted callables.
        symtable: dict[str, object] = {}
        for alias, column in alias_map.items():
            symtable[alias] = context[column]
        # Bind the whitelisted callables LAST so a column whose identifier alias
        # collides with "col"/"sum"/"safe_div" cannot shadow the helper. The col
        # accessor reads from the closed-over context (not symtable), so
        # col("col"), col("sum"), and col("safe_div") still resolve the
        # exact-name column value for every column name.
        symtable["safe_div"] = safe_div
        symtable["sum"] = formula_sum
        symtable["col"] = col
        return symtable
