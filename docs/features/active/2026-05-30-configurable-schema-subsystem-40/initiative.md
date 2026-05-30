# configurable-schema-subsystem - Initiative Overview

- Issue: #40
- Owner: drmoisan
- Last Updated: 2026-05-30

## Goal & Outcomes

Replace the hardcoded AOP/LE input schemas with a configurable, user-buildable
schema subsystem so that drifted or slightly different input formats can be
onboarded without code changes, while still producing the exact canonical output
contract the downstream mix pipeline requires. Outcomes:

- Schemas are persisted, configurable definitions in a shared registry directory.
- New files are matched to the best schema automatically; non-matches are
  explained and a new schema can be built point-and-click.
- Dedup, column-building, and runtime formulas are declared per schema.
- Existing AOP/LE behavior is reproduced exactly by bundled default schemas.

## Decomposition (Child Features/Workstreams)

- **Feature A — Schema model + shared-registry persistence + bundled defaults** - `../<A-folder>/`
- **Feature B — Configurable matching + best-match discovery + mismatch explanation** - `../<B-folder>/`
- **Feature C — Configurable ETL core (dedup policy + column builder + asteval formula engine + ratio recompute)** - `../<C-folder>/`
- **Feature D — GUI schema builder + manual column-matching + runtime formula entry** - `../<D-folder>/`

Dependencies: strictly linear. A → B → C → D. Each builds on the prior; they
ship together under epic #40 on a single integration branch.

## Cross-Cutting Constraints & Assumptions

- New logic lives in new modules; `src/normalize_le.py` is at the 500-line ceiling.
- `asteval` is an approved new dependency (user, 2026-05-30) for the formula engine only.
- The configurable loader must satisfy the canonical downstream output contract
  (`mix_transforms.pivot_le`/`pivot_aop`, `mix_lookups.*`).
- Ratio / per-unit / %GS measures are recomputed post-aggregation from summed $
  and volume with safe-division (denominator null or <= 0 yields 0), never summed.
- The LE as-built quirk (Super Category and PPG both from source PPG) must be
  expressible in a schema.
- Pyright strict; JSON round-trip behind a typed adapter; >=85% line / >=75% branch coverage.
- PySide6 GUI tests require the documented CI system libs and `QT_QPA_PLATFORM=offscreen`.

## Milestones & Status

- M1 Feature A (schema model + persistence + bundled defaults) - Not started
- M2 Feature B (matching + discovery + explanation) - Not started
- M3 Feature C (configurable ETL core) - Not started
- M4 Feature D (GUI schema builder + manual matching + formula entry) - Not started
- M5 Epic integration validation + single PR to main - Not started

## Initiative-Level Validation

- End-to-end: a drifted input file is matched (or a new schema is built point-and-click),
  loaded through the configurable loader, deduplicated per policy, derived columns
  computed, and the resulting tables drive the existing mix pipeline to a CHECK result.
- Integration: bundled default AOP/LE schemas reproduce existing fixtures exactly.
- Determinism/Regression: existing CLI loaders and the current test suite remain green.
- Error handling/Resilience: non-matching files produce a structured, human-readable
  explanation; unsafe formulas are rejected by the sandboxed evaluator.

## Notes / Follow-Ups

- Research basis: `artifacts/research/2026-05-29-configurable-schema-subsystem-research.md`.
- Design decisions (user, 2026-05-30): shared-registry persistence (1b), asteval
  formula engine (2b), run all four features end-to-end (3b).
- Formula design input: `Rate_Impacts_corrected.m` safeDiv ratio-recompute pattern.
