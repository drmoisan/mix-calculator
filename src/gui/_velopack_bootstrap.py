"""Velopack runtime SDK bootstrap helper for ``src.gui.app:main()`` (issue #31).

Velopack ships a C-extension ``velopack.pyd`` with no ``py.typed`` marker,
so the SDK's ``App`` constructor and ``.run`` method are Unknown under
Pyright strict mode. This module isolates the untyped call to a single
function whose signature is fully typed, keeping ``src/gui/app.py``
under the 500-line cap.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

import velopack  # type: ignore[import-untyped]  # velopack runtime SDK; no py.typed marker

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["run_velopack_bootstrap"]


class _VelopackAppProtocol(Protocol):
    """Structural contract for the Velopack ``App`` runtime object.

    The Protocol records the runtime contract (``run()`` returns ``None``)
    so the helper can be typed end-to-end without per-call suppressions.
    """

    def run(self) -> None:
        """Drive Velopack's first-install and uninstall hooks."""


def run_velopack_bootstrap() -> None:
    """Invoke ``velopack.App().run()`` exactly once.

    Wraps the untyped Velopack SDK call so the production entry-point can
    call a single typed seam. ``getattr`` is used to access the C-extension
    ``App`` attribute so Pyright's strict attribute-access check is
    satisfied. Per Velopack's documented ``harmless when unmanaged``
    semantics the call is a no-op when the app is not installed via a
    Velopack installer.
    """
    app_constructor = cast(
        "Callable[[], _VelopackAppProtocol]",
        getattr(velopack, "App", None),
    )
    if app_constructor is None:
        # Defensive guard: a missing ``App`` attribute would indicate a
        # broken or wrong-version velopack install; surface a clear error.
        raise RuntimeError(
            "velopack.App is not available; check the installed velopack "
            "package version."
        )
    app = app_constructor()
    app.run()
