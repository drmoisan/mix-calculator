"""Schema matching and discovery built additively on Feature A and the resolver.

This module scores how completely a set of actual source headers maps onto the
required columns of one or more :class:`src.schema_model.SchemaDefinition`
candidates, selects the best-matching schema deterministically, and explains a
non-match through a typed, human-readable :class:`MismatchReport`.

Responsibilities:
    - Build a structured :class:`MismatchReport` for the unmatched required
      columns of a candidate schema against a set of actual headers, naming each
      unmatched column's declared aliases and its closest actual candidates with
      ``difflib`` similarity scores, plus the unrecognized actual columns.
    - Render that report as a concise, professional explanation string.

Scope boundaries:
    - Pure logic only. No I/O, no logging, no wall-clock, no randomness.
    - Depends only on the standard library, the Feature A schema model, and the
      additive :mod:`src.etl_column_probe`. It does not import or modify the ETL
      loaders, transforms, GUI, or CLI, and it does not modify
      :mod:`src.etl_columns`.

Determinism:
    - Candidate ordering, tie-breaks, and report ordering are derived only from
      the inputs; no clock or RNG is consulted.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src._schema_matching_helpers import coverage_score
from src.etl_column_probe import probe_columns
from src.etl_columns import DEFAULT_THRESHOLD, normalize_name

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.schema_model import SchemaDefinition
    from src.schema_registry import SchemaRegistry

# Default number of closest actual candidates reported per unmatched required
# column. The report is an operator aid, so a small fixed cap keeps the rendered
# explanation readable while still surfacing the most plausible corrections.
DEFAULT_MAX_CANDIDATES: int = 3


@dataclass(frozen=True)
class CandidateScore:
    """One actual header proposed as a near-miss for an unmatched column.

    Purpose:
        Pair an actual source header with its normalized ``difflib`` similarity
        to an unmatched required column so the report can rank plausible
        corrections.

    Attributes:
        actual_name: The actual source header (verbatim, source casing).
        score: The :class:`difflib.SequenceMatcher` ratio on normalized names,
            in ``[0.0, 1.0]``. A near-miss reported here is below the matching
            threshold (otherwise it would have bound).
    """

    actual_name: str
    score: float


@dataclass(frozen=True)
class UnmatchedColumn:
    """A required column that no actual header resolved, with its near-misses.

    Purpose:
        Carry everything an operator needs to correct one unmatched required
        column: its canonical name, the aliases the schema declared for it, and
        the closest actual headers with similarity scores.

    Attributes:
        canonical_name: The canonical name of the unmatched required column.
        aliases: The declared match aliases for the column, in schema order.
        candidates: Closest actual headers with descending similarity scores,
            capped at the report's ``max_candidates``.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    candidates: tuple[CandidateScore, ...]


@dataclass(frozen=True)
class MismatchReport:
    """A structured, renderable explanation of why headers did not fully match.

    Purpose:
        Explain a schema non-match. For each unmatched required column it records
        the canonical name, declared aliases, and the closest actual candidates
        with similarity scores; it also lists the actual headers that no required
        column claimed.

    Responsibilities:
        - Hold the structured non-match data as immutable value objects.
        - Render a concise, professional, human-readable explanation via
          :meth:`render`.

    Usage:
        Built by :func:`build_mismatch_report` (and, in later phases, attached to
        a match result). Treated as an immutable value object.

    Attributes:
        unmatched_required: One :class:`UnmatchedColumn` per required column that
            did not bind, in schema-declaration order.
        unrecognized_actual: Actual headers that no required column claimed, in
            source order.
    """

    unmatched_required: tuple[UnmatchedColumn, ...]
    unrecognized_actual: tuple[str, ...]

    def render(self) -> str:
        """Render the report as a concise, professional explanation string.

        Produces a multi-line, human-readable summary that names each unmatched
        required column, its declared aliases, and its closest actual candidates
        with similarity scores, followed by the unrecognized actual headers.
        The wording is factual and neutral per the repository tonality policy.

        Returns:
            A non-empty explanation string. When there are no unmatched required
            columns and no unrecognized headers, returns a short all-matched
            confirmation line.
        """
        # A fully matched probe yields an empty report; state that plainly rather
        # than rendering empty sections.
        if not self.unmatched_required and not self.unrecognized_actual:
            return "All required columns matched; no unrecognized columns."

        lines: list[str] = []

        # Render each unmatched required column with its aliases and ranked
        # near-misses so an operator can identify the likely source correction.
        if self.unmatched_required:
            lines.append("Unmatched required columns:")
            for column in self.unmatched_required:
                lines.append(self._render_unmatched_column(column))

        # List unrecognized headers separately; these are present in the source
        # but claimed by no required column.
        if self.unrecognized_actual:
            joined = ", ".join(self.unrecognized_actual)
            lines.append(f"Unrecognized actual columns: {joined}.")

        return "\n".join(lines)

    @staticmethod
    def _render_unmatched_column(column: UnmatchedColumn) -> str:
        """Render a single unmatched required column as one explanation line.

        Args:
            column: The unmatched required column to render.

        Returns:
            A single line naming the column, its declared aliases (when any), and
            its closest actual candidates with two-decimal similarity scores.
        """
        # Aliases are optional; include them only when declared so the line stays
        # concise for columns that rely solely on the canonical name.
        if column.aliases:
            alias_text = f" (aliases: {', '.join(column.aliases)})"
        else:
            alias_text = ""

        # Candidates may be empty when no actual header has any similarity; report
        # that explicitly rather than emitting a dangling "closest:" fragment.
        if column.candidates:
            candidate_text = ", ".join(
                f"{candidate.actual_name} ({candidate.score:.2f})"
                for candidate in column.candidates
            )
            closest = f"closest actual: {candidate_text}"
        else:
            closest = "no close actual candidates"

        return f"  - {column.canonical_name}{alias_text}; {closest}."


def _required_columns(schema: SchemaDefinition) -> list[tuple[str, tuple[str, ...]]]:
    """Return the required columns of a schema as (canonical_name, aliases).

    A required column is any :class:`src.schema_model.ColumnSpec` whose
    ``required`` flag is set; drop columns and optional columns do not contribute
    to a mismatch report.

    Args:
        schema: The candidate schema to inspect.

    Returns:
        A list of ``(canonical_name, aliases)`` pairs in schema-declaration order
        for every required column.
    """
    # Preserve declaration order so the rendered report is stable and matches the
    # schema author's intent.
    return [
        (column.canonical_name, column.aliases)
        for column in schema.columns
        if column.required
    ]


def _closest_candidates(
    target_norm: str,
    actual: Sequence[str],
    actual_norms: Sequence[str],
    max_candidates: int,
) -> tuple[CandidateScore, ...]:
    """Rank actual headers by normalized similarity to one target name.

    Args:
        target_norm: The normalized canonical name being matched.
        actual: The actual headers (verbatim), index-aligned to ``actual_norms``.
        actual_norms: Normalized actual headers, index-aligned to ``actual``.
        max_candidates: Maximum number of candidates to return.

    Returns:
        The closest actual headers as :class:`CandidateScore` objects sorted by
        descending score, capped at ``max_candidates``. Ties in score preserve
        source order because the underlying sort is stable.
    """
    # Score every actual header against the target so the operator sees the most
    # plausible corrections, even when all of them fall below the bind threshold.
    scored: list[CandidateScore] = []
    for index, norm in enumerate(actual_norms):
        ratio = difflib.SequenceMatcher(None, target_norm, norm).ratio()
        scored.append(CandidateScore(actual_name=actual[index], score=ratio))

    # Sort by descending score; Python's sort is stable, so equal scores keep
    # their source order, preserving determinism without a clock or RNG.
    scored.sort(key=lambda candidate: candidate.score, reverse=True)
    return tuple(scored[:max_candidates])


def build_mismatch_report(
    actual: Sequence[str],
    schema: SchemaDefinition,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> MismatchReport:
    """Build a structured mismatch report for a schema against actual headers.

    Probes the schema's required columns against the actual headers and, for each
    required column that does not bind, records its declared aliases and its
    closest actual candidates (similarity below ``threshold``). Also records the
    actual headers that no required column claimed.

    Args:
        actual: The actual source headers, in source order.
        schema: The candidate schema whose required columns are evaluated.
        threshold: Minimum normalized similarity ratio for a bind (default
            :data:`src.etl_columns.DEFAULT_THRESHOLD`); used by the probe to
            decide which required columns are unmatched.
        max_candidates: Maximum number of closest candidates reported per
            unmatched required column (default :data:`DEFAULT_MAX_CANDIDATES`).

    Returns:
        A :class:`MismatchReport` describing the unmatched required columns and
        the unrecognized actual headers. An empty report (no unmatched required
        columns, no unrecognized headers) indicates a full required-column match.
    """
    required = _required_columns(schema)
    required_names = [name for name, _ in required]

    # Probe only the required columns; optional/drop columns must not turn a
    # well-formed source into a reported mismatch.
    probe = probe_columns(actual, required_names, threshold=threshold)

    actual_list = list(actual)
    actual_norms = [normalize_name(name) for name in actual_list]
    aliases_by_name = dict(required)

    # Build one UnmatchedColumn per required column the probe could not bind,
    # ranking the closest actual headers as candidate corrections.
    unmatched: list[UnmatchedColumn] = []
    for name in probe.unmatched_expected:
        candidates = _closest_candidates(
            normalize_name(name), actual_list, actual_norms, max_candidates
        )
        unmatched.append(
            UnmatchedColumn(
                canonical_name=name,
                aliases=aliases_by_name.get(name, ()),
                candidates=candidates,
            )
        )

    return MismatchReport(
        unmatched_required=tuple(unmatched),
        unrecognized_actual=tuple(probe.unmatched_actual),
    )


@dataclass(frozen=True)
class MatchResult:
    """The outcome of scoring a set of headers against schema candidates.

    Purpose:
        Carry the best-matching schema (when any candidate scored above zero
        coverage, or when candidates exist), its coverage score, and the mismatch
        report explaining any unmatched required columns for that schema.

    Usage:
        Returned by :func:`find_best_match` and
        :func:`find_best_match_in_registry`. Treated as an immutable value
        object.

    Schema-acceptance policy:
        The result always reports the highest-scoring candidate and its
        coverage; it does not itself reject a low score. Callers decide whether
        ``score`` clears their acceptance bar. When the candidate list is empty,
        ``schema`` is ``None`` and ``score`` is ``0.0``.

    Attributes:
        schema: The highest-scoring candidate schema, or ``None`` when no
            candidates were supplied.
        score: The required-column coverage fraction of the selected schema, in
            ``[0.0, 1.0]``; ``0.0`` when ``schema`` is ``None``.
        report: The mismatch report for the selected schema (an empty report
            when every required column matched). For an empty candidate list the
            report is empty.
    """

    schema: SchemaDefinition | None
    score: float
    report: MismatchReport


def find_best_match(
    headers: Sequence[str],
    schemas: Sequence[SchemaDefinition],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> MatchResult:
    """Select the schema whose required columns best cover the headers.

    Scores each candidate by the fraction of its required columns that resolve
    to an actual header (canonical name or any declared alias), then returns the
    highest-scoring candidate with its coverage score and mismatch report. Ties
    break deterministically by newer schema ``version`` (descending, compared as
    text), then by ``name`` (ascending). No wall-clock or RNG is consulted, so
    repeated calls on the same inputs return identical results.

    Args:
        headers: The actual source headers, in source order.
        schemas: The candidate schemas to score. May be empty.
        threshold: Minimum normalized similarity ratio for a required column to
            count as matched (default :data:`src.etl_columns.DEFAULT_THRESHOLD`).

    Returns:
        A :class:`MatchResult`. When ``schemas`` is empty, ``schema`` is ``None``,
        ``score`` is ``0.0``, and ``report`` is an empty report. Otherwise the
        result holds the highest-scoring candidate, its coverage fraction, and
        the mismatch report for that candidate.
    """
    # An empty candidate list cannot select anything; return the explicit
    # no-match result rather than raising.
    if not schemas:
        return MatchResult(
            schema=None,
            score=0.0,
            report=MismatchReport(unmatched_required=(), unrecognized_actual=()),
        )

    actual_norms = [normalize_name(header) for header in headers]

    # Score every candidate up front so the tie-break can compare scores. The
    # score is the required-column coverage fraction with alias support.
    scored: list[tuple[SchemaDefinition, float]] = []
    for schema in schemas:
        score = coverage_score(actual_norms, _required_columns(schema), threshold)
        scored.append((schema, score))

    # Select deterministically: highest coverage first, then newer version, then
    # lexicographically smaller name. Sorting ascending on (-score, ...) with
    # version descending requires a composite key; build it explicitly so the
    # ordering rationale is clear and stable.
    best_schema, best_score = scored[0]
    for schema, score in scored[1:]:
        if _is_better_candidate(schema, score, best_schema, best_score):
            best_schema, best_score = schema, score

    report = build_mismatch_report(headers, best_schema, threshold=threshold)
    return MatchResult(schema=best_schema, score=best_score, report=report)


def _is_better_candidate(
    schema: SchemaDefinition,
    score: float,
    best_schema: SchemaDefinition,
    best_score: float,
) -> bool:
    """Decide whether a candidate should replace the current best.

    The decision criteria, in priority order: a strictly higher coverage score
    wins; on an equal score the newer ``version`` (greater as text) wins; on an
    equal version the lexicographically smaller ``name`` wins. The ordering is
    total and input-derived, so selection is deterministic.

    Args:
        schema: The candidate being considered.
        score: The candidate's coverage score.
        best_schema: The current best schema.
        best_score: The current best score.

    Returns:
        ``True`` when ``schema`` should replace ``best_schema``.
    """
    # Primary key: higher coverage always wins outright.
    if score != best_score:
        return score > best_score

    # Secondary key: equal coverage resolves to the newer (greater) version. The
    # version is compared as text, matching the model's free-form version field.
    if schema.version != best_schema.version:
        return schema.version > best_schema.version

    # Tertiary key: equal version resolves to the lexicographically smaller name
    # so the result is stable and reproducible.
    return schema.name < best_schema.name


def find_best_match_in_registry(
    headers: Sequence[str],
    registry: SchemaRegistry,
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> MatchResult:
    """Match headers against every schema saved in a Feature A registry.

    Loads each candidate schema from the registry via the public
    :meth:`src.schema_registry.SchemaRegistry.list_schemas` and
    :meth:`src.schema_registry.SchemaRegistry.load` API, then delegates scoring
    and selection to :func:`find_best_match`. The registry's own injected file
    store is the only I/O boundary; this function adds none. Determinism follows
    from ``list_schemas`` returning a sorted order and ``find_best_match`` being
    input-deterministic.

    Args:
        headers: The actual source headers, in source order.
        registry: The Feature A :class:`src.schema_registry.SchemaRegistry` to
            load candidate schemas from.
        threshold: Minimum normalized similarity ratio for a required column to
            count as matched (default :data:`src.etl_columns.DEFAULT_THRESHOLD`).

    Returns:
        A :class:`MatchResult`. When the registry holds no schemas, ``schema`` is
        ``None``, ``score`` is ``0.0``, and ``report`` is empty.
    """
    # Load every registered schema by name; list_schemas is already sorted, so the
    # candidate order is deterministic before find_best_match applies tie-breaks.
    schemas = [registry.load(name) for name in registry.list_schemas()]
    return find_best_match(headers, schemas, threshold=threshold)
