# Remediation Plan — schema-builder-ux-overhaul (Issue #50) — Cycle 2

- Work Mode: full-feature
- Entry timestamp: 2026-06-05T21-27
- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main`; Head: `7b8994c`
- Cycle-entry findings: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/remediation-inputs.2026-06-05T21-27.md`
- Source artifacts:
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/policy-audit.2026-06-05T21-27.md`
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/code-review.2026-06-05T21-27.md`
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/feature-audit.2026-06-05T21-27.md`

## Scope

This cycle remediates exactly two findings and touches no production wiring. R1–R6 are
CLOSED and are not reopened.

- B1 (blocking): `tests/gui/test_schema_builder_presenter.py` is 506 lines, over the
  500-line cap that applies to test code. Split into focused modules, preserving every
  existing test verbatim. All resulting files must be <= 500 lines.
- N4 (non-blocking): `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py`
  report 0% coverage because they are never imported at runtime; the missed lines are
  structural (imports, `__all__`, `class`, method `def` signatures), not the `...`
  bodies, which are already excluded by `[tool.coverage.report].exclude_lines`
  (`^\s*\.\.\.\s*$`). Add both type-only protocol modules to `[tool.coverage.run].omit`
  in `pyproject.toml` so they no longer appear as 0%-covered rows, and revert the no-op
  `# pragma: no cover` lines previously added to the `...` bodies. No behavioral change.

## Constraints and Invariants to Preserve

- Do not delete, rename, or weaken any existing test or assertion during the split.
- Do not change production behavior. N4 is a coverage-config change: it adds two
  type-only contract modules to `[tool.coverage.run].omit` in `pyproject.toml` and
  reverts the no-op `# pragma: no cover` lines previously added to their `...` bodies.
  A `pyproject.toml` edit is a config change, not a workflow change, so
  `modified-workflow-needs-green-run` does not apply.
- Toolchain order per `.claude/rules/python.md`: Black → Ruff → Pyright → Pytest, run
  via Poetry with the `env -u VIRTUAL_ENV` prefix (Poetry virtual-env quirk).
- pytest-qt requires `QT_QPA_PLATFORM=offscreen`.
- Coverage thresholds (uniform, all tiers): line >= 85%, branch >= 75%, no regression
  on changed lines.
- All evidence artifacts MUST be written under
  `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/<kind>/`.

## Test-Split Design (Reference for Phase 1)

Pre-split source: `tests/gui/test_schema_builder_presenter.py` — 19 test functions
(18 plain `test_` + 1 parametrized into 3 cases) and 2 module-level helpers
(`_configure_valid_keyable_view`, `_stored_schema_with_structured_key_and_aggregate`).

Split outputs:

- `tests/gui/_schema_builder_presenter_fixtures.py` — shared helper module holding the
  two existing helpers verbatim, exported for import by both test modules.
- `tests/gui/test_schema_builder_presenter_core.py` — presenter state / edit-load /
  preview / formula tests:
  `test_save_assembles_and_persists_valid_schema`,
  `test_save_surfaces_validation_error_for_invalid_schema`,
  `test_update_preview_applies_schema_through_loader`,
  `test_update_preview_surfaces_validation_error`,
  `test_validate_formula_accepts_valid_expression`,
  `test_validate_formula_rejects_bad_expressions` (parametrized, 3 cases),
  `test_load_existing_renders_schema_into_view`,
  `test_update_preview_surfaces_loader_error`,
  `test_load_existing_renders_structured_key_and_dtypes`,
  `test_edit_load_modify_save_round_trips`,
  `test_save_rejects_unknown_discriminator`,
  `test_add_derived_appends_row_in_order`,
  `test_injected_evaluator_is_used`.
- `tests/gui/test_schema_builder_presenter_seeding.py` — seeding / new-from-template
  tests:
  `test_new_from_template_seeds_clears_name`,
  `test_new_from_template_save_as_does_not_overwrite_template`,
  `test_seed_from_caller_pre_lists_rows_and_parses_key`,
  `test_seed_from_caller_blank_menu_path_leaves_state_empty`,
  `test_seed_from_caller_reads_preview_slice_without_io`.

The original `tests/gui/test_schema_builder_presenter.py` is removed after the split so
no test is duplicated. Total test count must be unchanged: pre-split == post-split sum.

## B1 / N4 → Task Map

- B1: P0-T4, P0-T6, P1-T1, P1-T2, P1-T3, P1-T4, P1-T5, P1-T6, P2-T8, P2-T9
- N4: P0-T5, P1-T7, P2-T6 (coverage report confirms the two protocol modules are omitted)

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record them in `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/phase0-instructions-read.md` with `Timestamp:`, `Policy Order:`, and the explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`. Acceptance: artifact exists with all three fields populated.
- [x] [P0-T2] Capture baseline Black result by running `env -u VIRTUAL_ENV poetry run black --check .` and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-black.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact records the exact command and exit code.
- [x] [P0-T3] Capture baseline Ruff result by running `env -u VIRTUAL_ENV poetry run ruff check .` and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-ruff.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact records the exact command and exit code.
- [x] [P0-T4] Capture baseline Pyright result by running `env -u VIRTUAL_ENV poetry run pyright` and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-pyright.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact records the exact command and exit code.
- [x] [P0-T5] Capture baseline Pytest result with coverage by running `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-pytest.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` that records numeric baseline total line coverage %, branch coverage %, passed/failed counts, and the per-file coverage % for `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py`. Acceptance: numeric coverage headline values are present (not placeholders).
- [x] [P0-T6] Record the pre-split test count and the line count of the target file by running `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_builder_presenter.py --collect-only -q` and a line count of `tests/gui/test_schema_builder_presenter.py`, then write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/remediation-baseline/baseline-test-count.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` recording the exact collected-item count (parametrized cases counted individually) and the file line count (expected 506). Acceptance: collected-item count and 506-line file size are both recorded as the authoritative pre-split reference.

### Phase 1 — Split Test File (B1) and Omit Type-Only Protocol Modules from Coverage (N4)

- [x] [P1-T1] Create `tests/gui/_schema_builder_presenter_fixtures.py` containing the two existing helpers `_configure_valid_keyable_view` and `_stored_schema_with_structured_key_and_aggregate` copied verbatim (including docstrings and imports they require), with a module docstring describing the shared-fixture purpose. Acceptance: file exists, imports resolve, and the two helper bodies are byte-for-byte equivalent to the originals.
- [x] [P1-T2] Create `tests/gui/test_schema_builder_presenter_core.py` containing the 13 core tests enumerated in the Test-Split Design (including the parametrized `test_validate_formula_rejects_bad_expressions`) copied verbatim, importing the two helpers from `tests.gui._schema_builder_presenter_fixtures`. Acceptance: file exists; every listed test name is present with unchanged body and assertions.
- [x] [P1-T3] Create `tests/gui/test_schema_builder_presenter_seeding.py` containing the 5 seeding / new-from-template tests enumerated in the Test-Split Design copied verbatim, importing helpers from `tests.gui._schema_builder_presenter_fixtures` where used. Acceptance: file exists; every listed test name is present with unchanged body and assertions.
- [x] [P1-T4] Delete the original `tests/gui/test_schema_builder_presenter.py`. Acceptance: the original file no longer exists and no test name now appears in more than one module.
- [x] [P1-T5] Verify no assertion was dropped or weakened by diffing the union of test bodies in the two new modules plus helpers against the original file content (assertions, parametrize cases, and helper logic must all be present). Acceptance: every `assert` and every `@pytest.mark.parametrize` case from the original is accounted for in the new files; record the comparison result in the diff confirmation captured at P2-T9.
- [x] [P1-T6] Confirm post-split file sizes by line-counting `tests/gui/_schema_builder_presenter_fixtures.py`, `tests/gui/test_schema_builder_presenter_core.py`, and `tests/gui/test_schema_builder_presenter_seeding.py`. Acceptance: each of the three files is <= 500 lines.
- [x] [P1-T7] Apply the coverage-omit fix for N4 (Option A), the correct minimal fix. (a) Revert the no-op `# pragma: no cover` lines previously added to the `...` body lines in `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py`, restoring each `...` body to its pre-cycle state; leaving dead pragmas would recreate the N2 finding that cycle 1 fixed. These pragmas are no-ops because `[tool.coverage.report].exclude_lines` already excludes bare `...` bodies (`^\s*\.\.\.\s*$`). (b) Add `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py` to the `[tool.coverage.run].omit` list in `pyproject.toml` so these never-imported, type-only protocol modules no longer appear as 0%-covered rows in the coverage report; make no other change to either protocol module beyond the pragma revert. Acceptance: the two protocol files no longer appear as rows in the coverage report (omitted via `[tool.coverage.run].omit`); no `# pragma: no cover` remains in either protocol file; no signature, docstring, or `__all__` is altered; Ruff and Pyright stay clean.

### Phase 2 — Final QA Loop, Coverage, Masking, File-Size Gate, AC Re-Confirmation

- [x] [P2-T1] Run Black and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/final-black.2026-06-05T21-27.md`. Command: `env -u VIRTUAL_ENV poetry run black --check .`. Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: EXIT_CODE 0; if Black reformats any file, restart the loop at P2-T1.
- [x] [P2-T2] Run Ruff and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/final-ruff.2026-06-05T21-27.md`. Command: `env -u VIRTUAL_ENV poetry run ruff check .`. Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: EXIT_CODE 0 with zero lint errors.
- [x] [P2-T3] Run Pyright and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/final-pyright.2026-06-05T21-27.md`. Command: `env -u VIRTUAL_ENV poetry run pyright`. Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: EXIT_CODE 0 with zero type errors.
- [x] [P2-T4] Run the full test suite with coverage and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/final-pytest.2026-06-05T21-27.md`. Command: `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`. Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` with numeric post-change total line %, branch %, passed/failed counts, and confirmation that the two protocol modules `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py` are absent from the per-file report (omitted via `[tool.coverage.run].omit`). Acceptance: EXIT_CODE 0; all tests pass; if any prior QA step changed files, restart the loop at P2-T1.
- [x] [P2-T5] Confirm the post-split collected-item count equals the pre-split count from P0-T6 by running `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_builder_presenter_core.py tests/gui/test_schema_builder_presenter_seeding.py --collect-only -q` and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/regression-testing/test-count-parity.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` stating pre-split count, post-split sum, and the equality result. Acceptance: pre-split count == post-split sum (no test lost or added).
- [x] [P2-T6] Compare coverage against baseline and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/coverage-comparison.2026-06-05T21-27.md` with `Timestamp:`, `Command:` (reference P0-T5 and P2-T4), `EXIT_CODE:`, and an `Output Summary:` reporting baseline total line/branch %, post-change total line/branch %, changed-code coverage, and confirmation that `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py` are absent from the coverage report. Acceptance: the two protocol files no longer appear as 0%-covered rows in the coverage report (omitted via `[tool.coverage.run].omit`); overall coverage line >= 85% / branch >= 75% with no regression on changed lines.
- [x] [P2-T7] Run the masking scan over changed files and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/masking-scan.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` confirming no test was masked, skipped, xfailed, or weakened by the split. Acceptance: scan reports zero masked/weakened tests.
- [x] [P2-T8] Run the file-size gate over ALL resulting test files and the changed production/config files, enumerating each path and its line count: `tests/gui/_schema_builder_presenter_fixtures.py`, `tests/gui/test_schema_builder_presenter_core.py`, `tests/gui/test_schema_builder_presenter_seeding.py`, `src/gui/_columns_tab_protocol.py`, `src/gui/_key_tab_protocol.py`, `pyproject.toml`. Write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/final-file-sizes.2026-06-05T21-27.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` listing each enumerated file with its line count and a confirmation that `tests/gui/test_schema_builder_presenter.py` no longer exists. Acceptance: every enumerated file is <= 500 lines and the over-cap original is gone.
- [x] [P2-T9] Re-confirm acceptance criteria and the split fidelity, and write `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/evidence/qa-gates/ac-reconciliation.2026-06-05T21-27.md` with `Timestamp:` and an `Output Summary:` confirming: (a) the 22 AC checkboxes in `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` and the 16 AC checkboxes in `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md` remain valid with no AC regressed by this cycle (this cycle changes no features), and (b) the test-split preserved every assertion and parametrize case per P1-T5. Acceptance: no AC regressed; split fidelity confirmed.
