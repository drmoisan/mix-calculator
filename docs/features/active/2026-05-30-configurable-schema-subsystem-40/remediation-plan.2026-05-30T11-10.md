# Remediation Plan — Cycle 1: configurable-schema-subsystem (Epic #40)

**Entry timestamp:** 2026-05-30T11-10
**Cycle:** 1
**Feature folder:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40/`
**Base branch:** `main` (merge-base `d14d4e9d13c65864b44b23f83f66e330755feffd`)
**Head:** `epic/configurable-schema-subsystem-40` (`04dba2aec0127a64211846f47e8c3c122637e216`)
**Cycle-entry inputs:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40/remediation-inputs.2026-05-30T11-10.md`
**Source audit artifacts:**
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/policy-audit.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/code-review.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/feature-audit.2026-05-30T10-55.md`

## Scope and Constraints

This plan remediates two Minor, test-only, procedural findings (F1, F2) raised
by the comprehensive feature-review. Both are mechanical and carry no
production-behavior change.

- **Test-only.** No production module may be modified: `src/schema_*`, GUI
  production code under `src/gui/`, the CLI, transforms, loaders, or any other
  file under `src/`. No behavior change.
- **No new suppressions.** F1 is resolved by refactor only. Do NOT add an E402
  approval; do NOT edit any file under `.claude/rules/` (including
  `python-suppressions.md`).
- **File size.** Every changed or new file must remain `< 500` lines.
- **Determinism.** Tests remain deterministic; no temp files, no network, no
  real DB/Excel; in-memory fixtures only.
- **Per-batch budget.** Changes are limited to test-support files. The 3-production
  + 3-test per-batch cap is respected by splitting work across phases; no
  production file is touched in any phase.
- **Toolchain per change phase.** Run in order: Black -> Ruff -> Pyright strict ->
  Pytest with coverage. Restart from Black on any failure or auto-fix.
- **Coverage.** Baseline is 717 tests, 99.12% line / 96.46% branch. Coverage must
  not regress and the full suite must stay green (>= 717 passing).

## Evidence Location Invariant

All evidence artifacts produced by this plan are written under
`docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/<kind>/`
per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing to
`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other
non-canonical evidence path is a policy violation.

## Findings Mapped to Phases

- **F1** (Minor) — 9 unauthorized `# noqa: E402` directives across 6 test files,
  each on an `import aop_fixtures` / `import le_fixtures` placed after a
  `sys.path.insert(0, ...)`. Resolved in Phase 1 by refactor: import the shared
  fixtures as normal top-of-file package imports and remove the `sys.path.insert`
  lines and all 9 `# noqa: E402` directives. There is also one lazy
  `import aop_fixtures` inside a function (`tests/test_schema_loader_derived.py`
  line 154) that depends on the same `sys.path.insert`; it must be converted to a
  package import in the same phase or fixture resolution breaks when the insert
  is removed.
- **F2** (Minor) — `tests/gui/fakes/fake_views.py` is 508 lines (> 500 ceiling,
  which applies to test code). Resolved in Phase 2 by splitting into per-protocol
  fake modules under `tests/gui/fakes/`, keeping each file `<= 500` lines and
  preserving the existing `from tests.gui.fakes.fake_views import ...` import
  surface.

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read the policy files in required order and record an evidence artifact at `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/baseline/phase0-instructions-read.2026-05-30T11-10.md`. The artifact MUST include `Timestamp:`, `Policy Order:`, and an explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`. Acceptance: artifact exists with all required fields populated.
- [x] [P0-T2] Capture the baseline `# noqa: E402` and fixture `sys.path.insert` inventory. Run `poetry run ruff check . --select E402` and `git grep -n "noqa: E402"` plus `git grep -n "sys.path.insert"` across `tests/`. Write the combined output to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/baseline/baseline-e402-inventory.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`. Acceptance: artifact records the 9 `# noqa: E402` occurrences across the 6 named files and every `sys.path.insert` line tied to fixture imports.
- [x] [P0-T3] Capture the baseline file-size inventory for `tests/gui/fakes/`. Run `wc -l tests/gui/fakes/*.py` and write the output to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/baseline/baseline-fakes-linecount.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`. Acceptance: artifact records `tests/gui/fakes/fake_views.py` at 508 lines (> 500 ceiling).
- [x] [P0-T4] Capture the baseline format/lint/type signal. Run `poetry run black --check .`, then `poetry run ruff check .`, then `poetry run pyright`. Write each command's result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/baseline/baseline-format-lint-type.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command. Acceptance: artifact records the current pass/fail state of all three commands.
- [x] [P0-T5] Capture the baseline test + coverage signal. Run `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write the result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/baseline/baseline-pytest-coverage.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` that records numeric coverage headline values: test count (expected 717 passing), line coverage (expected 99.12%), and branch coverage (expected 96.46%). Acceptance: artifact records 717 passing tests with the baseline line and branch coverage percentages.

---

### Phase 1 — F1: Remove E402 Suppressions by Fixture-Import Refactor

The shared fixtures `tests/aop_fixtures.py` and `tests/le_fixtures.py` are imported
in 6 test files via `sys.path.insert(0, ...)` followed by a bare
`import aop_fixtures` / `import le_fixtures` carrying `# noqa: E402`. GUI tests in
this repository already import sibling test-support modules as packages
(`from tests.gui.fakes.fake_services import ...`), confirming `tests` resolves as
an importable (namespace) package under the repository's default pytest prepend
import mode. The refactor replaces each late, suppressed import with a normal
top-of-file package import and removes the `sys.path.insert` lines that existed
only to enable those imports.

Implementation note for each task below: the fixture import must become a
top-of-file import that does not require `sys.path` manipulation. Two acceptable
forms (the implementer chooses the one that keeps Ruff `I` import-ordering and
Pyright strict clean without a suppression): (a) `from tests import aop_fixtures` /
`from tests import le_fixtures`, or (b) move the modules into an importable
test-support package and import from there. Whichever form is used MUST be applied
consistently and MUST leave zero `# noqa: E402` and zero fixture-only
`sys.path.insert` lines. Do NOT add `# noqa` of any code, and do NOT modify any
file under `src/`.

- [x] [P1-T1] In `tests/test_schema_loader_core.py`, replace the two late suppressed imports (`import aop_fixtures  # noqa: E402`, `import le_fixtures  # noqa: E402` at lines 34-35) with top-of-file package imports and remove the `sys.path.insert(0, str(Path(__file__).resolve().parent))` line (line 32) and the now-unused `sys` / `Path` imports if they become unused. Acceptance: file contains zero `# noqa: E402`, no fixture-only `sys.path.insert`, all references to `aop_fixtures` / `le_fixtures` resolve, and `poetry run ruff check tests/test_schema_loader_core.py` reports no `E402`.
- [x] [P1-T2] In `tests/test_schema_loader_integration.py`, replace the two late suppressed imports (lines 28-29) with top-of-file package imports and remove the `sys.path.insert` line (line 26) plus now-unused `sys` / `Path` imports if applicable. Acceptance: file contains zero `# noqa: E402`, no fixture-only `sys.path.insert`, references resolve, and `poetry run ruff check tests/test_schema_loader_integration.py` reports no `E402`.
- [x] [P1-T3] In `tests/test_schema_loader_derived.py`, replace the late suppressed import (`import le_fixtures  # noqa: E402` at line 32) with a top-of-file package import, convert the lazy in-function `import aop_fixtures` (line 154) to the same top-of-file package import form, and remove the `sys.path.insert` line (line 30) plus now-unused `sys` / `Path` imports if applicable. Acceptance: file contains zero `# noqa: E402`, no fixture-only `sys.path.insert`, both `le_fixtures` and `aop_fixtures` resolve via top-of-file package imports, and `poetry run ruff check tests/test_schema_loader_derived.py` reports no `E402`.
- [x] [P1-T4] In `tests/test_schema_loader_parity_aop.py`, replace the late suppressed import (`import aop_fixtures  # noqa: E402` at line 29) with a top-of-file package import and remove the `sys.path.insert` line (line 27) plus now-unused `sys` / `Path` imports if applicable. Acceptance: file contains zero `# noqa: E402`, no fixture-only `sys.path.insert`, references resolve, and `poetry run ruff check tests/test_schema_loader_parity_aop.py` reports no `E402`.
- [x] [P1-T5] In `tests/test_schema_loader_parity_le.py`, replace the late suppressed import (`import le_fixtures  # noqa: E402` at line 30) with a top-of-file package import and remove the `sys.path.insert` line (line 28) plus now-unused `sys` / `Path` imports if applicable. Acceptance: file contains zero `# noqa: E402`, no fixture-only `sys.path.insert`, references resolve, and `poetry run ruff check tests/test_schema_loader_parity_le.py` reports no `E402`.
- [x] [P1-T6] In `tests/gui/integration/test_behavioral_schema_import.py`, replace the two late suppressed imports (lines 35-36) with top-of-file package imports and remove the `sys.path.insert(0, str(Path(__file__).resolve().parents[2]))` line (line 33) plus now-unused `sys` / `Path` imports if applicable. Acceptance: file contains zero `# noqa: E402`, no fixture-only `sys.path.insert`, references resolve, and `poetry run ruff check tests/gui/integration/test_behavioral_schema_import.py` reports no `E402`.
- [x] [P1-T7] Run the toolchain loop for the Phase 1 changes: `poetry run black .`, then `poetry run ruff check .`, then `poetry run pyright`, then `poetry run pytest --cov --cov-branch --cov-report=term-missing`. If any step fails or changes files, fix within the test-only scope and restart from Black. Write the final clean-pass results to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/phase1-toolchain.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command (test summary MUST include numeric test count and line/branch coverage). Acceptance: all four commands pass in a single pass; test count >= 717; line coverage >= 99.12% and branch coverage >= 96.46% (no regression).
- [x] [P1-T8] Verify F1 closure across the whole tree. Run `poetry run ruff check . --select E402`, `git grep -n "noqa: E402" -- tests` (or `rg -n "noqa: E402" tests`), and `git grep -n "sys.path.insert" -- tests`. Write results to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/phase1-e402-closure.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`. Acceptance: zero `E402` findings, zero `# noqa: E402` directives remain in the diff, and no `sys.path.insert` remains that existed solely for fixture imports.

---

### Phase 2 — F2: Split `fake_views.py` Below the 500-Line Ceiling

`tests/gui/fakes/fake_views.py` (508 lines) defines four view fakes:
`FakeSourceSelectionView`, `FakePipelineView`, `FakeExportView`,
`FakeColumnMatchingView`, and `FakeSchemaBuilderView`. Sixteen consumer modules
import specific names from `tests.gui.fakes.fake_views`. The split moves the view
fakes into per-protocol modules under `tests/gui/fakes/` and keeps
`fake_views.py` as a thin re-export so the existing import surface continues to
work without touching consumers. Every resulting file must be `<= 500` lines. No
behavior change; the fake classes are copied verbatim with their docstrings.

- [x] [P2-T1] Create `tests/gui/fakes/fake_schema_builder_view.py` containing the `FakeSchemaBuilderView` class moved verbatim from `fake_views.py` (including its module docstring scoped to the schema-builder fake and the `from __future__ import annotations` header). Acceptance: file defines `FakeSchemaBuilderView` with all methods intact, is `<= 500` lines, and `poetry run pyright` reports no new errors for it.
- [x] [P2-T2] Create `tests/gui/fakes/fake_column_matching_view.py` containing the `FakeColumnMatchingView` class moved verbatim from `fake_views.py` (with module docstring and future-annotations header). Acceptance: file defines `FakeColumnMatchingView` with all methods intact, is `<= 500` lines.
- [x] [P2-T3] Create `tests/gui/fakes/fake_pipeline_view.py` containing the `FakePipelineView` and `FakeExportView` classes moved verbatim from `fake_views.py` (with module docstring and future-annotations header). Acceptance: file defines both classes with all methods intact, is `<= 500` lines.
- [x] [P2-T4] Create `tests/gui/fakes/fake_source_selection_view.py` containing the `FakeSourceSelectionView` class moved verbatim from `fake_views.py` (with module docstring and future-annotations header). Acceptance: file defines `FakeSourceSelectionView` with all methods intact, is `<= 500` lines.
- [x] [P2-T5] Rewrite `tests/gui/fakes/fake_views.py` as a thin re-export module that imports the four view fakes from the new per-protocol modules and re-exports them via an explicit `__all__` so existing `from tests.gui.fakes.fake_views import ...` imports continue to resolve. Keep a module docstring describing the re-export purpose. Acceptance: `fake_views.py` contains no class definitions, re-exports `FakeSourceSelectionView`, `FakePipelineView`, `FakeExportView`, `FakeColumnMatchingView`, and `FakeSchemaBuilderView`, and is `<= 500` lines.
- [x] [P2-T6] Run the toolchain loop for the Phase 2 changes: `poetry run black .`, then `poetry run ruff check .`, then `poetry run pyright`, then `poetry run pytest --cov --cov-branch --cov-report=term-missing`. If any step fails or changes files, fix within the test-only scope and restart from Black. Write the final clean-pass results to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/phase2-toolchain.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` per command (test summary MUST include numeric test count and line/branch coverage). Acceptance: all four commands pass in a single pass; test count >= 717; line coverage >= 99.12% and branch coverage >= 96.46% (no regression).
- [x] [P2-T7] Verify F2 closure. Run `wc -l tests/gui/fakes/*.py`. Write results to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/phase2-fakes-linecount.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`. Acceptance: every file under `tests/gui/fakes/` is `<= 500` lines, including the rewritten `fake_views.py`.

---

### Phase 3 — Final QA Loop and Closure Evidence

- [x] [P3-T1] Run the full Python toolchain loop in order on the complete tree: `poetry run black .` (acceptance: exit 0, no files reformatted). If files change, restart the loop. Write the result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/final-black.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P3-T2] Run `poetry run ruff check .` (acceptance: exit 0, zero findings, zero `E402` directives in the diff). If Ruff auto-fixes any file, restart from P3-T1. Write the result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/final-ruff.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P3-T3] Run `poetry run pyright` (acceptance: exit 0, zero errors under strict mode). Write the result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/final-pyright.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P3-T4] Run `poetry run pytest --cov --cov-branch --cov-report=term-missing` (acceptance: all tests pass, test count >= 717, line coverage >= 99.12%, branch coverage >= 96.46%; no regression versus baseline). Write the result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/final-pytest-coverage.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` recording numeric test count and line/branch coverage.
- [x] [P3-T5] Record the coverage delta verification at `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/coverage-delta.2026-05-30T11-10.md` with `Timestamp:`, baseline coverage (line 99.12% / branch 96.46% from P0-T5), post-change coverage (from P3-T4), and changed-code coverage note (changes are test-only; production coverage is unaffected). Acceptance: post-change line coverage >= baseline and branch coverage >= baseline; no changed-line regression.
- [x] [P3-T6] Confirm no production file was modified. Run `git diff --name-only main...HEAD` (or against the merge-base `d14d4e9`) and verify every changed path is under `tests/`. Write the result to `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/scope-check.2026-05-30T11-10.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`. Acceptance: zero changed paths under `src/`, `.claude/rules/`, `.github/`, or any non-test location; all changes confined to `tests/`.

---

## Acceptance Criteria (cycle exit)

- F1 resolved by refactor: zero `# noqa: E402` directives remain in the diff
  (P1-T8, P3-T2); no `sys.path.insert` remains solely for fixture imports
  (P1-T8); `poetry run ruff check .` reports zero `E402` (P3-T2).
- F2 resolved: every file under `tests/gui/fakes/` is `<= 500` lines (P2-T7);
  the existing import surface is preserved via re-export (P2-T5).
- No production module modified; all changes confined to `tests/` (P3-T6).
- No new suppressions added; no policy file edited.
- Full toolchain passes in a single clean pass: Black -> Ruff -> Pyright strict ->
  Pytest with coverage (P3-T1 through P3-T4).
- Coverage does not regress: line >= 99.12%, branch >= 96.46%, test count >= 717
  (P3-T4, P3-T5).
- All evidence artifacts written under
  `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/<kind>/`.

## Out of Scope (informational; not part of this loop)

- T1 mutation testing for `src/schema_formula.py` / `src/schema_loader.py`
  (pre-merge/nightly gate per `quality-tiers.md`).
- `asteval` typing/approval (user-approved 2026-05-30; no action).
