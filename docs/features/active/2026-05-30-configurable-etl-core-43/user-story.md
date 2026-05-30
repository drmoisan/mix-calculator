# `configurable-etl-core` — User Story

- Issue: #43
- Parent: Epic #40
- Owner: drmoisan
- Status: Ready for planning
- Last Updated: 2026-05-30

## Story Statement

- As a user with an input file in a slightly different format, I want the pipeline
  to process it using a configurable schema — matching columns, deduplicating
  complementary rows, building missing columns, and computing formulas — so that
  I get correct normalized output without a code change.
- As a maintainer, I want the configurable loader to reproduce the current AOP
  and LE outputs exactly via the bundled default schemas, so that backward
  compatibility is proven before any code depends on the new path.

## Problem / Why

Features A and B model and match schemas but do not yet process data with them.
Feature C makes schemas executable: it deduplicates, builds columns, and
evaluates user formulas, while guaranteeing the existing AOP/LE behavior is
reproduced exactly. The formula engine uses the user-approved `asteval`
dependency, sandboxed behind a typed adapter.

## Personas & Scenarios

- Persona: analyst onboarding a drifted LE export.
  - Cares about: correct dedup of YTD/BOY rows; correct derived totals and
    ratios; no silent data corruption.
  - Constraints: no code changes; deterministic, auditable results.
- Scenario: the analyst's file has the same business meaning as LE but is missing
  the `YTG` column and labels two measures differently. The matched schema
  declares `YTG` as a derived column (`sum(May..Dec)`), maps the renamed columns
  via aliases, and collapses the YTD/BOY rows additively. `SchemaLoader` produces
  the canonical LE frame; a ratio column the analyst defines is recomputed after
  aggregation with `safe_div`, never summed.

## Acceptance Criteria

- [x] AC1: `SchemaLoader(default_le)` reproduces `normalize_le.normalize` output exactly on the existing LE fixtures (columns, order, values, PPG quirk, derived YTG, dropped YTD/YTG).
- [x] AC2: `SchemaLoader(default_aop)` reproduces `load_aop`'s validated frame exactly on the existing AOP fixtures.
- [x] AC3: Dedup honors `additive` vs `select_from` per measure; `mode == none` preserves rows; dimensions taken from the first row.
- [x] AC4: The column builder constructs a missing column from other columns via a derived-column expression.
- [x] AC5: Non-additive (ratio/per-unit/%GS) measures are recomputed post-aggregation from summed dollars/volume with safe-division; zero/negative/null/NaN denominators yield 0.
- [x] AC6: The formula engine evaluates valid expressions including columns with spaces/special characters (`SKU #`, `Off Invoice $`), and rejects syntactically invalid, disallowed-construct, or unknown-column expressions with descriptive `FormulaError`s.
- [x] AC7: `asteval` is added to `pyproject.toml`; a local `typings/asteval/__init__.pyi` stub makes Pyright strict pass with no suppression.
- [x] AC8: An integration test feeds `SchemaLoader` output through the existing pipeline transforms to a consistent result.
- [x] AC9: Formula-engine security is covered by fuzz/property tests (rejection of unsafe input; safe-division edge cases).
- [x] AC10: New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage; modules classified in `quality-tiers.yml` (formula engine + loader core T1, with a property test per pure function).
- [x] AC11: Existing test suite remains green; no existing loader, transform, CLI, or GUI behavior is modified.

## Non-Goals

- No GUI dialogs or manual matching (Feature D).
- No change to existing CLI loaders, `pipeline_service`, transforms, or the running GUI.
- No new persistence sink; the loader returns a DataFrame.
