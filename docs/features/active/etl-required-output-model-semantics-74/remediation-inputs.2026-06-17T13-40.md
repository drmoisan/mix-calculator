# Remediation Inputs: etl-required-output-model-semantics (#74, epic child CF1) — cycle 3

**Entry timestamp:** 2026-06-17T13-40
**Feature folder:** `docs/features/active/etl-required-output-model-semantics-74/`
**Base branch:** `main` (`0a47fef`)
**Head:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)
**Supersedes:** cycles 1 and 2 (both failed — AOP required-flag minimization is blocked by a loader
ordering/which-columns-to-keep coupling that requires a CF2-scoped loader change).

## Resolution: descope AOP minimization from CF1 (orchestrator scope decision)

Verification across cycles 1–2 established that making `default_aop` measures `required: false`
reorders the SchemaLoader output for the `none`-dedup path, because `src/_schema_loader_helpers.py`
couples both the located-by-name / which-columns-to-keep decision and the emitted column ORDER to
the `required` flag. Decoupling needs a new schema-model located-by-name / presence-optional signal
plus a loader change — squarely CF2 (loader) scope, not CF1 (model semantics).

The orchestrator has already updated the contract to reflect the descope:
- `spec.md`: AOP removed from CF1 scope; AC #3 rescoped to `default_le`; descope note added.
- `initiative.md`: CF2 scope expanded to own the located-by-name/presence-optional signal, the
  loader ordering decouple, and the `default_aop` required-flag minimization.

Additionally, deserialization always sets in-memory `version = SCHEMA_FORMAT_VERSION` and runs the
`required = required AND in_output` migration for pre-3.0 sources; since every AOP measure is
`in_output: true`, the migration keeps them `required: true`. So whether the bundled `default_aop`
file is on-disk 2.0 or 3.0, the loaded AOP schema is functionally identical. CF1 therefore reverts
its only `default_aop` change (the version bump) so CF1 touches zero of the AOP schema file.

## Enumerated Fix List

### R1 — Revert the CF1 `default_aop` version bump (make CF1 touch zero of the AOP file)

- **File:** `src/schemas/default_aop.schema.json`
- **Action:** Restore the file to its `main` (`0a47fef`) state, i.e. `"version": "2.0"` with its
  original `required` flags unchanged. Equivalent to `git checkout main -- src/schemas/default_aop.schema.json`.
- **Rationale:** AOP minimization is deferred to CF2; CF1 must not leave a half-applied AOP change.
  The forward migration upgrades `default_aop` to 3.0 in memory on load, so behavior is unchanged.
- **Verification:** `git diff main -- src/schemas/default_aop.schema.json` is empty.

### R2 — Confirm the CF1 test suite remains green with the AOP file reverted

- **Files:** existing tests (no new AOP test is added in CF1; the cycle-1 R3 AOP accessor test is
  NOT added — it moves to CF2).
- **Key test to confirm:** `tests/test_default_schemas.py::test_bundled_defaults_are_current_format_with_structured_key_parts`
  must still pass — it asserts `default_aop` loads at `SCHEMA_FORMAT_VERSION` (3.0) via the
  on-load migration, which holds with the file at 2.0.
- **Action:** If any CF1 test was added that asserts the `default_aop` FILE is at 3.0 on disk or
  asserts AOP measures are `required: false`, update or remove it (such an assertion would be CF2's,
  not CF1's). Do not weaken any LE assertion.

## Verification

- `git diff main -- src/schemas/default_aop.schema.json` — empty.
- Full toolchain single clean pass: `poetry run black .` -> `poetry run ruff check .` ->
  `poetry run pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`.
  Coverage >= 85% line, >= 75% branch; no regression on changed lines.
- `default_le` and `default_aop` SchemaLoader parity tests pass unchanged (zero output regression).
- Spec DoD AC #3 (now LE-scoped) is `- [x]`.

## Do-Not-Do List

- Do not edit `src/_schema_loader_helpers.py` or any loader code (that is CF2).
- Do not add the AOP `required_output_columns()` accessor test (moves to CF2).
- Do not change any emitted output for AOP or LE; parity tests are the oracle.
- Do not weaken or remove existing LE tests, parity assertions, or coverage thresholds.
- Do not introduce suppressions; do not add dependencies; do not exceed the 500-line cap.
- Do not extend scope into CF2-CF7.

## Notes for the Planner

- This cycle is a revert plus a green-toolchain confirmation; no production logic changes.
- The model/serialization code (`schema_model.py`, `_schema_model_specs.py`,
  `schema_serialization.py`) already correctly implements the 3.0 semantics and migration; leave
  them unchanged.
