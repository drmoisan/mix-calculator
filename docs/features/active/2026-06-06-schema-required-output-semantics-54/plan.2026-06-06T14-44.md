# schema-required-output-semantics - Refactor Plan

- **Issue:** #54
- **Parent (optional):** #50 (rides in PR #51)
- **Owner:** drmoisan
- **Last Updated:** 2026-06-06T14-44
- **Status:** Draft
- **Version:** 1.0
- **Work Mode:** full-feature
- **Branch:** feature/schema-builder-ux-overhaul-50

## Overview

Add an explicit `in_output: bool = True` field to `ColumnSpec` and switch the
schema loader's output determination from `drop_columns` by-name exclusion to
`in_output` inclusion (plus the business `KEY` and derived columns, in schema
order). `required` keeps its current meaning (source-presence). The bundled
`default_le` schema's `YTD/YTG` becomes `required: false, in_output: false`
with `drop_columns: []`; `default_aop` gains explicit `in_output: true`. The
#50 schema-builder carries `in_output` end-to-end. Parity with the protected
loaders is the top invariant and must hold byte-for-byte. No
`SCHEMA_FORMAT_VERSION` bump (additive field, safe default `true`).

This plan implements the FINAL spec (v1.0) exactly. It does not redesign the
locked approach (research option (a)).

## Required References (read, do not restate)

Standing repository instructions are auto-loaded by the harness (no `CLAUDE.md`
appears in any files-to-read list below; it is always in effect). The following
must be read in policy order before implementation:

1. `.claude/rules/general-code-change.md`
2. `.claude/rules/general-unit-test.md`
3. `.claude/rules/python.md`
4. `.claude/rules/python-suppressions.md`
5. `.claude/rules/self-explanatory-code-commenting.md`
6. `.claude/rules/quality-tiers.md`

Feature inputs (authoritative):

- `docs/features/active/2026-06-06-schema-required-output-semantics-54/spec.md`
- `docs/features/active/2026-06-06-schema-required-output-semantics-54/issue.md`
- `artifacts/research/schema-required-output-semantics-54.md`

## Evidence Location Invariant

All evidence artifacts for this plan MUST be written under
`docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/<kind>/`
per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing to
`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other
non-canonical evidence path is a policy violation enforced by the
`enforce-evidence-locations.ps1` PreToolUse hook. Each command-step artifact
MUST include `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`.
Test-step artifacts MUST include numeric coverage headline values (line% and
branch%).

## Batching Constraint

This plan honors the python-typed-engineer per-batch cap (max 3 production
files + 3 test files per batch). Batches are sequenced: (1) model +
serialization, (2) loader emit + bundled schemas, (3) parity gate, (4) builder
cluster, (5) full final QA. Each implementation phase ends with a toolchain
gate (Black -> Ruff -> Pyright -> Pytest with `--cov --cov-branch`).

## File Size Guard

All in-scope production files are currently under the 500-line limit. The
largest in-scope file is `src/gui/widgets/schema_builder_dialog.py` at 489 lines
(close to the 500-line limit); `src/gui/presenters/schema_builder_presenter.py`
and `src/_schema_model_specs.py` are each 461 lines. Each editing task includes a
post-edit line-count check; if any edit would push a file over 500 lines, the
task is blocked and an extraction sub-task must be planned before proceeding.

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in order and record a Phase 0 evidence artifact at `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/phase0-instructions-read.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read: `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/quality-tiers.md`. (Standing harness-auto-loaded instructions noted as always-in-effect; no `CLAUDE.md` is listed.)
- [x] [P0-T2] Capture current line counts for every production file to be edited and write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/baseline-line-counts.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` listing each path with its line count: `src/_schema_model_specs.py`, `src/schema_model.py`, `src/schema_serialization.py`, `src/_schema_loader_helpers.py`, `src/schemas/default_le.schema.json`, `src/schemas/default_aop.schema.json`, `src/gui/presenters/_schema_builder_state.py`, `src/gui/presenters/schema_builder_presenter.py`, `src/gui/presenters/_columns_tab_presenter.py`, `src/gui/_schema_provider_factory.py`, `src/gui/widgets/schema_builder_dialog.py`, `src/gui/widgets/_schema_builder_drag_tabs.py`, `src/gui/_schema_view_protocols.py`. (AC-8)
- [x] [P0-T3] Run `poetry run black --check .` and write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/baseline-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-8)
- [x] [P0-T4] Run `poetry run ruff check .` and write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/baseline-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-8)
- [x] [P0-T5] Run `poetry run pyright` and write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/baseline-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts). (AC-8)
- [x] [P0-T6] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` and write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/baseline-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` that records passed/failed counts and numeric baseline coverage headline values (line% and branch%). (AC-8)
- [x] [P0-T7] Grep the repository for every tuple-unpack site of the builder column-row tuple and record `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/baseline/baseline-unpack-sites.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` enumerating each file:line that unpacks `(canonical, role, required, aliases)` (including `src/gui/presenters/_columns_tab_presenter.py`, `src/gui/presenters/schema_builder_presenter.py`, `src/gui/presenters/_schema_builder_state.py`, `src/gui/widgets/schema_builder_dialog.py`, `src/gui/widgets/_schema_builder_drag_tabs.py`, `src/gui/_schema_view_protocols.py`). This enumerated list is the authoritative checklist for Phase 4. (AC-7)

---

### Phase 1 — Model and Serialization

- [x] [P1-T1] In `src/_schema_model_specs.py`, add `in_output: bool = True` to the `ColumnSpec` dataclass, with an `Attributes:`-section docstring update describing `in_output` as output-membership (distinct from `required` = source-presence) per the self-explanatory commenting rule. Acceptance: `ColumnSpec(canonical_name="X", role="dimension")` has `in_output is True` by default. (AC-2, AC-6)
- [x] [P1-T2] Confirm/adjust the re-export and any validation in `src/schema_model.py` so `ColumnSpec.in_output` is visible to all importers; if `src/schema_model.py` only re-exports `ColumnSpec` unchanged, record that no edit was needed in the task notes. Acceptance: `from src.schema_model import ColumnSpec` exposes `in_output`. (AC-2, AC-6)
- [x] [P1-T3] In `src/schema_serialization.py`, add `"in_output"` to the column key set, emit `"in_output": column.in_output` in the column-to-object path, and parse it with a default of `True` (absent key -> `True`) in the object-to-column path; update the forward-migration column-key enumeration if it lists column keys. Update affected docstrings. Acceptance: `schema_from_json` on JSON lacking `in_output` yields `in_output is True`; a schema with `in_output=False` round-trips through `schema_to_json`/`schema_from_json`. (AC-6)
- [x] [P1-T4] Add unit tests in `tests/test_schema_serialization.py`: (a) absent `in_output` in JSON parses as `True`; (b) `in_output=False` round-trips; (c) extend the existing serialization property/round-trip coverage to include `in_output`. Tests must be deterministic with no temp files and follow Arrange-Act-Assert. Acceptance: new tests pass. (AC-6)
- [x] [P1-T5] Run the toolchain gate for this batch: `poetry run black .`, then `poetry run ruff check .`, then `poetry run pyright`, then `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Restart from Black if any step changes files or fails. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/phase1-gate.md` with one section per command, each with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (test section records line% and branch%). (AC-8)

---

### Phase 2 — Loader Output Determination and Bundled Schemas

- [x] [P2-T1] In `src/_schema_loader_helpers.py`, change `_output_column_order` to include a declared column only when `c.in_output` is `True` (remove the `drop_columns` set computation from this function), preserving schema order and the existing derived-column insertion. Update the function docstring to state output is determined by `in_output` inclusion. Acceptance: declared columns with `in_output=False` are absent from the returned order; `in_output=True` columns plus derived columns remain in schema order. (AC-2)
- [x] [P2-T2] In `src/_schema_loader_helpers.py`, change the `none`-mode (AOP) branch of `emit_output_columns` to filter declared columns by `in_output` instead of by `drop_columns`, preserving the frame's natural column order and the `KEY` handling. Update the docstring. Acceptance: AOP `none`-mode output preserves prior column set/order via `in_output` filtering. (AC-2, AC-4)
- [x] [P2-T3] In `src/_schema_loader_helpers.py`, update the `_by_name_optional_columns` docstring/inline comment that currently states the LE discriminator `YTD/YTG` is required and resolved normally; after the bundled-schema change it is `required=false` and is included in the by-name-optional list. Verify (no behavior change needed beyond the docstring) that a `required=false, in_output=false` column is carried through `resolve_and_rename` (by-name-optional) and survives `collapse_by_key` as the dedup discriminator, and is excluded only at emit. Acceptance: docstring accurately reflects the new by-name-optional membership of `YTD/YTG`. (AC-5)
- [x] [P2-T4] Edit `src/schemas/default_le.schema.json`: set `YTD/YTG` to `"required": false` and `"in_output": false`; set `"drop_columns": []`; add an explicit `"in_output": true` to every other declared LE column (consistent explicit representation matching how `required`/`numeric` are written). Acceptance: JSON parses; `YTD/YTG` is `required:false, in_output:false`; `drop_columns` is empty. (AC-1)
- [x] [P2-T5] Edit `src/schemas/default_aop.schema.json`: add explicit `"in_output": true` to every declared AOP column (AOP `YTG` stays `required:false, in_output:true`); confirm `"drop_columns": []`. Acceptance: JSON parses; `YTG` is `required:false, in_output:true`; `drop_columns` is empty. (AC-1, AC-4)
- [x] [P2-T6] Run the toolchain gate for this batch: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch --cov-report=term-missing`), restarting from Black on any change/failure. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/phase2-gate.md` (per-command sections with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; test section records line% and branch%). (AC-8)

---

### Phase 3 — Parity Verification (Top Invariant)

- [x] [P3-T1] Run the LE parity test in isolation: `poetry run pytest tests/test_schema_loader_parity_le.py -v`. Acceptance: all tests pass (LE schema-driven output equals `normalize_le.TARGET_COLUMNS` exactly). Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/regression-testing/phase3-parity-le.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-3)
- [x] [P3-T2] Run the AOP parity test in isolation: `poetry run pytest tests/test_schema_loader_parity_aop.py -v`. Acceptance: all tests pass (AOP schema-driven output equals `load_aop` output exactly, including the optional-but-output `YTG`). Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/regression-testing/phase3-parity-aop.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-4)
- [x] [P3-T3] Update `tests/test_default_schemas.py`: change the assertion `drop_columns == ("YTD/YTG",)` to `drop_columns == ()`, and add assertions that LE `YTD/YTG` has `required is False` and `in_output is False`. Acceptance: updated test passes. (AC-1)
- [x] [P3-T4] Add new behavioral tests covering output-membership semantics in `tests/test_schema_loader_derived.py` (or a sibling loader test module if more appropriate by structure): (a) a `ColumnSpec` with `in_output=False` is excluded from output; (b) `in_output=True` is included; (c) the discriminator case (`required:false, in_output:false`) is present in source, used by `collapse_by_key` dedup, and absent from output. Tests must be deterministic, no temp files, Arrange-Act-Assert. If `tests/test_schema_loader_derived.py` has a `test_drop_columns_removed_from_output` test, update its name/docstring to reflect `in_output` exclusion while keeping the `"YTD/YTG" not in out.columns` assertion. Acceptance: new and updated tests pass. (AC-2, AC-5)
- [x] [P3-T5] Run the toolchain gate for this batch: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch --cov-report=term-missing`), restarting from Black on any change/failure. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/phase3-gate.md` (per-command sections; test section records line% and branch%). (AC-8)

---

### Phase 4 — Schema-Builder Carries `in_output` End-to-End

- [x] [P4-T1] In `src/gui/presenters/_schema_builder_state.py`, change the column row type from the 4-tuple `(canonical_name, role, required, aliases)` to the 5-tuple `(canonical_name, role, required, in_output, aliases)`, update the field type annotation and its docstring, and update every internal unpack site in this file (including the declared-names comprehension at the `[canonical for canonical, _role, _required, _aliases in state.columns]` site and the `assemble_schema` comprehension at the `for canonical, role, required, aliases in state.columns` site). `assemble_schema` must forward `in_output` into `ColumnSpec(..., in_output=in_output, ...)`. Acceptance: Pyright is clean for this file; `assemble_schema` produces a `ColumnSpec` whose `in_output` matches the row value. (AC-7)
- [x] [P4-T2] In `src/gui/presenters/schema_builder_presenter.py`, update `_spec_to_row` to emit `(spec.canonical_name, spec.role, spec.required, spec.in_output, spec.aliases)`, update `_state_from_schema` to build rows as `(c.canonical_name, c.role, c.required, c.in_output, c.aliases)`, and update any other unpack site in this file (e.g., the `for canonical, _role, _required, _aliases in self._state.columns` comprehension) to the 5-tuple arity. Update affected docstrings. Acceptance: Pyright clean; round-trip schema -> state -> schema preserves `in_output`. (AC-7)
- [x] [P4-T3] In `src/gui/presenters/_columns_tab_presenter.py`, update every column-row unpack site to the 5-tuple arity (the sites at the `for canonical, _role, _required, _aliases ...` lines, the `for index, (name, role, required, aliases) in enumerate(...)` loop and its `self._state.columns[index] = (...)` reassignment which must carry `in_output`, and the `for name, _role, _required, _aliases ...` and `for canonical, _role, _required, _aliases ...` comprehensions). Acceptance: Pyright clean; alias edits preserve the row's `in_output` value. (AC-7)
- [x] [P4-T4] Update the remaining tuple-arity sites discovered in [P0-T7] outside the three presenter files so Pyright is clean repository-wide: `src/gui/widgets/schema_builder_dialog.py` (the `get_columns`/`set_columns` docstrings and the `for canonical, _r, _req, _a in self.get_columns()` site), `src/gui/widgets/_schema_builder_drag_tabs.py` (docstrings and the `[canonical for canonical, _r, _req, _a in self._state.columns]` site), and `src/gui/_schema_view_protocols.py` (the `(canonical_name, role, required, aliases)` contract docstrings and any typed tuple signature). If a site only documents the tuple shape, update the docstring; if it unpacks the tuple, update arity. Additionally, update the explicit 4-tuple type annotations on the `set_columns`/`get_columns` parameter and return signatures from `tuple[str, str, bool, tuple[str, ...]]` to `tuple[str, str, bool, bool, tuple[str, ...]]` (matching the `_schema_builder_state.columns` field annotation updated in [P4-T1]) in all three files: `src/gui/_schema_view_protocols.py` (lines ~195, ~210), `src/gui/widgets/schema_builder_dialog.py` (lines ~159, ~175), and `src/gui/widgets/_schema_builder_drag_tabs.py` (lines ~95, ~141). Acceptance: `poetry run pyright` reports zero errors related to column-row tuple arity, and no `tuple[str, str, bool, tuple[str, ...]]` column-row annotation remains in those three files. (AC-7)
- [x] [P4-T5] Confirm `src/gui/_schema_provider_factory.py` `_spec_from_schema` split: with the bundled LE change, LE `YTD/YTG` (now `required:false`) lands in the optional set. No code change is required if the split already keys on `column.required`; record in task notes whether an edit was needed. Acceptance: loading the bundled LE schema places `YTD/YTG` in the optional specs, not the required specs. (AC-7)
- [x] [P4-T6] Add/extend builder tests: in `tests/gui/test_schema_provider_factory.py`, assert the real bundled LE schema's `YTD/YTG` appears in the optional specs (not required specs); add a builder test (in the appropriate `tests/gui/` builder test module) asserting `assemble_schema` forwards `in_output` from a 5-tuple state row to the resulting `ColumnSpec`. Tests must be deterministic and avoid real Qt where avoidable (use the existing presenter/state seams and fakes). Acceptance: new tests pass. (AC-7)
- [x] [P4-T7] Verify no in-scope file exceeds 500 lines after the builder edits (re-check the files listed in [P0-T2]). Re-check explicitly the three files edited by [P4-T4]: `src/gui/widgets/schema_builder_dialog.py` (the close-to-limit file at 489 lines), `src/gui/widgets/_schema_builder_drag_tabs.py`, and `src/gui/_schema_view_protocols.py`. If any file exceeds 500 lines, stop and plan an extraction sub-task before continuing; this clause applies to `src/gui/widgets/schema_builder_dialog.py` in particular given its 489-line baseline. Record the post-edit line counts in `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/phase4-line-counts.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-8)
- [x] [P4-T8] Run the toolchain gate for this batch: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch --cov-report=term-missing`), restarting from Black on any change/failure. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/phase4-gate.md` (per-command sections; test section records line% and branch%). (AC-7, AC-8)

---

### Phase 5 — Full Final QA Loop

- [x] [P5-T1] Run formatting: `poetry run black .`. If it changes any file, restart the loop from this step after the change settles. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-8)
- [x] [P5-T2] Run linting: `poetry run ruff check .`. If it reports errors, fix and restart from [P5-T1]. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. (AC-8)
- [x] [P5-T3] Run type checking: `poetry run pyright`. If it reports errors, fix and restart from [P5-T1]. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts). (AC-8)
- [x] [P5-T4] Run the full test suite with coverage: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. If any test fails or files change, fix and restart from [P5-T1]. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` recording passed/failed counts and numeric post-change coverage (line% and branch%). (AC-3, AC-4, AC-5, AC-6, AC-7, AC-8)
- [x] [P5-T5] Verify coverage thresholds and no-regression-on-changed-lines: compare baseline coverage ([P0-T6]) to final coverage ([P5-T4]); confirm line >= 85%, branch >= 75%, and that changed lines are covered. Write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-coverage-delta.md` with `Timestamp:`, baseline line%/branch%, post-change line%/branch%, changed-code coverage, and a PASS/REMEDIATION-REQUIRED determination. If thresholds are not met, the outcome is remediation-required (not PASS). (AC-8)
- [x] [P5-T6] Map every acceptance criterion to its satisfying evidence artifact(s) and write `docs/features/active/2026-06-06-schema-required-output-semantics-54/evidence/qa-gates/final-ac-traceability.md` (`Timestamp:` plus an AC-1..AC-8 -> artifact-path table). Acceptance: every AC maps to at least one passing artifact. (AC-1..AC-8)

---

## Acceptance Criteria Coverage Map

- AC-1 (`default_le` `YTD/YTG` required:false, in_output:false, drop_columns []): P2-T4, P3-T3
- AC-2 (output by `in_output` inclusion, not `drop_columns`): P1-T1, P1-T2, P2-T1, P2-T2, P3-T4
- AC-3 (LE output equals `normalize_le.TARGET_COLUMNS`): P3-T1
- AC-4 (AOP output equals `load_aop`, incl. `YTG`): P2-T2, P2-T5, P3-T2
- AC-5 (processing-only column present, used for dedup, excluded from output): P2-T3, P3-T4
- AC-6 (`in_output` defaults True; absent loads True; round-trips): P1-T1, P1-T3, P1-T4
- AC-7 (builder carries `in_output` end-to-end; provider-factory split): P0-T7, P4-T1..P4-T6
- AC-8 (full toolchain pass; coverage >= 85%/75%; no regression): P0-T2..P0-T6, P1-T5, P2-T6, P3-T5, P4-T7, P4-T8, P5-T1..P5-T5
