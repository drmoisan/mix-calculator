# Remediation Inputs — gui-silent-crash-crash-visibility (Issue #46) — Cycle 2

- **Timestamp:** 2026-05-31T03-25
- **Source audits:**
  - `policy-audit.2026-05-31T03-25.md`
  - `code-review.2026-05-31T03-25.md`
  - `feature-audit.2026-05-31T03-25.md`
- **Prior cycle:** `remediation-inputs.2026-05-31T02-43.md` (R1-R4, all CLEARED)

## Cycle-1 Outcome Recap

R1 (app.py <= 500), R2 (`resolve_log_dir` rename in spec), R3 (faithful file-sizes evidence), and R4 (closure-pinning tests + 100% coverage on `_crash_handler.py`) are all CLEARED on their stated definitions of done. Cycle 1 introduced one new Blocking finding (F5) by way of the R4 fixture and test additions; cycle 2 must address it.

## Remediation-Required Findings

### R5 — Split `tests/gui/test_crash_handler.py` to restore the 500-line cap (Blocking)

- **Source:** Policy audit F5 / Code review Blocking finding / Feature audit AC-12 PARTIAL.
- **Current state:** `tests/gui/test_crash_handler.py` is 549 lines at HEAD `e17da56` (`wc -l` and `awk 'END{print NR}'` agree). The file is wholly new on this branch (`git diff --stat 0b353ad..HEAD -- tests/gui/test_crash_handler.py` -> `549 insertions(+)`). The cycle-0 head reported this file at 332 lines (per cycle-0 code-review file-size table); the R4 cycle-1 remediation added approximately 217 lines (a `_FakePath`/`_FakeFileHandle` fixture pair at lines 348-432, plus three new tests at lines 435-549).
- **Required action:** Split into two files. Recommended split:
  - `tests/gui/test_crash_handler.py` retains: AC-1..AC-4 / AC-7 installer-contract tests, the idempotency test, the `resolve_log_dir` parametric test, the Qt message-handler routing test. Approximate residual: 345 lines (well under cap).
  - `tests/gui/test_crash_handler_closures.py` (NEW): the `_FakePath` / `_FakeFileHandle` fixture pair (lines 348-432 of the current file) plus the three R4 closure-invocation tests:
    - `test_sys_excepthook_appends_traceback_record`
    - `test_threading_excepthook_appends_traceback_record`
    - `test_append_traceback_swallows_oserror`
  - Re-export shared imports (`crash_handler`, `pytest`, `cast`, `Callable`, `Path`, `Any`, `threading`, `logging`) at the top of the new file; the closure tests already access private symbols via `vars(crash_handler)["..."]` so no `# pyright: ignore` / `# noqa: B009` is needed.
- **Definition of done:**
  - `awk 'END{print NR}' tests/gui/test_crash_handler.py` returns `<= 500`.
  - `awk 'END{print NR}' tests/gui/test_crash_handler_closures.py` returns `<= 500`.
  - All four Python toolchain stages pass in a single pass.
  - `src/gui/_crash_handler.py` line and branch coverage remain at 100% / 100% (post-R4 state).
  - All 737 tests still pass (the three R4 tests should appear in the new file and run identically).
  - `evidence/qa-gates/phase8/file-sizes.md` is regenerated to include all four test files; rows for `test_crash_handler.py`, `test_crash_handler_closures.py`, `test_runners_threaded.py`, `test_pipeline_worker.py`, and `test_app_composition.py` should each show `PASS`.
- **Artifact paths:**
  - Code: `tests/gui/test_crash_handler.py` (modified — closures and fixtures removed), `tests/gui/test_crash_handler_closures.py` (NEW).
  - Evidence: regenerate `evidence/qa-gates/phase8/file-sizes.md` (extend table with test-file rows) and `evidence/qa-gates/phase8/pytest.md` (rerun, confirm 737 passed and coverage unchanged).
  - Spec checkbox: AC-12 stays `[x]` on its literal production-only scope; the cross-cutting `general-code-change.md` cap is the policy driver for this remediation.

## Non-Remediation Items (acknowledged, not blocking)

- Cycle-0 "Suggestion" items not addressed (top-level imports in `_crash_handler.py`, single-f-string concatenation, explicit `Qt.ConnectionType` on `thread.quit`, `@dataclass(frozen=True)` for `_State`): minor quality nits; optional.
- `tests/gui/test_app_composition.py` is at 480 lines (20-line headroom). Near the cap; consider this when adding further composition-root tests.
- `src/gui/_crash_handler.py` is at 495 lines (5-line headroom). Near the cap; any additional installer surface should land in a sibling module.

## Suggested Remediation Order

1. R5 — split `tests/gui/test_crash_handler.py` and regenerate phase-8 file-sizes / pytest evidence.

After R5 lands, the feature should be re-audited. No other Blocking or Material findings remain.

## Verification Commands for the Remediator

```
awk 'END{print NR}' tests/gui/test_crash_handler.py tests/gui/test_crash_handler_closures.py
wc -l tests/gui/test_crash_handler.py tests/gui/test_crash_handler_closures.py
poetry run black --check .
poetry run ruff check .
poetry run pyright
poetry run pytest --cov --cov-branch --cov-report=term-missing
git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..HEAD -- pyproject.toml poetry.lock
git diff HEAD -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'
```
