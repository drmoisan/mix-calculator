"""Minimal typed stub for the ``asteval`` package (Issue #43, Feature C).

The upstream ``asteval`` distribution ships no ``py.typed`` marker and no type
stubs, so under Pyright strict every attribute access against it would be typed
as ``Unknown``. This local stub declares only the narrow surface that
``src.schema_formula`` uses, fully annotated, so the formula adapter type-checks
with no suppression.

Scope: this stub intentionally models a subset of ``asteval.Interpreter``. It is
not a complete description of the library; only the constructor parameters and
attributes the adapter touches are declared. The constructor's untouched tail
parameters are absorbed by ``**kwargs``.
"""

from collections.abc import Callable

class _RuntimeError:
    """A single entry in :attr:`Interpreter.error`.

    Each evaluation error asteval collects exposes :meth:`get_error`, which
    returns the exception class name and a human-readable message. The adapter
    inspects these to raise a descriptive ``FormulaError``.
    """

    def get_error(self) -> tuple[str, str]:
        """Return the ``(exception_name, message)`` pair for this error."""
        ...

class Interpreter:
    """Typed view of the asteval expression interpreter used by the adapter.

    Only the keyword constructor parameters, the ``symtable`` mapping, the
    ``error`` list, and the callable evaluation entry point are declared. The
    real class accepts further constructor parameters that the adapter never
    passes; they are absorbed by ``**kwargs``.

    Attributes:
        symtable: The interpreter symbol table. The adapter constrains this to
            the whitelisted functions plus the supplied column values.
        error: The list of evaluation errors collected during the most recent
            call. Empty when evaluation succeeded.
    """

    symtable: dict[str, object]
    error: list[_RuntimeError]

    def __init__(
        self,
        symtable: dict[str, object] | None = ...,
        *,
        user_symbols: dict[str, object] | None = ...,
        use_numpy: bool = ...,
        minimal: bool = ...,
        readonly_symbols: object | None = ...,
        no_print: bool = ...,
        **kwargs: object,
    ) -> None:
        """Construct an interpreter with the supplied symbol table and flags."""
        ...

    def __call__(self, expr: str) -> object:
        """Evaluate ``expr`` against the current symbol table and return its value."""
        ...

# asteval also exposes the symtable factory and procedure type, but the adapter
# does not use them; only the names above are declared.
make_symbol_table: Callable[..., dict[str, object]]
