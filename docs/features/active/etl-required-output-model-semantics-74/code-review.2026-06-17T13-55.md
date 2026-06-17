# Code Review: etl-required-output-model-semantics (#74, epic child CF1)

**Review Date:** 2026-06-17
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Feature Folder Selection Rule:** Selected by the issue-#74 suffix matching the branch name and the active feature folder carrying the CF1 scoping docs.
**Base Branch:** `main` (`0a47fef`)
**Head Branch:** `refactor/etl-required-output-model-semantics-74` (`1182cad`)
**Review Type:** Post-remediation re-review (cycle 3)

---

## Executive Summary

CF1 of epic #74 redefines the schema `required` flag to mean "required OUTPUT identity column" (format version `2.0 -> 3.0`), adds a `SchemaDefinition.required_output_columns()` accessor, and adds a deterministic forward migration `required(3.0) = required(2.0) AND in_output(2.0)` that upgrades pre-3.0 persisted schemas on load while preserving `in_output`. The bundled `default_le` schema is updated to 3.0 with months/`FY`/quarters/`Super Category` set `required: false` (`in_output: true`) and the six output-identity dimensions kept `required: true`. The diff is small and well-scoped: 3 source files, 1 JSON file, 4 test files.

This is the cycle-3 re-review. The prior review (`2026-06-17T12-35`) raised one Major finding: the `default_aop.schema.json` flags were not aligned to the new meaning. That finding is resolved by descoping AOP minimization to CF2 (the loader couples emitted column order and which-columns-to-keep to `required`, so AOP minimization needs a CF2 loader change) and reverting the CF1 AOP version bump. This review independently confirmed `git diff main -- src/schemas/default_aop.schema.json` is empty and that the loader genuinely reads `column.required` to build `required_expected` and the column-keep/order plan, corroborating the descope rationale.

**What changed:**
- `src/schema_model.py`: `SCHEMA_FORMAT_VERSION "2.0" -> "3.0"`; module/class docstrings define 3.0 `required`-output semantics; new `required_output_columns() -> tuple[str, ...]`.
- `src/_schema_model_specs.py`: `ColumnSpec.required`/`in_output` docstrings rewritten to the required-output meaning.
- `src/schema_serialization.py`: new `_version_predates_required_output`; `migrate_required` threaded through deserialization; required-output recompute applied only for pre-3.0 sources.
- `src/schemas/default_le.schema.json`: version 3.0; measure/derived columns `required: false`, identity dimensions `required: true`.
- `src/schemas/default_aop.schema.json`: reverted to `main` (zero diff).
- Tests: LE required-set/accessor/resolve tests, five migration tests, version assertion update.

**Top 3 risks:**
1. AOP `required`-flag minimization is deferred to CF2; until CF2 lands, AOP carries the old input-presence flags on disk (mitigated: on-load migration keeps loaded behavior identical; output parity holds). Tracked in `initiative.md`.
2. The `required_output_columns()` accessor returns only source `required` columns (derived contribution intentionally empty in CF1); future required-derived designations must extend it (documented in the docstring).
3. `schema_serialization.py` is at 497 lines, close to the 500-line cap; further serialization growth in later children should extract a helper module.

**PR readiness recommendation:** **Go** — The model-semantics scope is complete and clean; the single prior Major finding is resolved by a verified descope and revert; no blocking or material findings remain.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/schemas/default_aop.schema.json` | whole file | AOP `required` flags remain at the pre-3.0 input-presence meaning on disk; minimization deferred to CF2. | No CF1 action; CF2 owns the loader decouple and AOP minimization. | Loader couples column order/keep to `required`; minimizing AOP without the loader change reorders output. | `git diff main -- src/schemas/default_aop.schema.json` empty; descope note in `spec.md`; `_schema_loader_helpers.py:172-194`. |
| Info | `src/schema_serialization.py` | file length | File is 497 lines, near the 500-line cap. | Extract a helper module before adding more serialization logic in later children. | Headroom is small for CF2-CF7 serialization work. | `awk END{print NR} src/schema_serialization.py` = 497. |
| Nit | `src/schema_model.py` | `required_output_columns()` | Derived-required contribution is a hard-coded empty tuple in CF1. | Acceptable for CF1; extend when a schema designates a required derived output. | Keeps the accessor structurally extensible without current behavior change. | `src/schema_model.py` accessor body; docstring documents the intent. |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The migration is expressed as a single, auditable rule (`required AND in_output`) applied only when the source predates 3.0, with the gate computed once per schema (`migrate_required`) and threaded by keyword argument into per-column reconstruction. This keeps the mapping consistent across all columns and avoids per-column re-derivation.
- The version gate `_version_predates_required_output` is conservative for unparseable major versions (treated as legacy and migrated), which is the safe default for hand-authored/legacy inputs, and it is explicitly tested.
- `required_output_columns()` is a pure, read-only accessor that reads only `required` (never `in_output`), correctly excluding the emitted-but-not-required `Super Category` and the measure columns. Declared order is preserved.
- Docstrings on `ColumnSpec`, `SchemaDefinition`, and `_object_to_column` were updated to the 3.0 meaning, including the precise note that the bundled `default_le` file is hand-authored at 3.0 (the generic migration is for older *user* schemas, not the source of the bundled flag values). This prevents a future maintainer from assuming the bundled flags come from the migration.

#### Typing and API notes

- New public surface is `SchemaDefinition.required_output_columns() -> tuple[str, ...]` and the `SCHEMA_FORMAT_VERSION` value change. Both are additive; no constructor signature changed. `_version_predates_required_output` is module-internal. Typing is precise; Pyright reports 0 errors.

#### Error handling and logging

- The resolve gate continues to raise `ValueError` when a required-output dimension is absent (verified by `test_default_le_resolve_raises_when_required_dimension_absent`). Serialization raises `SchemaSerializationError` on malformed key objects (pre-existing path). No broad catches; no print/logging added.

---

## Test Quality Audit

The added tests cover the full behavior surface of the change: the LE required-output set and accessor, the resolve gate (positive: months absent resolves; negative: missing `Customer` raises), and the migration mapping across five scenarios (drop-when-not-emitted, stay-when-emitted, 3.0 pass-through, round-trip idempotence, unparseable-version-as-legacy). The resolve tests exercise the real production path (`resolve_and_rename`), not a stub, so they verify the change is wired into the loader rather than merely covered.

### Reviewed test and QA artifacts

- `tests/test_schema_migration.py` — five migration scenarios; pure in-memory JSON; covers the new `_version_predates_required_output` branches including the `except ValueError` path.
- `tests/test_schema_loader_core.py` — `resolve_and_rename` positive/negative against bundled `default_le`; confirms required-output gating is live in the loader.
- `tests/test_default_schemas.py` — LE flag assertions and accessor; AOP-loads-at-3.0 assertion confirms the on-load migration with the file at on-disk 2.0.
- `evidence/qa-gates/aop-diff-after-revert.2026-06-17T13-40.md` — `git diff main -- src/schemas/default_aop.schema.json` exit 0/empty (revert verified).
- `evidence/qa-gates/final-pytest.2026-06-17T13-40.md` — 1058 passed with coverage.

### Quality assessment prompts

- **Determinism:** No wall-clock, RNG, network, or filesystem use; literal frames/JSON strings.
- **Isolation:** Each test asserts a single behavior.
- **Speed:** Full suite 38.72s; migration tests are in-memory.
- **Diagnostics:** Assertions carry identifying context (column name) so a failure names the offending column.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff contains only schema model/serialization/test code and JSON flags. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess/shell construction in the diff. |
| Input validation at boundaries | ✅ PASS | Resolve raises on missing required-output dimension; serialization rejects unknown keys and malformed key objects. |
| Error handling remains explicit | ✅ PASS | Specific `ValueError`/`SchemaSerializationError`; no broad catch. |
| Configuration / path handling is safe | ✅ PASS | Bundled schema read is read-only; no path interpolation introduced. |

---

## Research Log

No external research required. The change is internal to the schema model/serialization subsystem; all evidence came from diff inspection, toolchain output, coverage data, schema-flag dumps, and feature-folder artifacts.

---

## Verdict

The CF1 model-semantics change is ready for normal PR flow. The implementation is small, strongly typed, well-documented, and fully covered, with the new code at 100% coverage and the full suite green in a single toolchain pass. Bundled-schema output parity is preserved for both LE and AOP. The prior Major finding (AOP flags not aligned) is resolved by a documented contract-level descope to CF2 plus a verified revert that leaves the AOP file with zero diff against `main`. This conclusion is consistent with the Findings Table (no Blockers/Major) and the Go readiness recommendation.
