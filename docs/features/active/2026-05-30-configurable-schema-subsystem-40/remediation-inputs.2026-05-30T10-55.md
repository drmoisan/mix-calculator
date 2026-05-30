# Remediation Inputs: configurable-schema-subsystem (Epic #40)

**Generated:** 2026-05-30
**Base branch:** `main` (merge-base `d14d4e9d13c65864b44b23f83f66e330755feffd`)
**Head:** `epic/configurable-schema-subsystem-40` (`04dba2aec0127a64211846f47e8c3c122637e216`)
**Source artifacts:**
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/policy-audit.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/code-review.2026-05-30T10-55.md`
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/feature-audit.2026-05-30T10-55.md`

## Disposition

All 37 acceptance criteria PASS. No code-correctness, security, or coverage failure. The toolchain is clean (Black, Ruff, Pyright strict, 717 tests, 99.12% line / 96.46% branch coverage). Two procedural (non-blocking, non-code-defect) findings hold the policy verdict at PARTIALLY COMPLIANT and require a minor remediation pass before merge. Neither finding is a Blocker or Major.

The `modified-workflow-needs-green-run` rule does NOT fire: the branch diff modifies no path under `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**` (verified by name-only diff scan).

## Remediation-Required Findings

### F1 (Minor) — Unauthorized `# noqa: E402` suppressions in test fixtures

- **Severity:** Minor (procedural; code is locally safe).
- **Locations (9 occurrences):**
  - `tests/test_schema_loader_core.py:34-35`
  - `tests/test_schema_loader_derived.py:32`
  - `tests/test_schema_loader_integration.py:28-29`
  - `tests/test_schema_loader_parity_aop.py:29`
  - `tests/test_schema_loader_parity_le.py:30`
  - `tests/gui/integration/test_behavioral_schema_import.py:35-36`
- **Problem:** Each suppresses Ruff E402 (module-level import not at top) on `import aop_fixtures` / `import le_fixtures` placed after a deliberate `sys.path.insert(0, ...)`. E402 is not a pre-authorized pattern in `.claude/rules/python-suppressions.md`, and there is no recorded explicit user approval for E402.
- **Resolution options (any one resolves the finding):**
  1. **Refactor (preferred):** make the shared in-memory fixtures importable without `sys.path` manipulation — e.g. move `aop_fixtures.py`/`le_fixtures.py` into an importable package (`tests/fixtures/`) with an `__init__.py`, or expose them as `conftest.py` fixtures. This removes the `sys.path.insert` and therefore the E402 directives entirely.
  2. **Record explicit approval:** obtain and record explicit user approval for `# noqa: E402` on shared-fixture imports in test code.
  3. **Add a pre-authorized pattern:** add an E402 entry to `.claude/rules/python-suppressions.md` with a required comment format (e.g. `# noqa: E402 - fixture import after test sys.path bootstrap`) and update each directive to match verbatim. (Policy-document edit — requires user authorization; this reviewer does not modify policy files.)
- **Acceptance check after fix:** `poetry run ruff check .` passes with zero E402 directives remaining (Option 1) OR every E402 directive matches a pre-authorized pattern / recorded approval (Options 2-3); `poetry run pytest -q` stays green (717 pass).

### F2 (Minor) — Test file exceeds the 500-line ceiling

- **Severity:** Minor (procedural; file-size policy applies to test code).
- **Location:** `tests/gui/fakes/fake_views.py` — 508 lines (was 218 at base `d14d4e9`).
- **Problem:** `general-code-change.md` sets a 500-line ceiling on production code, test code, and reusable scripts. Only markdown docs, raw text fixtures, and throwaway scripts are exempt. This fake-views module is 8 lines over.
- **Resolution:** split the module into per-protocol fake modules under `tests/gui/fakes/` (for example `fake_schema_builder_view.py` and `fake_column_matching_view.py`), keeping each under 500 lines, and update imports. No behavior change.
- **Acceptance check after fix:** `wc -l tests/gui/fakes/*.py` shows every file <= 500 lines; `poetry run pytest -q` stays green.

## Non-Remediation Notes (informational, no action required for merge)

- **T1 mutation testing** (`src/schema_formula.py`, `src/schema_loader.py`, >= 75% score) is a pre-merge/nightly pipeline gate per `.claude/rules/quality-tiers.md`, not part of the per-commit feature-review loop. Confirm in the pre-merge pipeline; not a feature-review blocker.
- **`asteval` dependency** is user-approved (2026-05-30) for the formula engine and typed via `typings/asteval/__init__.pyi` with no suppression. No action.

## Suggested remediation scope

A single minor remediation plan covering F1 and F2 (both isolated, mechanical, no behavior change). After remediation, re-run the full toolchain and re-audit; the policy verdict is expected to reach FULLY COMPLIANT and PR readiness to reach Go.
