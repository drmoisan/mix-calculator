"""Activation-time schema matching for the source-tab import flow (Decision 6).

This helper classifies the active source sheet's headers against the persisted
schemas when a source tab is activated. Matching is alias-aware: the schema
registry's :func:`~src.schema_matching.find_best_match_in_registry` already scores
each schema's required columns against the actual headers using the columns'
persisted aliases (the matched source-column-to-canonical mappings). This module
turns that score into one of three activation outcomes — proceed, partial, or
none — so the import-flow wiring can auto-select a matching schema, offer a
"New from template" seed for a partial match, or fall back to the placeholder.

Responsibilities:
    - ``ActivationDecision``: the classified activation outcome plus the closest
      schema name and the match score.
    - ``classify_activation``: run the alias-aware registry match and classify the
      score against the full and partial acceptance thresholds.

Scope boundaries:
    - No Qt import, no I/O of its own. Matching flows through the injected service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.etl_columns import DEFAULT_THRESHOLD

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.gui.services.schema_service import SchemaServiceProtocol

__all__ = [
    "ActivationDecision",
    "PARTIAL_MATCH_THRESHOLD",
    "classify_activation",
]

# A score at or above this fraction (but below the full acceptance threshold)
# signals a possibly-new schema: many of an existing schema's alias columns match
# the active sheet, but not enough to bind. This is the "New from template"
# trigger per Decision 6. Chosen below DEFAULT_THRESHOLD so a partial band exists.
PARTIAL_MATCH_THRESHOLD: float = 0.5


@dataclass(frozen=True)
class ActivationDecision:
    """The classified outcome of matching an active sheet against the registry.

    Purpose:
        Carry the activation decision so the import-flow wiring can auto-select a
        matching schema (``"proceed"``), seed a new schema from the closest
        existing one (``"partial"``), or leave the placeholder selected with
        Import disabled (``"none"``).

    Attributes:
        action: One of ``"proceed"`` (a schema bound at/above the full
            threshold), ``"partial"`` (the closest schema scored in the partial
            band — a possibly-new schema), or ``"none"`` (no usable match).
        schema_name: The closest existing schema's name when ``action`` is
            ``"proceed"`` or ``"partial"``; ``None`` when ``action`` is
            ``"none"``.
        score: The closest schema's required-column coverage score.
    """

    action: str
    schema_name: str | None
    score: float


def classify_activation(
    service: SchemaServiceProtocol,
    headers: Sequence[str],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    partial_threshold: float = PARTIAL_MATCH_THRESHOLD,
) -> ActivationDecision:
    """Classify the active sheet's headers against the persisted schemas.

    Runs the service's alias-aware registry match (which scores each schema's
    required columns against the headers using the columns' persisted aliases),
    then classifies the best score into a three-way decision per Decision 6:

    Routing table:
        - ``score >= threshold`` and a schema was selected → ``"proceed"`` (the
          schema is auto-selected; Import enables).
        - ``partial_threshold <= score < threshold`` with a selected schema →
          ``"partial"`` (the closest schema seeds a "New from template").
        - otherwise → ``"none"`` (placeholder stays selected; Import disabled).

    Args:
        service: The schema service used to run the alias-aware registry match.
        headers: The actual source headers from the active sheet, in source order.
        threshold: The full acceptance threshold; defaults to the Feature B
            :data:`~src.etl_columns.DEFAULT_THRESHOLD`.
        partial_threshold: The lower bound of the partial-match band; a score in
            ``[partial_threshold, threshold)`` triggers new-from-template.

    Returns:
        An :class:`ActivationDecision` carrying the action, the closest schema
        name (when any), and the score.
    """
    result = service.find_best_match(headers)
    # No candidate at all means nothing to select; fall through to the placeholder.
    if result.schema is None:
        return ActivationDecision(action="none", schema_name=None, score=result.score)
    # A score clearing the full bar auto-selects the matching schema.
    if result.score >= threshold:
        return ActivationDecision(
            action="proceed", schema_name=result.schema.name, score=result.score
        )
    # A score in the partial band signals a possibly-new schema: offer the closest
    # existing schema as a "New from template" seed (Decision 6).
    if result.score >= partial_threshold:
        return ActivationDecision(
            action="partial", schema_name=result.schema.name, score=result.score
        )
    # Below the partial band there is no usable match; keep the placeholder.
    return ActivationDecision(action="none", schema_name=None, score=result.score)
