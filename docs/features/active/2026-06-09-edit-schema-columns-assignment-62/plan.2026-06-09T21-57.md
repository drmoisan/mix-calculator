# edit-schema-columns-assignment (Plan)

- **Issue:** #62
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-09T22-30
- **Status:** Draft
- **Version:** 1.0
- **Work Mode:** minor-audit
- **Requirements source (sole):** `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/issue.md` — `## Acceptance Criteria` section only.

**Fail-closed evidence rule:** Phase 0 baseline artifacts, Phase 2 final-QC artifacts, and the coverage-comparison artifact are mandatory. If any required baseline, QA, or coverage-comparison artifact is missing or has incomplete fields (`Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`), the audit verdict must be BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Each evidence-producing task records its canonical artifact path under `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/<kind>/`. Do not mark evidence-backed work complete without the artifact on disk.

**Evidence location invariant:** All evidence artifacts MUST be written under `docs/features/active/2026-06-09-edit-schema-columns-assignment-62/evidence/<kind>/` per `evidence-and-timestamp-conventions`. Non-canonical paths (`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, etc.) are prohibited and fail preflight.

**Single in-scope language:** Python (Black → Ruff → Pyright → Pytest). Coverage policy applies (>= 85% line, >= 75% branch, no regression on changed lines).

---

## Root-cause summary (verified by code inspection)

- `ColumnsTabPresenter._render_assignments_and_dtypes` (src/gui/presenters/_columns_tab_presenter.py:334) renders each row's assignment from `state.consumed_columns.get(canonical)`.
- `consumed_columns` is populated only by `prepopulate()` (live fuzzy match against `state.source_columns`, src/gui/presenters/_columns_tab_presenter.py:80) or by `assign_column` (manual drop).
- The edit path: `SchemaBuilderPresenter.load_existing` → `_state_from_schema` (src/gui/presenters/schema_builder_presenter.py:265) loads each column row WITH its persisted aliases → `_render_state` → `view.set_columns` → `DragTabBinder.set_columns` (src/gui/widgets/_schema_builder_drag_tabs.py:95) resets `consumed_columns = {}`, rebuilds an empty source pool (no `preview_slice`), then calls `prepopulate()` — which has nothing to match.
- Net: persisted aliases are loaded into rows but never reflected into `consumed_columns`, so `set_assignment(canonical, None)` is pushed for every row.

## Fix direction (verified, minimal)

- The fix is presenter-level inside `ColumnsTabPresenter.prepopulate()` (and/or a small private seed helper it calls). After the live fuzzy-match pass, for each canonical row that is NOT already assigned (`canonical not in consumed_columns`) and that carries a persisted alias, seed `consumed_columns[canonical]` from that alias.
- Ordering is deterministic and live-match-wins: the fuzzy-match pass runs first; alias seeding only fills rows the live pass left unassigned. This preserves AC-3 (a live match is never overridden or duplicated).
- One-source-per-row invariant: seed at most one alias per row (the persisted assignment), and do not re-add a source already consumed by the live pass. `_bind` is alias-idempotent (`_add_alias` de-duplicates), so no duplicate aliases are produced.
- Source-pool reflection decision: in the edit-from-button path there is no `preview_slice`, so the source pool is empty and the alias is the only assignment signal. The plan does NOT add the aliased source name back into the empty pool; the assignment is reflected only through `consumed_columns` (the rendered-assignment map). This keeps the render contract intact without inventing a phantom pool entry. The implementation task documents this decision in the helper docstring.
- `DragTabBinder.set_columns` already calls `prepopulate()` after loading rows. Confirmed: a presenter-level fix requires NO binder change.
- Constraints held: no Qt import added; no I/O; no new dependency; presenter stays Qt-free.

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record the read evidence. Order: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`. AC: artifact `evidence/baseline/phase0-instructions-read.md` exists with `Timestamp:`, `Policy Order:`, and the explicit list of files read.
- [x] [P0-T2] Record branch/commit baseline. AC: artifact `evidence/baseline/phase0-branch-commit.md` exists with `Timestamp:`, current branch name, and `HEAD` short SHA.
- [x] [P0-T3] Capture Black baseline. Command: `poetry run black --check .`. AC: artifact `evidence/baseline/baseline-black.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (pass/fail and count of files that would reformat).
- [x] [P0-T4] Capture Ruff baseline. Command: `poetry run ruff check .`. AC: artifact `evidence/baseline/baseline-ruff.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error count).
- [x] [P0-T5] Capture Pyright baseline. Command: `poetry run pyright`. AC: artifact `evidence/baseline/baseline-pyright.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).
- [x] [P0-T6] Capture Pytest + coverage baseline. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. AC: artifact `evidence/baseline/baseline-pytest.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including passed/failed counts and numeric headline line-coverage % and branch-coverage % (no placeholders).
- [x] [P0-T7] Record baseline line counts of the files expected to change. Files: `src/gui/presenters/_columns_tab_presenter.py`, `tests/gui/test_columns_tab_presenter.py`, `tests/gui/test_schema_builder_presenter_core.py`, `tests/gui/test_edit_schema_wiring.py`. AC: artifact `evidence/baseline/baseline-file-sizes.md` records each file's current line count and notes that the 500-line cap applies; confirms `src/gui/widgets/source_input_widget.py` is out of scope and must not be touched.

### Phase 1 — Constrained Small-Path Implementation (placeholder)

- [x] [P1-T1] Implement the persisted-alias seeding in `ColumnsTabPresenter.prepopulate()` (src/gui/presenters/_columns_tab_presenter.py). After the existing live fuzzy-match loop and before `self._render()`, run a second deterministic pass: for each canonical row in `self._state.columns`, if `canonical not in self._state.consumed_columns` and the row carries at least one persisted alias, seed `self._state.consumed_columns[canonical] = <first persisted alias>` (do not modify `source_columns`, do not re-call `_bind` in a way that re-appends an already-present alias). Prefer extracting a private helper (for example `_seed_from_persisted_aliases`) with a full docstring documenting the live-match-wins ordering and the decision NOT to reflect the alias into the source pool. AC: each row with a persisted alias and no live match has its assignment in `consumed_columns`; live-matched rows are unchanged; no Qt import is added; no I/O is introduced; file remains under 500 lines. Maps to AC-1, AC-2, AC-3.
- [x] [P1-T2] Add a positive unit test for AC-1 in `tests/gui/test_columns_tab_presenter.py`: construct a `SchemaBuilderState` with column rows carrying persisted aliases and an EMPTY `source_columns` pool (edit-from-button path), drive `ColumnsTabPresenter.prepopulate()` with `FakeColumnsTabView`, and assert `view.assignments` contains `(canonical, <alias>)` for each aliased row (not `None`). AC: test fails before P1-T1 and passes after; deterministic; no temp files; no Qt. Maps to AC-1.
- [x] [P1-T3] Add a negative unit test for AC-2 in `tests/gui/test_columns_tab_presenter.py`: a state with one aliased row and one row with no alias (empty pool); assert the no-alias row renders `(canonical, None)`. AC: test passes after fix; deterministic. Maps to AC-2.
- [x] [P1-T4] Add a no-regression unit test for AC-3 (live-preview-slice path) in `tests/gui/test_columns_tab_presenter.py`: reuse the existing `_state_with_pool()` style fixture where a live `source_columns` pool fuzzy-matches a canonical row that ALSO carries a different persisted alias; assert the live fuzzy match wins (`consumed_columns[canonical]` equals the live-pool match, not the persisted alias) and that the source is not duplicated across rows (one-source-per-row holds). AC: existing fuzzy-prepopulation tests still pass; the new test confirms live-match precedence. Maps to AC-3.
- [x] [P1-T5] Add an AC-4 round-trip test in `tests/gui/test_schema_builder_presenter_core.py`: using `SchemaBuilderPresenter` with a fake schema service and a fake view, `load_existing(name)` a schema whose columns carry aliases, then `save()` and assert the saved schema's column aliases are retained (assignments preserved through the edit-then-save round-trip). AC: deterministic; no temp files; no I/O beyond the fake service. Maps to AC-4.
- [x] [P1-T6] Confirm no production change is required in `src/gui/widgets/_schema_builder_drag_tabs.py` (the binder already calls `prepopulate()` after `set_columns`). AC: a short note in the PR/implementation summary states the binder path was verified and left unchanged; no edit to that file.
- [x] [P1-T7] Implementation completion acceptance: all four AC tests (P1-T2..P1-T5) pass; the full Phase 2 loop is ready to run; no file in scope exceeds 500 lines; presenter remains Qt-free and I/O-free. AC: P1-T2, P1-T3, P1-T4, P1-T5 green and root-cause behavior corrected.

### Phase 2 — Final QC Loop

Run the toolchain in order: format → lint → type-check → test. If any step changes files or fails, restart from the formatter and rerun the full loop until a single clean pass completes. Each command-bearing task below is unconditional and must be executed and recorded (no SKIPPED).

- [x] [P2-T1] Format. Command: `poetry run black .`. AC: artifact `evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. If files were reformatted, restart the loop.
- [x] [P2-T2] Lint. Command: `poetry run ruff check .`. AC: artifact `evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (0 errors required; no unauthorized suppressions added).
- [x] [P2-T3] Type-check. Command: `poetry run pyright`. AC: artifact `evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (0 errors required).
- [x] [P2-T4] Test with coverage. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. AC: artifact `evidence/qa-gates/final-pytest.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` including passed/failed counts and numeric post-change line-coverage % and branch-coverage % (no placeholders).
- [x] [P2-T5] Coverage delta/threshold verification. AC: artifact `evidence/qa-gates/coverage-comparison.md` records baseline coverage (from P0-T6), post-change coverage (from P2-T4), and changed-line coverage for the modified production file; confirms line >= 85%, branch >= 75%, and no regression on changed lines. If any threshold is unmet, outcome is remediation-required, not PASS.
- [x] [P2-T6] File-size-cap scan of ALL changed files. AC: artifact `evidence/qa-gates/file-size-scan.md` lists every file changed in this fix (production AND test) with its final line count and confirms each is <= 500 lines. Explicitly confirms `src/gui/widgets/source_input_widget.py` was not modified. If any changed file exceeds 500 lines, outcome is remediation-required, not PASS.
- [x] [P2-T7] AC traceability check. AC: artifact `evidence/qa-gates/ac-traceability.md` maps each of AC-1, AC-2, AC-3, AC-4 to the specific passing test(s) (P1-T2..P1-T5) and the production change (P1-T1), confirming every acceptance criterion in `issue.md` `## Acceptance Criteria` is covered by an executed, passing test.
