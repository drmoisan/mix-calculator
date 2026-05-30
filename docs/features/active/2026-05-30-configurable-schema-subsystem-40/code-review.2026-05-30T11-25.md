# Code Review: configurable-schema-subsystem (Epic #40) — Cycle-1 Re-Review

**Review Date:** 2026-05-30
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40`
**Feature Folder Selection Rule:** Epic folder whose suffix (`-40`) matches the issue number in the branch name `epic/configurable-schema-subsystem-40`.
**Base Branch:** `main` (merge-base `d14d4e9`)
**Head Branch:** `epic/configurable-schema-subsystem-40` @ `0ddfc53`
**Review Type:** Post-remediation re-review (cycle 1)

---

## Executive Summary

This is the cycle-1 re-review of the configurable-schema-subsystem epic after the F1/F2 remediation commit `0ddfc53`. The reviewed scope is the full branch diff `main...HEAD` (not a plan subset). The epic delivers, across child features #41–#44: a typed persisted schema model + shared registry + bundled default AOP/LE schemas; a pure column-matching/best-match-discovery engine; a configurable ETL core with a sandboxed asteval formula engine and ratio recompute; and a GUI schema builder with manual column matching and runtime formula entry wired into the import flow.

**What changed:** The cycle-1 remediation commit `0ddfc53` is test-only. F1: nine `# noqa: E402` directives and the fixture-only `sys.path.insert` lines were removed across six test files; shared in-memory fixtures (`aop_fixtures`, `le_fixtures`) are now imported as top-of-file package imports (`from tests import aop_fixtures`). F2: `tests/gui/fakes/fake_views.py` was reduced from 508 to 23 lines (a thin re-export) and per-protocol fakes were split into separate files, each <= 500 lines. No production module was touched by the remediation. The underlying feature implementation (commits #41–#44) is unchanged since cycle 0, where it was reviewed as functionally complete with a clean toolchain.

**Top 3 risks:**
1. Formula-engine sandbox escape — mitigated: asteval is constrained behind a typed adapter that validates/rejects imports, dunder access, subscripting, comprehensions, lambdas, and non-whitelisted calls; rejection is covered by property/fuzz tests.
2. Exact-reproduction drift from the legacy AOP/LE loaders — mitigated: parity tests assert `assert_frame_equal` against `load_aop` and `normalize`.
3. GUI regression of known-file import behavior — mitigated: behavioral import-flow integration test and the full existing GUI suite stay green.

**PR readiness recommendation:** **Go** — Both prior findings are resolved by a clean test-only refactor; the full toolchain is green and coverage exceeds thresholds; no Blocker, Major, or Minor finding remains.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `tests/gui/fakes/fake_views.py` | whole file | F2 resolved: reduced from 508 to 23 lines as a thin re-export; per-protocol fakes split out, each <= 500 lines | None — confirmed compliant | Closes the cycle-0 F2 over-ceiling finding | `wc -l tests/gui/fakes/*.py` (max 414) |
| Info | `tests/test_schema_loader_*.py`, `tests/gui/integration/test_behavioral_schema_import.py` | import headers | F1 resolved: all 9 `# noqa: E402` and fixture-only `sys.path.insert` removed; fixtures imported as top-of-file package imports | None — confirmed compliant | Closes the cycle-0 F1 unauthorized-suppression finding without adding suppression or editing policy | `git grep "noqa: E402"`/`sys.path.insert` over code returns no matches; `poetry run ruff check .` passes |
| Info | `typings/asteval/__init__.pyi` | whole file | User-approved `asteval` is typed via a fully annotated local stub (no `# type: ignore`/`# pyright: ignore`) | None | Confirms AC7 (#43) and the suppression-free typing constraint | `poetry run pyright` — 0 errors strict |

No Blockers or Major findings. No Minor findings. blocking_count: 0.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The F1 fix is a genuine refactor, not a suppression: making the shared fixtures importable as a package (`from tests import aop_fixtures` / `from tests.le_fixtures import ...`) removes the root cause (`sys.path.insert`) rather than masking the E402 warning. The ruff `per-file-ignores` block was left at `tests/**/* = ["S101"]` with no E402 escape hatch added.
- The F2 split keeps a thin `fake_views.py` re-export so existing imports continue to work while every per-protocol fake module stays well under the 500-line ceiling.
- The asteval adapter constrains the interpreter symtable to whitelisted functions plus row/column values and inspects the post-eval `.error` list, raising a descriptive `FormulaError`. The local typed stub declares only the narrow surface the adapter uses.

#### Typing and API notes

- Pyright strict passes with 0 errors. No `Any` in public signatures. Frozen dataclasses model the schema; view/service protocols define the GUI seam. New modules are classified in `quality-tiers.yml` (formula engine + loader core T1; model/serialization/matching/presenters/service T2; Qt dialogs T3).

#### Error handling and logging

- Specific exceptions throughout (`FormulaError`, descriptive `ValueError` for malformed JSON / invariant violations). Invariants enforced in `SchemaDefinition.__post_init__`. No broad catch-all observed.

---

## Test Quality Audit

The full suite (717 tests) passes in 31.73s with 99.12% line / 96.46% branch coverage. The remediation preserved determinism: fixtures remain pure in-memory builders, now reached via package imports rather than path manipulation.

### Reviewed test and QA artifacts

- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/phase1-e402-closure.2026-05-30T11-10.md` — verifies zero `# noqa: E402` and zero fixture-only `sys.path.insert` remain after refactor.
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/phase2-fakes-linecount.2026-05-30T11-10.md` — verifies every `tests/gui/fakes/*.py` is <= 500 lines.
- `docs/features/active/2026-05-30-configurable-schema-subsystem-40/evidence/qa-gates/final-pytest-coverage.2026-05-30T11-10.md` — 717 pass, coverage headline.
- `artifacts/python/lcov.info` — regenerated this re-review run.

### Quality assessment prompts

- **Determinism:** No temp files; in-memory SQLite/openpyxl; Hypothesis seed-on-failure; Qt offscreen.
- **Isolation:** Each test targets a single behavior; parity/integration suites isolate loader vs transforms.
- **Speed:** 31.73s for 717 tests.
- **Diagnostics:** Descriptive `FormulaError`/`ValueError` messages name the offending construct/column.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No credentials/keys in the diff; config files are schema JSON only. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess in the schema subsystem; asteval is sandboxed behind the validating adapter. |
| Input validation at boundaries | ✅ PASS | Formula validation rejects disallowed constructs and unknown columns; JSON adapter validates keys/required fields. |
| Error handling remains explicit | ✅ PASS | Specific exceptions; invariants at construction; no silent swallow. |
| Configuration / path handling is safe | ✅ PASS | Registry directory resolved via settings/env seam, unit-tested without disk. |

---

## Research Log

No external research was required. The review relied on diff inspection, the re-run toolchain output, coverage data, and the feature-folder QA-gate evidence artifacts.

---

## Verdict

The cycle-1 re-review confirms the remediation commit `0ddfc53` resolves both prior findings cleanly and is strictly test-only — no production code changed. F1 was fixed by refactoring fixtures into importable package modules (zero `# noqa: E402`, zero fixture-only `sys.path.insert`, no policy edit), and F2 by splitting the over-ceiling fake module so every `tests/gui/fakes/*.py` file is <= 500 lines. The full Python toolchain is clean in a single pass and coverage exceeds the uniform thresholds.

The change is ready for normal PR flow. This recommendation is consistent with the Findings Table (no Blocker/Major/Minor) and the Go readiness recommendation above.
