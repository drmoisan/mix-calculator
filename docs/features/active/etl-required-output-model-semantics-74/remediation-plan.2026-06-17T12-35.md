# Remediation Plan: etl-required-output-model-semantics (#74, epic child CF1) — cycle 1

- **Issue:** #74 (epic child CF1)
- **Entry timestamp:** 2026-06-17T12-35
- **Feature folder:** `docs/features/active/etl-required-output-model-semantics-74/`
- **Remediation contract:** `docs/features/active/etl-required-output-model-semantics-74/remediation-inputs.2026-06-17T12-35.md`
- **Spec:** `docs/features/active/etl-required-output-model-semantics-74/spec.md`
- **Base branch:** `main` (`0a47fef`)
- **Head:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)
- **Scope:** Exactly R1 from the remediation inputs (AOP `required`-flag alignment) plus its named test addition. No CF2–CF7 work, no suppressions, no dependency additions.

## Scope Confirmation (from supporting reads)

- `src/_load_aop_helpers.py` confirms the AOP output-identity dimension set. The declared
  column order in `src/schemas/default_aop.schema.json` mirrors `SOURCE_COLUMNS`:
  `KEY`, then dimensions `Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`,
  then the twelve months, `YTD`, `Q1`–`Q4`, `YTG`, then dimensions `Super Category`, `PPG`.
- After R1, the AOP columns with `required: true` are exactly the seven dimensions in declared
  order: `Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`, `Super Category`,
  `PPG`. `KEY` and `YTG` stay `required: false, in_output: true`; all measures
  (`Jan`–`Dec`, `YTD`, `Q1`–`Q4`) become `required: false, in_output: true`.
- `required_output_columns()` (src/schema_model.py) returns declared `ColumnSpec` names where
  `required is True`, in declared order. The expected AOP accessor result is therefore:
  `("Customer", "SKU Descripiton", "SKU #", "Customer Master", "Type", "Super Category", "PPG")`.
- AOP `Super Category`/`PPG` differ from the LE case: AOP keeps both as `required: true`
  (output-identity dimensions), so unlike `default_le` they ARE included in the AOP required set.

## Evidence Location Invariant

All evidence artifacts produced by this plan are written under
`docs/features/active/etl-required-output-model-semantics-74/evidence/<kind>/` per
`.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Non-canonical evidence paths
(for example `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`) are forbidden and
must not be used.

---

### Phase 0 — Baseline Capture and Policy Read

- [x] [P0-T1] Read repository policy files in the required order and record an evidence artifact at `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/phase0-instructions-read.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`. AC: artifact exists with all three fields and the seven files listed.
- [x] [P0-T2] Confirm the AOP output-identity dimension set by reading `src/_load_aop_helpers.py` (`SOURCE_COLUMNS`, `EXPECTED_COLUMNS`, `LABEL_COLUMNS`) and record the confirmed dimension list and declared column order to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/aop-dimension-set.md` with `Timestamp:` and the seven required-output dimensions in declared order. AC: artifact lists `Customer, SKU Descripiton, SKU #, Customer Master, Type, Super Category, PPG` and notes `KEY`/`YTG` as optional.
- [x] [P0-T3] Capture the pre-change AOP `required` flag set by running `python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (the printed list, expected to still include measures pre-change) to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/aop-required-flags-before.md`. AC: artifact shows the pre-change list including `Jan`..`Dec`, `YTD`, `Q1`–`Q4`.
- [x] [P0-T4] Run `poetry run black --check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/black-baseline.md`. AC: artifact records exit code and pass/fail summary.
- [x] [P0-T5] Run `poetry run ruff check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/ruff-baseline.md`. AC: artifact records exit code and pass/fail summary.
- [x] [P0-T6] Run `poetry run pyright` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/pyright-baseline.md`. AC: artifact records exit code and error/warning counts.
- [x] [P0-T7] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (test pass count plus numeric line-coverage and branch-coverage headline values) to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/pytest-coverage-baseline.md`. AC: artifact records exit code, pass count, and numeric line and branch coverage percentages.

---

### Phase 1 — Apply R1: Align AOP `required` Flags

- [ ] [P1-T1] In `src/schemas/default_aop.schema.json`, set `required: false` on the `Jan` measure column (canonical_name `Jan`); leave its `in_output: true`, `role`, `numeric`, `expected_dtype`, and order unchanged. AC: `Jan` object reads `"required": false, "in_output": true` and no other field changed.
- [ ] [P1-T2] In `src/schemas/default_aop.schema.json`, set `required: false` on the remaining month measure columns `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec`; leave each `in_output: true` and all other fields unchanged. AC: each of the eleven month columns reads `"required": false, "in_output": true`.
- [ ] [P1-T3] In `src/schemas/default_aop.schema.json`, set `required: false` on the total/quarter measure columns `YTD`, `Q1`, `Q2`, `Q3`, `Q4`; leave each `in_output: true` and all other fields unchanged. AC: `YTD`, `Q1`, `Q2`, `Q3`, `Q4` each read `"required": false, "in_output": true`.
- [ ] [P1-T4] In `src/schemas/default_aop.schema.json`, verify (no edit) that dimension columns `Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`, `Super Category`, `PPG` remain `required: true, in_output: true`, and that `KEY` and `YTG` remain `required: false, in_output: true`. AC: confirmed states match; if any dimension was inadvertently altered, restore it.
- [ ] [P1-T5] Verify (no edit) that `version`, column order, `role`, `numeric`, `expected_dtype`, `aliases`, `sentinel_clean`, `key`, `dedup`, `derived_columns`, `fill_rules`, and `drop_columns` in `src/schemas/default_aop.schema.json` are byte-identical to the pre-change file except for the flipped `required` flags on the measures. AC: `git diff src/schemas/default_aop.schema.json` shows only `required: true -> false` lines on the seventeen measure columns and nothing else.
- [ ] [P1-T6] Run `python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/aop-required-flags-after.md`. AC: printed list equals `['Customer', 'SKU Descripiton', 'SKU #', 'Customer Master', 'Type', 'Super Category', 'PPG']` (only output-identity dimensions, no measures).

---

### Phase 2 — Add AOP `required_output_columns()` Accessor Test

- [ ] [P2-T1] In `tests/test_default_schemas.py`, add module-level constants mirroring the LE pattern: `_AOP_REQUIRED_DIMENSIONS = ("Customer", "SKU Descripiton", "SKU #", "Customer Master", "Type", "Super Category", "PPG")` and `_AOP_NON_REQUIRED_MEASURES = tuple(_MONTHS) + ("YTD",) + tuple(_QUARTERS)`, each with an intent comment describing the 3.0 required-output meaning for AOP. AC: both constants defined with comments; values match the declared AOP required-output order.
- [ ] [P2-T2] In `tests/test_default_schemas.py`, add `test_default_aop_required_output_columns_accessor` mirroring `test_default_le_required_output_columns_accessor`: load `default_aop`, call `required_output_columns()`, assert the result equals `_AOP_REQUIRED_DIMENSIONS`, and assert each name in `_AOP_NON_REQUIRED_MEASURES` is not present. Include a docstring stating the assertion scope (only AOP output-identity dimensions returned; measures excluded). AC: test asserts equality to the ordered dimension tuple and exclusion of every measure; no existing test is weakened or removed.
- [ ] [P2-T3] Run `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_default_schemas.py -q` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/regression-testing/aop-parity-and-accessor.md`. AC: bundled AOP parity tests pass unchanged and the new accessor test passes; exit code 0.

---

### Phase 3 — Final QA Loop

- [ ] [P3-T1] Run `poetry run black .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-black.md`. If files are reformatted, restart the loop from this task. AC: artifact records exit 0 and "no files changed" (or, if changed, the loop is restarted and a clean pass recorded).
- [ ] [P3-T2] Run `poetry run ruff check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-ruff.md`. No suppressions may be added. If lint fails, fix the root cause and restart from P3-T1. AC: artifact records exit 0 with zero lint errors.
- [ ] [P3-T3] Run `poetry run pyright` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-pyright.md`. If type errors appear, fix the root cause (no `# type: ignore` additions) and restart from P3-T1. AC: artifact records exit 0 with zero type errors.
- [ ] [P3-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (test pass count plus numeric post-change line and branch coverage values) to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-pytest-coverage.md`. If any test fails or a stage changed files, restart from P3-T1. AC: artifact records exit 0, full suite passes, line coverage >= 85%, branch coverage >= 75%.
- [ ] [P3-T5] Compare baseline coverage (P0-T7) against post-change coverage (P3-T4) and confirm no regression on the changed lines; record `baseline line/branch`, `post-change line/branch`, and `changed-lines coverage` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/coverage-delta.md` with `Timestamp:`. AC: post-change coverage is not below baseline and the changed `tests/test_default_schemas.py` lines are covered.

---

### Phase 4 — Acceptance Verification and Issue Mirror

- [ ] [P4-T1] Verify R1 acceptance against the remediation inputs: AOP measure `required` flags reflect the 3.0 meaning (P1-T6 output), AOP bundled parity is unchanged (P2-T3), the new accessor test passes (P2-T3), and the toolchain is clean (P3-T1..P3-T4). Record the cross-reference to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/r1-acceptance.md` with `Timestamp:` and an evidence-path map from each acceptance condition to its artifact. AC: all four conditions map to passing artifacts.
- [ ] [P4-T2] Re-check spec Definition of Done item AC #3 in `docs/features/active/etl-required-output-model-semantics-74/spec.md` to `- [x]` (the `default_le`/`default_aop` updated to 3.0 line) only after P4-T1 confirms acceptance; do not alter any other spec content. AC: only the AC #3 checkbox is changed; the edit is limited to that line.
- [ ] [P4-T3] Mirror the issue update to `docs/features/active/etl-required-output-model-semantics-74/evidence/issue-updates/issue-74.2026-06-17T12-35.md` with `Timestamp:`, the exact remediation summary text, and `PostedAs:` per the conventions skill. AC: mirror artifact exists with required fields.

---

## Acceptance Criteria Mapping (to remediation-inputs R1)

- R1 expected behavior "AOP measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4` set `required: false`, `in_output: true`" -> P1-T1, P1-T2, P1-T3.
- R1 "identity/dimension columns keep correct `required` values; `KEY`/`YTG` unchanged" -> P1-T4.
- R1 "AOP emitted output byte-identical (zero regression)" -> P1-T5, P2-T3 (parity), P3-T5 (coverage no-regression).
- R1 "Test/coverage to add: `default_aop` `required_output_columns()` assertion mirroring LE" -> P2-T1, P2-T2.
- R1 verification command (required-flag print) -> P1-T6.
- R1 verification command (parity + accessor pytest) -> P2-T3.
- R1 verification command (full toolchain single clean pass, coverage thresholds) -> P3-T1..P3-T5.
- R1 acceptance "AC #3 re-checked once flags reflect 3.0, parity confirmed, toolchain clean" -> P4-T1, P4-T2.

## Do-Not-Do Compliance

- No change to AOP `in_output`, column order, dtypes, key, dedup, derived, fill, or drop (enforced by P1-T5).
- No relaxation of AOP identity-dimension `required` flags (P1-T4 verifies they stay `required: true`).
- No CF2–CF7 scope: no loader, matching, GUI, or `normalize_le` edits — only `src/schemas/default_aop.schema.json` and `tests/test_default_schemas.py` are touched.
- No suppressions added (enforced in P3-T2, P3-T3).
- No dependencies added.
- 500-line file cap respected: the only edits are one JSON file and one test addition; no production source module grows. `src/schema_serialization.py` is not modified.
- No existing tests, parity assertions, or coverage thresholds weakened (P2-T2 adds a test; P3-T4 maintains thresholds).
