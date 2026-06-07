# Phase 0 — AC-2 Context (Auto-Selection on Activation)

Timestamp: 2026-06-05T23-08

## AC-2 statement from `spec.md` (section "Behavior", item 2)

> 2. **Schema auto-selection.** When a source tab is activated, the best-matching
>    schema is auto-selected from the registry. This finishes wiring the
>    `SourceSelectionPresenter.on_schema_discovery` seam left unwired as #48
>    follow-up F2.

## Matching acceptance line from `user-story.md` (section "Acceptance Criteria")

> - [x] Activating a source tab auto-selects the best-matching schema; placeholder
> - [x] shown when none matches.

## Relevance to this remediation

The cycle-3 defensive guard (B1) must preserve AC-2 for the populated-selection case:
when a file AND a real worksheet are selected and the header matches a schema, activation
must still auto-select the matched schema and enable Import. The guard only suppresses
discovery when `path` or `sheet` is blank/whitespace (placeholder / combo-population
events that fire `currentTextChanged` before a worksheet is chosen). AC-2 re-confirmation
is performed in Phase 3 ([P3-T1], [P3-T2]).
