# Remediation Inputs — Cycle 1: configurable-schema-subsystem (Epic #40)

**Entry timestamp:** 2026-05-30T11-10
**Cycle:** 1
**Base branch:** `main` (merge-base `d14d4e9d13c65864b44b23f83f66e330755feffd`)
**Head:** `epic/configurable-schema-subsystem-40` (`04dba2aec0127a64211846f47e8c3c122637e216`)
**Source audit artifacts (from the comprehensive feature-review):**
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/policy-audit.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/code-review.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/feature-audit.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/remediation-inputs.2026-05-30T10-55.md` (reviewer-authored, superseded by this orchestrator cycle-entry inputs)

## Disposition

All 37 acceptance criteria across child features #41-#44 PASS. The toolchain is
clean (Black, Ruff, Pyright strict, 717 tests, 99.12% line / 96.46% branch). No
code-correctness, security, or coverage failure. Two Minor, procedural,
test-only findings hold the policy verdict at PARTIALLY COMPLIANT and must be
remediated before merge. Neither is a Blocker or Major; both are mechanical with
no production-behavior change.

## Findings to remediate this cycle

### F1 (Minor) — Unauthorized `# noqa: E402` suppressions in test fixtures

- 9 occurrences across 6 test files:
  - `tests/test_schema_loader_core.py` (2)
  - `tests/test_schema_loader_derived.py` (1)
  - `tests/test_schema_loader_integration.py` (2)
  - `tests/test_schema_loader_parity_aop.py` (1)
  - `tests/test_schema_loader_parity_le.py` (1)
  - `tests/gui/integration/test_behavioral_schema_import.py` (2)
- Each suppresses Ruff `E402` on `import aop_fixtures` / `import le_fixtures`
  placed after a deliberate `sys.path.insert(0, ...)`. `E402` is NOT a
  pre-authorized pattern in `.claude/rules/python-suppressions.md` and has no
  recorded user approval.
- **Required resolution (Option 1 — refactor; no suppression, no policy edit):**
  make the shared in-memory fixtures importable without `sys.path` manipulation.
  Move `aop_fixtures.py` / `le_fixtures.py` into an importable test-support
  package (e.g. `tests/fixtures/` with `__init__.py`) and/or expose them via a
  `conftest.py`, then replace the post-`sys.path` imports with normal top-of-file
  package imports. Remove every `sys.path.insert` that existed only to enable
  those imports, and remove all 9 `# noqa: E402` directives.
- Do NOT take Option 2 (record E402 approval) or Option 3 (edit the policy file);
  the refactor is the sanctioned, suppression-free fix.
- **Acceptance:** `poetry run ruff check .` passes with zero `E402` directives
  remaining anywhere in the diff; no `sys.path.insert` remains solely for fixture
  imports; `poetry run pytest` stays green (717 pass).

### F2 (Minor) — Test file exceeds the 500-line ceiling

- `tests/gui/fakes/fake_views.py` is 508 lines; the 500-line ceiling in
  `.claude/rules/general-code-change.md` applies to test code.
- **Required resolution:** split the module into per-protocol fake modules under
  `tests/gui/fakes/` (e.g. `fake_schema_builder_view.py`,
  `fake_column_matching_view.py`), keep each file <= 500 lines, and update
  imports. No behavior change. If a thin re-export from `fake_views.py` keeps
  existing imports working, ensure the resulting `fake_views.py` is also <= 500.
- **Acceptance:** every file under `tests/gui/fakes/` is <= 500 lines
  (`wc -l tests/gui/fakes/*.py`); `poetry run pytest` stays green.

## Hard constraints for the remediation

- Test-only changes. Do NOT modify any production module, the schema_* modules,
  the GUI production code, the CLI, or transforms. No behavior change.
- No new suppressions; resolve F1 by refactor, not by suppression or policy edit.
- Every changed/new file < 500 lines.
- Tests remain deterministic; no temp files, no network, no real DB/Excel.
- Full toolchain must pass in a single clean pass: Black -> Ruff -> Pyright
  strict -> Pytest with coverage; coverage must not regress.

## Exit criteria for this cycle

After remediation, re-run the full toolchain and re-audit (feature-review). The
cycle exits only when the re-audit reports zero blocking findings AND the policy
verdict reaches FULLY COMPLIANT (both F1 and F2 resolved).

## Non-remediation notes (informational)

- T1 mutation testing for `src/schema_formula.py` / `src/schema_loader.py` is a
  pre-merge/nightly gate per `quality-tiers.md`, not part of this loop.
- `asteval` is user-approved (2026-05-30) and typed via `typings/asteval/__init__.pyi`
  with no suppression. No action.
