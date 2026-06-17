# Code Review: etl-required-output-model-semantics (#74, epic child CF1)

**Review Date:** 2026-06-17
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Feature Folder Selection Rule:** Caller-designated active folder; suffix `-74` matches the canonical issue number and the branch name `refactor/etl-required-output-model-semantics-74`.
**Base Branch:** `main` (`0a47fef`)
**Head Branch:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)
**Review Type:** Initial review

---

## Executive Summary

This change implements the foundational semantic of epic #74: the schema `required` flag is redefined from input-presence to "required OUTPUT identity column" (one value column plus its dimension columns), `in_output` continues to mean "emitted in output (may be true without `required`)," and `SCHEMA_FORMAT_VERSION` is bumped `2.0 -> 3.0`. A deterministic forward migration recomputes `required(3.0) = required(2.0) AND in_output(2.0)` for pre-3.0 sources while preserving `in_output`, so emitted output is unchanged for upgraded persisted schemas. A read-only `SchemaDefinition.required_output_columns()` accessor exposes the ordered identity set. The bundled `default_le` schema relaxes its month/quarter/FY measures (and the derived `Super Category`) to `required: false` while keeping `in_output: true`.

**What changed:**
Three source modules (`schema_model.py`, `_schema_model_specs.py`, `schema_serialization.py`), two bundled schema JSON files (`default_le`, `default_aop`), and four test files. The migration and accessor are small, pure, well-typed additions. Coverage on the changed modules is 98-100% line; the suite is green in a single pass (1058 passed), independently verified. Loader output parity for both bundled schemas is preserved (zero regression).

**Top 3 risks:**
1. `default_aop.schema.json` was only version-bumped; its `required` flags were not aligned to the 3.0 meaning, so the core semantic is applied inconsistently across the two bundled schemas (Major).
2. `schema_serialization.py` is at 497 lines, three lines under the 500-line cap; the next addition to this module risks breaching the cap and will need a helper-module extraction.
3. The migration treats any unparseable major version as legacy-and-migrate; a hand-authored 3.0 schema with a malformed version string would silently have its `required` flags recomputed. This is the documented, conservative choice and is tested, but it is a behavior worth keeping in mind for CF-series user-schema handling.

**PR readiness recommendation:** **Conditional Go** — mergeable on quality gates; align the `default_aop` `required` flags to 3.0 before merge for semantic consistency with `default_le`.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Major | `src/schemas/default_aop.schema.json` | whole file (version line + measure column `required` flags) | Version bumped to `3.0` but `required` flags not aligned to the 3.0 required-output meaning; measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4` remain `required: true` (old input-presence meaning), unlike the equivalent LE measures set to `required: false`. | Set AOP measure columns to `required: false` (keep `in_output: true`), preserve identity-dimension `required: true`, confirm parity unchanged, and add an AOP `required_output_columns()` assertion mirroring the LE test. | Spec Scope directs "align `required` flags to the new meaning" for AOP; leaving them as input-presence makes the foundational semantic inconsistent between the two bundled schemas and would cause an AOP source missing a month column to still fail at load while the equivalent LE source loads. | `git diff` of `default_aop.schema.json` shows only the `2.0`->`3.0` line; `python -c` dump shows `Jan..Dec`, `YTD`, `Q1..Q4` all `required=True`; spec.md Scope bullet for `default_aop.schema.json`. |
| Info | `src/schema_serialization.py` | file length | Module is 497 lines, near the 500-line cap. | Plan a helper-module extraction before the next serialization addition (CF2+). | Proactive cap management per general-code-change 500-line rule. | `wc -l src/schema_serialization.py` = 497. |
| Info | `src/schema_serialization.py` | `_version_predates_required_output` `except ValueError` | Unparseable major version is treated as pre-3.0 and migrated. | None required; behavior is documented and tested. Track for CF-series user-schema handling. | Conservative upgrade choice; could recompute `required` for a malformed-but-intended-3.0 input. | `tests/test_schema_migration.py::test_unparseable_version_is_treated_as_legacy`. |

No Blocker findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The migration is centralized: `_version_predates_required_output` computes the gate once in `_object_to_schema` and threads `migrate_required` (keyword-only) into every `_object_to_column` call, so every column reconstruction uses a single consistent decision.
- The mapping `required(3.0) = required(2.0) AND in_output(2.0)` is the minimal output-preserving rule and is implemented exactly as specified, with `in_output` passed through untouched.
- `required_output_columns()` reads only `required` in declared order and reserves an explicit (currently empty) required-derived contribution, which is a clean, typed extension point for later epic children without changing current behavior.
- The bundled `default_le` is hand-authored directly at 3.0 (not relying on the generic migration), and the code comments correctly distinguish the generic user-schema migration from the hand-authored bundled flag values, including why `Super Category` (a `copy_from: PPG` derived column) is authored `required: false`.

#### Typing and API notes

- New public surface is fully typed: `required_output_columns(self) -> tuple[str, ...]`; helper `_version_predates_required_output(version: str) -> bool`; `_object_to_column(obj, *, migrate_required: bool)`. No `Any` introduced; Pyright clean.
- No existing constructor signature changed; the addition is purely additive, consistent with the spec's "no change to existing constructor signatures."

#### Error handling and logging

- The new `except ValueError` is narrow (only the `int()` parse) and returns a conservative `True` rather than swallowing or re-raising silently; the rationale is documented. Existing `SchemaSerializationError`/`ValueError` contract paths are unchanged. No print/logging added (consistent with the pure-data nature of the module).

---

## Test Quality Audit

The test additions cover the new behavior comprehensively: the migration is exercised across drop-when-not-emitted, stay-when-emitted, 3.0 pass-through, round-trip stability, and unparseable-version-as-legacy; the accessor is asserted to return exactly the ordered LE identity dimensions and to exclude `Super Category` and the measures; loader positive/negative tests confirm a source missing only month/quarter columns now loads while a source missing the `Customer` identity dimension still raises. Bundled-schema parity tests confirm zero output regression for both schemas.

### Reviewed test and QA artifacts

- `tests/test_schema_migration.py` — five migration mapping cases plus three legacy-format cases; pure string-to-object transforms, deterministic, no temp files.
- `tests/test_default_schemas.py::test_default_le_required_output_columns_accessor` — asserts the accessor returns the ordered identity set and excludes measures/`Super Category`.
- `tests/test_schema_loader_core.py` — relaxed-required positive load and retained identity-required negative load.
- `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/coverage-delta.md` — baseline vs post-change coverage and no-regression-on-changed-lines analysis; figures independently confirmed.
- `evidence/qa-gates/final-bundled-parity.md` — bundled `default_le`/`default_aop` output parity, 36 passed.

### Quality assessment prompts

- **Determinism:** Schema JSON built from in-memory string literals; no clock/RNG/network/filesystem.
- **Isolation:** Each test asserts a single mapping or accessor behavior.
- **Speed:** Full suite 34.13s/1058 tests; the schema subset is sub-second.
- **Diagnostics:** Tuple/boolean equality assertions produce direct, actionable diffs.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff contains only schema flag/version edits and pure transforms; no credentials. |
| No unsafe subprocess or command construction | N/A | No subprocess or shell invocation in scope. |
| Input validation at boundaries | ✅ PASS | `require_str`/`optional_bool` typed accessors validate JSON fields; version parsed defensively. |
| Error handling remains explicit | ✅ PASS | Narrow `except ValueError`; existing raise paths preserved. |
| Configuration / path handling is safe | ✅ PASS | Bundled schemas read from packaged `src/schemas/`; no runtime temp files or user-path interpolation introduced. |

---

## Research Log

No external research was required. All conclusions are grounded in the branch diff, the spec/plan, the feature evidence artifacts, and an independent full-suite toolchain re-run.

---

## Verdict

The implementation is clean, well-typed, comprehensively tested, and preserves bundled-schema output parity with no regression on changed lines. It is ready for normal PR flow after one follow-up: align `default_aop.schema.json` `required` flags to the 3.0 required-output meaning so the foundational semantic is consistent across both bundled schemas. This is a Major spec-Scope item but does not block on quality gates (AOP output is unchanged and the DoD checklist, which enumerates only LE columns, is satisfied). Recommendation: Conditional Go.
