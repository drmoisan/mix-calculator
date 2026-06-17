# Remediation Plan: etl-required-output-model-semantics (#74, epic child CF1) — cycle 2

- **Issue:** #74 (epic child CF1)
- **Entry timestamp:** 2026-06-17T13-10
- **Feature folder:** `docs/features/active/etl-required-output-model-semantics-74/`
- **Remediation contract:** `docs/features/active/etl-required-output-model-semantics-74/remediation-inputs.2026-06-17T13-10.md`
- **Supersedes:** cycle 1 (`remediation-inputs.2026-06-17T12-35.md` / `remediation-plan.2026-06-17T12-35.md`), which failed because flipping AOP measure `required` flags reordered the SchemaLoader output for the `none`-dedup path (see `evidence/regression-testing/r1-output-order-regression.2026-06-17T12-35.md`).
- **Spec:** `docs/features/active/etl-required-output-model-semantics-74/spec.md`
- **Base branch:** `main` (`0a47fef`)
- **Head:** `refactor/etl-required-output-model-semantics-74` (`02e1579`)
- **Mode:** full-bug remediation (spec-driven; `spec.md` is the requirements source; no `issue.md` exists for this feature).
- **Scope:** Exactly R1 (loader-ordering decouple), R2 (AOP measure `required`-flag flip), and R3 (AOP accessor test) from the cycle-2 remediation inputs. No CF2–CF7 work, no suppressions, no dependency additions. R1 is sequenced before R2 so the flag flip lands on a flag-independent ordering and AOP parity stays green throughout.

## Scope Confirmation (from supporting reads)

- **Authoritative AOP output column order (the binding oracle).** `src/load_aop.py` builds its
  keep-list as `EXPECTED_COLUMNS` (= `SOURCE_COLUMNS` minus `KEY` and `YTG`, in declared order)
  and then appends `KEY` (when present) followed by `YTG` (when present). With the standard
  with-YTG fixture this yields, exactly:
  `Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, YTG, KEY`.
  This matches the protected order recorded in the cycle-1 regression dossier.
- **Root cause (confirmed in `src/_schema_loader_helpers.py`).** `resolve_and_rename` builds the
  select+rename keep-list as `required_expected` columns first (filtered by `c.required` in schema
  order), then appends the located by-name optionals (`KEY`, then any `required=False` columns in
  schema order). The `none`-path `emit_output_columns` preserves this frame order. Therefore the
  emitted AOP column order is coupled to the `required` flag: flipping the measures to
  `required: false` moves them out of the required group and into the appended optional group,
  reordering them after `Super Category`/`PPG`. The `default_le` `aggregate` path is unaffected
  because its emit rebuilds canonical order via `_output_column_order(schema)` independent of
  `required`.
- **R1 chosen mechanism (ordering-only).** In `resolve_and_rename`, order the resolved
  (non-by-name) columns by their declared `schema.columns` index instead of filtering by
  `c.required`. The set of resolved columns (everything not located by name) is unchanged; only the
  keep-list ordering changes from `required`-grouped to declared-order. The located by-name
  optionals continue to be appended after the resolved columns in by-name order (`KEY`, then `YTG`),
  matching `load_aop`'s `KEY`-then-`YTG` append. Because the AOP non-by-name resolved set equals
  `EXPECTED_COLUMNS` and the by-name optionals are `KEY` then `YTG`, the resulting frame order
  reproduces `load_aop`'s order exactly and becomes independent of the `required` flag. This is the
  enabling change that keeps `tests/test_schema_loader_parity_aop.py` green when R2 lands.
- **R1 invariants.** Ordering-only: no change to which columns are emitted (membership is unchanged
  — `resolve_columns` still validates the same set, `emit_output_columns` still filters by
  `in_output`), no dtype/value/index change, no change to the `collapse`/`aggregate` (`default_le`)
  emit path. The `_by_name_optional_columns` helper and the `none`/`aggregate` emit branches are
  not altered by R1.
- **R2 after R1.** Flip AOP measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4` to `required: false`
  (`in_output: true` unchanged). `YTG` is already `required: false, in_output: true`. `KEY` is
  already `required: false, in_output: true`. Dimensions `Customer`, `SKU Descripiton`, `SKU #`,
  `Customer Master`, `Type`, `Super Category`, `PPG` stay `required: true, in_output: true`. With
  R1 in place the emitted order does not move, so the parity oracle stays byte-identical.
- **R3 expected accessor result.** `SchemaDefinition.required_output_columns()`
  (`src/schema_model.py`) returns declared `ColumnSpec` names where `required is True`, in declared
  order. After R2 the AOP result is exactly the seven output-identity dimensions in declared order:
  `("Customer", "SKU Descripiton", "SKU #", "Customer Master", "Type", "Super Category", "PPG")`.
  `KEY` (required: false) is excluded; all measures and `YTG` are excluded.
- **File-size cap.** `src/_schema_loader_helpers.py` is 465 lines. The R1 change must be minimal —
  reorder the existing keep-list construction by declared index, or extract one small `_prefixed`
  helper — and must not push the file past the 500-line cap.

## Evidence Location Invariant

All evidence artifacts produced by this plan are written under
`docs/features/active/etl-required-output-model-semantics-74/evidence/<kind>/` per
`.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Non-canonical evidence paths
(for example `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`,
`artifacts/regression-testing/`) are forbidden and must not be used.

---

### Phase 0 — Baseline Capture and Policy Read

- [x] [P0-T1] Read repository policy files in the required order and record an evidence artifact at `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/phase0-instructions-read.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`. AC: artifact exists with all three fields and the seven files listed.
- [x] [P0-T2] Confirm the authoritative AOP output column order by reading `src/load_aop.py` (the `columns_to_keep` / `KEY`-then-`YTG` append) and `src/_load_aop_helpers.py` (`SOURCE_COLUMNS`, `EXPECTED_COLUMNS`) and record the confirmed order to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/aop-output-order.md` with `Timestamp:` and the exact emitted column sequence `Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, YTG, KEY`. AC: artifact records the protected order verbatim and names `src/load_aop.py` as the oracle source.
- [x] [P0-T3] Capture the pre-change AOP `required` flag set by running `python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (the printed list, expected to still include all measures pre-change) to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/aop-required-flags-before.md`. AC: artifact shows the pre-change list including `Jan`..`Dec`, `YTD`, `Q1`–`Q4`.
- [x] [P0-T4] Capture the pre-change AOP and LE parity oracle state by running `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py -q` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail counts) to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/parity-oracle-baseline.md`. AC: artifact records exit 0 and the AOP+LE parity tests passing on the clean tree before any edit.
- [x] [P0-T5] Run `poetry run black --check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/black-baseline.md`. AC: artifact records exit code and pass/fail summary.
- [x] [P0-T6] Run `poetry run ruff check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/ruff-baseline.md`. AC: artifact records exit code and pass/fail summary.
- [x] [P0-T7] Run `poetry run pyright` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/pyright-baseline.md`. AC: artifact records exit code and error/warning counts.
- [x] [P0-T8] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (test pass count plus numeric line-coverage and branch-coverage headline values) to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/pytest-coverage-baseline.md`. AC: artifact records exit code, pass count, and numeric line and branch coverage percentages.
- [x] [P0-T9] Record the current line count of `src/_schema_loader_helpers.py` by running `python -c "print(sum(1 for _ in open('src/_schema_loader_helpers.py', encoding='utf-8')))"` and write `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (the integer count, expected 465) to `docs/features/active/etl-required-output-model-semantics-74/evidence/baseline/helper-line-count-before.md`. AC: artifact records the pre-change line count so the 500-line cap can be verified after R1.

---

### Phase 1 — R1: Decouple `none`-dedup Emitted Column Order from the `required` Flag

> EXECUTION HALTED at [P1-T1] (2026-06-17T13-10). R1 as scoped is insufficient: with
> `_by_name_optional_columns` held unchanged (P1-T3), R2's flag flip sweeps the seventeen
> measures into the by-name-optional set, where they are field-identical to the genuine
> presence-optional `YTG`. No flag-independent, schema-driven rule reproduces `load_aop`'s
> `YTG`-trailing order, so the keep-list reorder cannot keep `tests/test_schema_loader_parity_aop.py`
> green after R2. This is a NEW FINDING requiring a plan revision (add a schema-model
> presence-optional signal). Source/schema/test files left unmodified; AOP+LE parity green.
> Finding dossier: `evidence/regression-testing/r1-scope-insufficiency-finding.2026-06-17T13-10.md`.

- [ ] [P1-T1] In `src/_schema_loader_helpers.py` `resolve_and_rename`, change the keep-list construction so the resolved (non-by-name) columns are ordered by their declared `schema.columns` index rather than filtered by `c.required`. The resolved set must stay identical (every declared column not located by name, i.e. the columns passed to `resolve_columns`), and the located by-name optionals must still be appended after the resolved columns in by-name order (`KEY`, then `YTG`). Keep the change minimal (reorder the existing list comprehension by declared index, or extract one `_prefixed` helper with a docstring). AC: `columns_to_keep` for AOP yields, after rename, the frame column order `Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, YTG, KEY`, independent of which columns are marked `required`.
- [ ] [P1-T2] In `src/_schema_loader_helpers.py`, confirm (no functional edit) that `resolve_columns` is still called with the same required-expected membership the loader validates today — the R1 change must not remove any column from the resolved set, only reorder the keep-list. If the membership set used for `resolve_columns` was incidentally narrowed by P1-T1, restore it so column membership is unchanged. AC: the set of names passed to `resolve_columns` (and thus the required-presence validation behavior) is identical to the pre-change behavior; only ordering of `columns_to_keep` changed.
- [ ] [P1-T3] In `src/_schema_loader_helpers.py`, verify (no edit) that `emit_output_columns` (both the `collapse`/`aggregate` branch and the `none` branch), `_by_name_optional_columns`, `collapse_by_key`, `apply_derived_columns`, and `_output_column_order` are unchanged by R1. AC: `git diff src/_schema_loader_helpers.py` shows edits confined to the `resolve_and_rename` keep-list ordering (plus an optional new private helper); no other function body is modified.
- [ ] [P1-T4] Update the docstring/intent comment in `resolve_and_rename` (and the new helper if extracted) to state that the keep-list is ordered by declared `columns` position so the `none`-path emitted column order is independent of the `required` flag and matches `load_aop`. Comply with `.claude/rules/self-explanatory-code-commenting.md` (no numbered notes; meta-what + why). AC: the docstring/comment explains the flag-independent ordering rationale and references the `load_aop` order parity.
- [ ] [P1-T5] Run the AOP and LE parity oracle UNCHANGED against the R1-only tree by running `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py -q` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/regression-testing/r1-parity-after-ordering-fix.md`. AC: exit 0; all AOP and LE parity tests pass with R1 applied and R2 not yet applied (proves the ordering change alone is zero-regression).
- [ ] [P1-T6] Verify the 500-line cap by running `python -c "print(sum(1 for _ in open('src/_schema_loader_helpers.py', encoding='utf-8')))"` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (the post-change integer count) to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/helper-line-count-after.md`. AC: post-change line count is <= 500.

---

### Phase 2 — R2: Flip AOP Measure `required` Flags to the 3.0 Required-Output Meaning

- [ ] [P2-T1] In `src/schemas/default_aop.schema.json`, set `required: false` on the twelve month measure columns `Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec`; leave each `in_output: true`, `role`, `numeric`, `expected_dtype`, and position unchanged. AC: each of the twelve month columns reads `"required": false, "in_output": true` and no other field changed.
- [ ] [P2-T2] In `src/schemas/default_aop.schema.json`, set `required: false` on the total/quarter measure columns `YTD`, `Q1`, `Q2`, `Q3`, `Q4`; leave each `in_output: true` and all other fields unchanged. AC: `YTD`, `Q1`, `Q2`, `Q3`, `Q4` each read `"required": false, "in_output": true`.
- [ ] [P2-T3] In `src/schemas/default_aop.schema.json`, verify (no edit) that dimension columns `Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`, `Super Category`, `PPG` remain `required: true, in_output: true`, and that `KEY` and `YTG` remain `required: false, in_output: true`. AC: confirmed states match; if any dimension was inadvertently altered, restore it.
- [ ] [P2-T4] Verify (no edit) that `version`, column order, `role`, `numeric`, `expected_dtype`, `aliases`, `sentinel_clean`, `key`, `dedup`, `derived_columns`, `fill_rules`, and `drop_columns` in `src/schemas/default_aop.schema.json` are unchanged except for the flipped `required` flags on the seventeen measures (`Jan`–`Dec`, `YTD`, `Q1`–`Q4`). AC: `git diff src/schemas/default_aop.schema.json` shows only `required: true -> false` lines on the seventeen measure columns and nothing else.
- [ ] [P2-T5] Run `python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/aop-required-flags-after.md`. AC: printed list equals `['Customer', 'SKU Descripiton', 'SKU #', 'Customer Master', 'Type', 'Super Category', 'PPG']` (only output-identity dimensions, no measures).
- [ ] [P2-T6] Run `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py -q` against the R1+R2 tree and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/regression-testing/r2-parity-after-flag-flip.md`. AC: exit 0; AOP and LE parity remain byte-identical with both R1 and R2 applied (proves the flag flip introduces no output regression because R1 decoupled order).

---

### Phase 3 — R3: Add AOP `required_output_columns()` Accessor Test

- [ ] [P3-T1] In `tests/test_default_schemas.py`, add module-level constants mirroring the LE pattern: `_AOP_REQUIRED_DIMENSIONS = ("Customer", "SKU Descripiton", "SKU #", "Customer Master", "Type", "Super Category", "PPG")` and `_AOP_NON_REQUIRED_MEASURES = tuple(_MONTHS) + ("YTD",) + tuple(_QUARTERS)`, each with an intent comment describing the 3.0 required-output meaning for AOP (output-identity dimensions in declared order; measures excluded). AC: both constants defined with comments; values match the declared AOP required-output order.
- [ ] [P3-T2] In `tests/test_default_schemas.py`, add `test_default_aop_required_output_columns_accessor` mirroring `test_default_le_required_output_columns_accessor`: load `default_aop`, call `required_output_columns()`, assert the result equals `_AOP_REQUIRED_DIMENSIONS`, assert each name in `_AOP_NON_REQUIRED_MEASURES` is not present, and assert `KEY` and `YTG` are not present. Include a docstring stating the assertion scope. AC: test asserts equality to the ordered dimension tuple and exclusion of every measure, `KEY`, and `YTG`; no existing test is weakened or removed.
- [ ] [P3-T3] Run `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py tests/test_default_schemas.py -q` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/regression-testing/r3-accessor-and-parity.md`. AC: AOP and LE parity tests pass unchanged and the new accessor test passes; exit 0.

---

### Phase 4 — Final QA Loop

- [ ] [P4-T1] Run `poetry run black .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-black.md`. If files are reformatted, restart the loop from this task. AC: artifact records exit 0 and "no files changed" (or, if changed, the loop is restarted and a clean pass recorded).
- [ ] [P4-T2] Run `poetry run ruff check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-ruff.md`. No suppressions may be added. If lint fails, fix the root cause and restart from P4-T1. AC: artifact records exit 0 with zero lint errors.
- [ ] [P4-T3] Run `poetry run pyright` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-pyright.md`. If type errors appear, fix the root cause (no `# type: ignore` additions) and restart from P4-T1. AC: artifact records exit 0 with zero type errors.
- [ ] [P4-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (test pass count plus numeric post-change line and branch coverage values) to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/final-pytest-coverage.md`. If any test fails or a stage changed files, restart from P4-T1. AC: artifact records exit 0, full suite passes, line coverage >= 85%, branch coverage >= 75%.
- [ ] [P4-T5] Compare baseline coverage (P0-T8) against post-change coverage (P4-T4) and confirm no regression on the changed lines in `src/_schema_loader_helpers.py` and `tests/test_default_schemas.py`; record `baseline line/branch`, `post-change line/branch`, and `changed-lines coverage` to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/coverage-delta.md` with `Timestamp:`. AC: post-change coverage is not below baseline and the changed lines in the touched files are covered.

---

### Phase 5 — Acceptance Verification and Issue Mirror

- [ ] [P5-T1] Verify R1 acceptance against the cycle-2 remediation inputs: the `none`-path emitted order is decoupled from the `required` flag (P1-T1..P1-T4), AOP and LE parity pass with R1 alone (P1-T5), and the 500-line cap holds (P1-T6). Record the cross-reference to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/r1-acceptance.md` with `Timestamp:` and an evidence-path map from each acceptance condition to its artifact. AC: all R1 conditions map to passing artifacts.
- [ ] [P5-T2] Verify R2 acceptance: AOP measure `required` flags reflect the 3.0 meaning (P2-T5), and AOP+LE parity remain byte-identical with R1+R2 (P2-T6). Record the cross-reference to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/r2-acceptance.md` with `Timestamp:`. AC: both R2 conditions map to passing artifacts.
- [ ] [P5-T3] Verify R3 acceptance: the new `default_aop` accessor test passes and asserts exactly the seven ordered dimensions while excluding measures, `KEY`, and `YTG` (P3-T2, P3-T3), and the full toolchain is clean (P4-T1..P4-T4). Record the cross-reference to `docs/features/active/etl-required-output-model-semantics-74/evidence/qa-gates/r3-acceptance.md` with `Timestamp:`. AC: all R3 conditions map to passing artifacts.
- [ ] [P5-T4] Re-check spec Definition of Done item AC #3 in `docs/features/active/etl-required-output-model-semantics-74/spec.md` to `- [x]` (the `default_le`/`default_aop` updated to 3.0; months/FY/quarters `required: false`, `in_output` unchanged line) only after P5-T1..P5-T3 confirm acceptance; do not alter any other spec content. AC: only the AC #3 checkbox is changed; the edit is limited to that line.
- [ ] [P5-T5] Mirror the issue update to `docs/features/active/etl-required-output-model-semantics-74/evidence/issue-updates/issue-74.2026-06-17T13-10.md` with `Timestamp:`, the exact remediation summary text, and `PostedAs:` per the conventions skill. AC: mirror artifact exists with required fields.

---

## Acceptance Criteria Mapping (to remediation-inputs R1/R2/R3)

- R1 "make the AOP (`none`-dedup) output column order independent of the `required` flag; ordering-only; `tests/test_schema_loader_parity_aop.py` passes UNCHANGED" -> P1-T1, P1-T2, P1-T3, P1-T4, P1-T5.
- R1 "no change to which columns are emitted, no dtype/value change, no change to the `default_le` path" -> P1-T2 (membership unchanged), P1-T3 (`emit`/`_output_column_order` unchanged), P1-T5 (LE parity green).
- R1 500-line cap constraint -> P0-T9 (before), P1-T6 (after).
- R2 "set `required: false` on measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4`; keep `in_output: true`; dimensions stay `required: true`; `KEY`/`YTG` unchanged" -> P2-T1, P2-T2, P2-T3.
- R2 "no change to `in_output`, column order, dtypes, key, dedup, or any value" -> P2-T4, P2-T6 (parity byte-identical).
- R2 verification command (required-flag print returns only the seven dimensions) -> P2-T5.
- R3 "add `default_aop` `required_output_columns()` accessor test; assert the seven ordered dimensions; exclude measures, `KEY`, `YTG`" -> P3-T1, P3-T2.
- Verification command (parity + accessor pytest) -> P3-T3.
- Verification command (full toolchain single clean pass, coverage thresholds) -> P4-T1..P4-T5.
- Acceptance "re-check spec DoD AC #3 to `- [x]`" -> P5-T4.

## Do-Not-Do Compliance

- Zero output regression for AOP and LE: parity is the oracle and is verified after R1 alone (P1-T5), after R1+R2 (P2-T6), and with the accessor test added (P3-T3).
- R1 is ordering-only: column membership (P1-T2), the `emit`/`_output_column_order`/`_by_name_optional_columns`/`collapse_by_key` bodies (P1-T3), and the `default_le` `aggregate` path are not changed.
- No relaxation of AOP identity-dimension `required` flags; only the seventeen measure columns flip (P2-T3, P2-T4).
- No CF2–CF7 scope: edits are confined to `src/_schema_loader_helpers.py` (single ordering decouple), `src/schemas/default_aop.schema.json`, and `tests/test_default_schemas.py`. No matching, GUI, `normalize_le`, or drop-unassigned work.
- No suppressions added (enforced in P4-T2, P4-T3).
- No dependencies added.
- 500-line file cap respected: `src/_schema_loader_helpers.py` (465 lines pre-change) stays <= 500 (P0-T9, P1-T6); the R1 change is minimal or extracts one small helper.
- No existing tests, parity assertions, or coverage thresholds weakened (P3-T2 adds a test; P4-T4 maintains thresholds).
