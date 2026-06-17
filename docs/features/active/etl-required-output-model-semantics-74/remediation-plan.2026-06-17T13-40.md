# Remediation Plan: etl-required-output-model-semantics (#74, epic child CF1) — cycle 3

- **Entry timestamp:** 2026-06-17T13-40 (matches `remediation-inputs.2026-06-17T13-40.md`)
- **Feature folder:** `docs/features/active/etl-required-output-model-semantics-74/`
- **Canonical issue:** #74
- **Primary input (contract):** `docs/features/active/etl-required-output-model-semantics-74/remediation-inputs.2026-06-17T13-40.md`
- **Base branch:** `main` (`0a47fef`)
- **Head:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)
- **Mode:** full-bug (spec-driven remediation; `spec.md` present, `user-story.md` not required)

## Cycle Objective

This cycle DESCOPES AOP required-flag minimization from CF1 (orchestrator decision; `spec.md`
and `initiative.md` are already updated). The work is a revert plus a green-toolchain
confirmation. NO production logic changes. CF1 must touch zero of the AOP schema file relative
to `main`.

The forward migration in `src/schema_serialization.py` always sets the in-memory
`version = SCHEMA_FORMAT_VERSION` and applies `required = required AND in_output` for pre-3.0
sources on load; since every AOP measure is `in_output: true`, the loaded AOP schema is
functionally identical whether the bundled file is on-disk 2.0 or 3.0. Reverting the file to 2.0
therefore changes no emitted output.

## Hard Constraints (from the inputs' Do-Not-Do list)

- Do NOT edit `src/_schema_loader_helpers.py` or any loader code (CF2 scope).
- Do NOT add the AOP `required_output_columns()` accessor test (moves to CF2).
- Do NOT change any emitted output for AOP or LE; parity tests are the oracle.
- Do NOT weaken or remove existing LE tests, parity assertions, or coverage thresholds.
- Do NOT introduce suppressions; do NOT add dependencies; do NOT exceed the 500-line cap.
- Do NOT extend scope into CF2–CF7.
- Leave `src/schema_model.py`, `src/_schema_model_specs.py`, `src/schema_serialization.py`
  unchanged.

## Acceptance Criteria (mapped to inputs R1/R2)

- **AC-R1:** `src/schemas/default_aop.schema.json` is restored to its `main` (`0a47fef`) state;
  `git diff main -- src/schemas/default_aop.schema.json` produces empty output.
- **AC-R2:** The full test suite stays green with AOP reverted. In particular
  `tests/test_default_schemas.py::test_bundled_defaults_are_current_format_with_structured_key_parts`
  still passes (it asserts `default_aop` loads at `SCHEMA_FORMAT_VERSION` via on-load migration,
  which holds with the file at 2.0). No CF1-added test asserts the `default_aop` FILE is 3.0 on
  disk or that AOP measures are `required: false`. No LE assertion is weakened.
- **AC-Toolchain:** A single clean toolchain pass (`black` → `ruff` → `pyright` → `pytest`
  with coverage) completes; line coverage >= 85%, branch coverage >= 75%; no regression on
  changed lines.

## Evidence Location Invariant

All evidence artifacts MUST be written under
`docs/features/active/etl-required-output-model-semantics-74/evidence/<kind>/` per
`.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing to `artifacts/baselines/`,
`artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical path is a policy violation.

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read the policy files in required order (`CLAUDE.md`,
  `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`,
  `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`,
  `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/quality-tiers.md`,
  `.claude/rules/tonality.md`). Write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/phase0-instructions-read.2026-06-17T13-40.md`
  containing `Timestamp:`, `Policy Order:`, and the explicit list of files read.
  Acceptance: the artifact exists and lists every policy file above.

- [x] [P0-T2] Capture the pre-revert state of the target file. Run
  `git diff main -- src/schemas/default_aop.schema.json` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/aop-diff-before-revert.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (the non-empty diff showing
  the CF1 version bump 2.0 → 3.0 still present at head).
  Acceptance: the artifact records a non-empty diff (the change R1 will revert).

- [x] [P0-T3] Capture the baseline formatting state. Run `poetry run black --check .` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/baseline-black.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
  Acceptance: the artifact records the exit code and pass/fail summary.

- [x] [P0-T4] Capture the baseline lint state. Run `poetry run ruff check .` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/baseline-ruff.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
  Acceptance: the artifact records the exit code and pass/fail summary.

- [x] [P0-T5] Capture the baseline type-check state. Run `poetry run pyright` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/baseline-pyright.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).
  Acceptance: the artifact records the exit code and error/warning counts.

- [x] [P0-T6] Capture the baseline test + coverage state. Run
  `poetry run pytest --cov --cov-branch --cov-report=term-missing` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/baseline-pytest.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` including the numeric
  passed/failed counts, total line coverage %, and total branch coverage %.
  Acceptance: the artifact records numeric coverage headline values (not placeholders).

---

### Phase 1 — R1 Revert AOP Schema to main

- [x] [P1-T1] Restore `src/schemas/default_aop.schema.json` to its `main` (`0a47fef`) state by
  running `git checkout main -- src/schemas/default_aop.schema.json`. This reverts the CF1
  version bump (3.0 → 2.0) and restores the original `required` flags. Do not hand-edit the file;
  use the checkout so the bytes are byte-identical to `main`.
  Acceptance: the command exits 0 and the working-tree file matches `main`.

- [x] [P1-T2] Verify the revert is complete. Run
  `git diff main -- src/schemas/default_aop.schema.json` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/aop-diff-after-revert.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` confirming empty output.
  Acceptance (AC-R1): the diff is empty and the artifact records `EXIT_CODE: 0` with an empty
  diff.

---

### Phase 2 — R2 Test Reconciliation (No Production Logic Changes)

- [x] [P2-T1] Inspect `tests/test_default_schemas.py` for any CF1-added test that asserts the
  `default_aop` FILE is at 3.0 on disk or that AOP measures are `required: false`. Such an
  assertion belongs to CF2. If found, update or remove only that assertion; if none exists,
  record that no change is required. Write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/aop-test-reconciliation.2026-06-17T13-40.md`
  with `Timestamp:`, the list of AOP-related tests inspected, and the finding
  (`no on-disk-3.0 or AOP-required-false assertion present` or the exact edit applied).
  Constraint: do NOT weaken any LE assertion; do NOT add the AOP accessor test.
  Acceptance: the artifact documents the inspection result; no LE assertion is altered.

- [x] [P2-T2] Confirm the key test passes with AOP reverted. Run
  `poetry run pytest "tests/test_default_schemas.py::test_bundled_defaults_are_current_format_with_structured_key_parts" -v`
  and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/aop-key-test.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (test PASSED).
  Acceptance (AC-R2): the named test passes (it asserts `default_aop` loads at
  `SCHEMA_FORMAT_VERSION` via the on-load migration, which holds with the file at 2.0).

---

### Phase 3 — Final QA Loop

Run the full Python toolchain in order (format → lint → type-check → test). If any step fails or
changes files, fix within the cycle constraints and restart the loop from P3-T1 until a single
clean pass completes. None of these tasks may be recorded as `SKIPPED`.

- [x] [P3-T1] Run `poetry run black .` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-black.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
  Acceptance: exit 0 and no files reformatted (a JSON-only revert should not reformat Python).

- [x] [P3-T2] Run `poetry run ruff check .` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-ruff.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
  Acceptance: exit 0 with zero lint errors.

- [x] [P3-T3] Run `poetry run pyright` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-pyright.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).
  Acceptance: exit 0 with zero type errors.

- [x] [P3-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-pytest.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` including numeric
  passed/failed counts, total line coverage %, and total branch coverage %.
  Acceptance: all tests pass; line coverage >= 85%; branch coverage >= 75%.

- [x] [P3-T5] Record the coverage delta against the Phase 0 baseline. Write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/coverage-delta.2026-06-17T13-40.md`
  with `Timestamp:`, baseline line/branch coverage (from P0-T6), post-change line/branch coverage
  (from P3-T4), and a statement on changed-lines regression. Because this cycle reverts a JSON
  file and changes no production logic, the expected outcome is no coverage regression.
  Acceptance (AC-Toolchain): the artifact shows post-change coverage >= baseline and >= thresholds
  with no regression on changed lines.

- [x] [P3-T6] Confirm AOP and LE SchemaLoader parity (zero output regression). Run
  `poetry run pytest "tests/test_default_schemas.py" -v` and write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-bundled-parity.2026-06-17T13-40.md`
  with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (all AOP and LE parity
  tests passed).
  Acceptance: all `default_aop` and `default_le` structural/parity tests pass unchanged.

- [x] [P3-T7] Confirm the spec Definition of Done reflects the rescoped AC #3 (now LE-scoped).
  Verify `docs/features/active/etl-required-output-model-semantics-74/spec.md` DoD AC #3 is
  marked `- [x]` and references `default_le` with the AOP minimization descoped to CF2. Write
  `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/spec-dod-confirm.2026-06-17T13-40.md`
  with `Timestamp:` and the confirmed DoD state. Do not edit production code or loader code.
  Acceptance: the artifact records that DoD AC #3 is `- [x]` and LE-scoped.

---

## Preflight Validation

This plan is submitted for validation-only preflight through `atomic-executor` with the directive
`DIRECTIVE: PREFLIGHT VALIDATION ONLY`. The target path
`docs/features/active/etl-required-output-model-semantics-74/remediation-plan.2026-06-17T13-40.md`
is reused for all revision iterations. Required signal: `PREFLIGHT: ALL CLEAR` or
`PREFLIGHT: REVISIONS REQUIRED`.
