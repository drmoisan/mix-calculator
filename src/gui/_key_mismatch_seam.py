"""KEY-mismatch resolution seams for the GUI import path (WS1a, issue #48).

This module holds the small default seams the :class:`PipelineService` forwards
to the LE and AOP loaders so a GUI session resolves a diverging source ``KEY``
through an injected resolver (a Qt modal at the composition root) instead of the
loaders' stdin ``input()`` path. It lives in its own module so
``pipeline_service.py`` stays under the repository's 500-line file cap.

Responsibilities:
    - ``default_key_mismatch_resolver``: the default "trust" ("Keep existing")
      policy that keeps the loaders off the interactive prompt path.
    - ``never_tty``: an ``is_tty`` seam that always reports a non-interactive
      stdin.
    - ``no_stdin_prompt``: a ``prompt`` seam that fails fast if the interactive
      path is ever reached.

The functions are pure (``no_stdin_prompt`` raises by design); none touch disk,
network, or a database.
"""

from __future__ import annotations

__all__ = [
    "default_key_mismatch_resolver",
    "never_tty",
    "no_stdin_prompt",
]


def default_key_mismatch_resolver() -> str:
    """Return the default KEY-mismatch policy for a GUI session (WS1a).

    The GUI default is ``"trust"`` ("Keep existing"): the source KEY column is
    kept as-is rather than rebuilt. Returning a concrete policy here means the
    loaders never reach the interactive ``prompt``/stdin path, because
    ``etl_key.reconcile_key`` short-circuits on ``"trust"``/``"overwrite"``
    (AC-1/AC-2).

    Returns:
        The literal ``"trust"`` policy string.
    """
    return "trust"


def never_tty() -> bool:
    """Return ``False`` so the loaders never treat stdin as interactive (WS1a).

    Injected as the ``is_tty`` seam so that, even in the defensive case where a
    resolver returned ``"prompt"``, the loader fails fast instead of reading real
    stdin.

    Returns:
        ``False`` always.
    """
    return False


def no_stdin_prompt(_message: str) -> str:
    """Raise instead of consulting stdin if the prompt path is ever reached (WS1a).

    Injected as the ``prompt`` seam so an unexpected interactive path surfaces
    loudly as a defect rather than silently blocking on stdin in a GUI session.

    Args:
        _message: The prompt message the loader would have shown (ignored).

    Returns:
        Never returns; always raises.

    Raises:
        RuntimeError: Always; a GUI session must resolve KEY mismatches through
            the injected resolver/Qt modal, never stdin.
    """
    raise RuntimeError(
        "KEY-mismatch prompt reached stdin in a GUI session; the injected "
        "resolver must return 'trust' or 'overwrite' (issue #48 / WS1a)."
    )
