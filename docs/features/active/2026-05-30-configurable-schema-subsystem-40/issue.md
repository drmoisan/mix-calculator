# configurable-schema-subsystem (Issue #40)

- Date captured: 2026-05-30
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/configurable-schema-subsystem/ (Issue #40)
- Promotion target: **epic** (decomposes into 4 features A-D)
- Work mode: full

- Issue: #40
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/40
- Last Updated: 2026-05-30
- Work Mode: full-feature

## Problem / Why

The pipeline currently hardcodes the AOP and LE input schemas as constant lists
in `src/_load_aop_helpers.py` and `src/normalize_le.py`. Real input files arrive
with unstable structure: column names drift, columns are missing, and slightly
different formats appear. Hardcoding a fixed schema per source forces a code
change for every structural variation. The user needs schemas to be
**configurable and user-buildable at runtime**, with visual point-and-click
tooling, so that new or drifted input formats can be onboarded without code
changes while still producing the exact canonical output contract the downstream
mix pipeline requires.

## Proposed Behavior

A configurable schema subsystem that:

1. Represents each input schema as a persisted, configurable definition rather
   than hardcoded constants. A schema declares its essential (logical) columns,
   per-column match aliases/patterns, the business-key composition, a dedup
   policy, derived/calculated columns, and drop/sentinel rules.
2. On new-file load, identifies the **best matching** persisted schema by scoring
   resolved-column coverage. When no schema is a suitable match, it produces a
   human-readable explanation of **which** required columns failed to match and
   **where** (closest source-column candidates and similarity scores), then
   offers to create a new matching schema.
3. **Always deduplicates rows.** When rows share descriptive (dimension) fields
   but carry complementary data (typically a year-to-date half and a
   balance-of-year half), the schema declares per-measure whether the values are
   **additive** (summed) or **selected** from a specific discriminator value.
   Ratio / per-unit / %GS measures are NOT summed; they are dropped and
   **recomputed** after aggregation from the correctly-summed dollar and volume
   columns using safe-division semantics (denominator null or <= 0 yields 0),
   per the established `Rate_Impacts_corrected.m` pattern.
4. Provides a **column builder** to construct a missing column from other columns,
   and a **runtime formula engine** for calculated columns the source lacks
   (e.g. `YTG = May + ... + Dec`, per-unit and %GS ratios).
5. Persists schemas in a **shared registry location** (a common directory,
   independent of any single `.db` file) resolved via a settings/path mechanism.
6. Exposes a **visual, point-and-click schema builder** GUI and a **manual
   column-matching** dialog used when fuzzy heuristics do not resolve a column.

## Acceptance Criteria (early draft)

- [ ] Schemas are defined as persisted, configurable definitions (not hardcoded constants).
- [ ] Bundled default AOP and LE schemas reproduce current pipeline output exactly (backward compatible).
- [ ] On file load, the system selects the best-matching schema by coverage score.
- [ ] When no schema matches, the system explains which required columns failed and the closest candidates.
- [ ] Dedup policy is declared per schema: additive vs. select-from-discriminator per measure.
- [ ] Ratio/per-unit/%GS columns are recomputed post-aggregation from summed $ and volume with safe-division.
- [ ] A column builder can construct a missing column from other columns.
- [ ] A runtime formula engine evaluates user-entered formulas for calculated columns.
- [ ] Schemas persist to a shared registry directory resolved via a settings/path mechanism.
- [ ] A visual point-and-click schema-builder GUI creates and edits schemas.
- [ ] A manual column-matching dialog overrides fuzzy matching when it fails.
- [ ] All new schema modules are Pyright-clean, formatted, and meet >=85% line / >=75% branch coverage.

## Constraints & Risks

- `src/normalize_le.py` is at the 500-line ceiling; new logic must live in new modules.
- New dependency `asteval` approved by the user (2026-05-30) for the formula engine only.
- The configurable loader must still satisfy the canonical downstream output contract consumed by `mix_transforms.pivot_le` / `pivot_aop` and `mix_lookups.*` (raises KeyError on missing required columns).
- The LE as-built quirk (Super Category and PPG both populated from source PPG) must be explicitly representable in the schema.
- Pyright runs in strict mode; the JSON round-trip must be type-safe behind a typed adapter.
- PySide6 GUI tests require the documented CI system libraries and `QT_QPA_PLATFORM=offscreen`.
- Formula-engine security: even with asteval, user-entered expressions must be sandboxed and fuzz-tested.

## Test Conditions to Consider

- [ ] Bundled-default schemas reproduce existing AOP/LE fixtures byte-for-byte vs. current loaders.
- [ ] Schema discovery scores and explanation report for matching and non-matching headers.
- [ ] Dedup additive vs. select-from-discriminator on complementary YTD/BOY rows.
- [ ] Ratio recomputation from summed dollars/volume with safe-division edge cases (zero/negative/null denominators).
- [ ] Formula engine: valid expressions, rejected unsafe expressions, columns with spaces/special chars (`SKU #`, `Off Invoice $`).
- [ ] Schema registry load/save/list round-trip in the shared directory.
- [ ] GUI schema-builder and manual-matching dialogs via pytest-qt.

## Next Step

- [ ] Promote to GitHub issue (epic).
- [ ] Create `docs/features/active/` epic folder and per-feature folders (A-D).