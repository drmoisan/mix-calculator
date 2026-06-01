# Code Review — gui-silent-crash-crash-visibility (Issue #46) — Reaudit Cycle 1

- **Timestamp:** 2026-05-31T03-25
- **Issue:** #46
- **Base:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Head:** `bug/gui-silent-crash-crash-visibility-46` @ `e17da56195d576de38faf47cfbfca2382ca702f1`
- **Prior review:** `code-review.2026-05-31T02-43.md` (Cycle 0)
- **Files reviewed:** 5 production (`src/gui/_crash_handler.py`, `src/gui/_crash_handler_bootstrap.py` [NEW in R1], `src/gui/app.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`) + 4 test files.

## Summary

The cycle-1 remediation cleared all four cycle-0 findings on their stated definition-of-done:

- R1: `src/gui/app.py` reduced from 503 to 499 lines via a clean extraction into `src/gui/_crash_handler_bootstrap.py` (94 lines, single `install_for_main()` public function with module-level anchor on the returned installation).
- R2: spec AC-1 verbatim text updated to `resolve_log_dir` (no leading underscore). No code change; the symbol-rename direction documented in plan P2-T2 stands.
- R3: `evidence/qa-gates/phase4/file-sizes.md` regenerated with `wc -l` / `awk NR` and bears an explicit correction note; `evidence/qa-gates/phase8/file-sizes.md` adds the post-R1 state.
- R4: three new tests (`test_sys_excepthook_appends_traceback_record`, `test_threading_excepthook_appends_traceback_record`, `test_append_traceback_swallows_oserror`) drive `_crash_handler.py` from 88% line / 100% branch to 100% / 100%. The tests use a `_FakePath`/`_FakeFileHandle` seam plus `vars(crash_handler)[name]` private-symbol access to avoid Pyright `reportPrivateUsage` and Ruff `B009` suppressions.

One new Blocking finding was introduced by the R4 change: `tests/gui/test_crash_handler.py` is now 549 lines, exceeding the 500-line cap that `general-code-change.md` applies to test code as well as production code. The remainder of the toolchain (black, ruff, pyright, pytest with coverage) passes in a single pass on phase-8 evidence.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocking | tests/gui/test_crash_handler.py | whole file (549 lines, +217 lines vs cycle 0) | File exceeds the 500-line cap after the R4 additions (cycle-0 332 -> cycle-1 549). The cap in `general-code-change.md` explicitly covers test code; no listed exception applies (this is not a raw text fixture for language-processing data). | Split into two files: keep AC-1..AC-4 / AC-7 installer-contract and `resolve_log_dir` tests in `test_crash_handler.py`; move the `_FakePath`/`_FakeFileHandle` fixture pair plus the three R4 closure-invocation tests into `tests/gui/test_crash_handler_closures.py`. Both files land under 500 lines. Re-run toolchain; coverage on `_crash_handler.py` must stay at 100%/100%. | `general-code-change.md` "No production code, test code, or reusable script file may exceed 500 lines." | `wc -l tests/gui/test_crash_handler.py` -> 549; `awk 'END{print NR}' tests/gui/test_crash_handler.py` -> 549 |
| Info | src/gui/_crash_handler_bootstrap.py | whole module | New helper module is well-factored: single public `install_for_main()` function, module-level `_installation` anchor with explanatory docstring, `__all__` declared, complete docstrings on the module and on the function. Ruff/black/pyright clean. | No change. | Confirms the R1 extraction follows the repository commenting and Python-design rules. | source review; `evidence/qa-gates/phase8/{black,ruff,pyright,pytest}.md` |
| Info | src/gui/app.py | composition root | The crash-handler call site is now `install_for_main()` (single import + single call); the `del _crash_installation` workaround line is removed. Net delta vs baseline: +6 lines and -1 statement of coverage denominator. | No change. | Preserves the AC-8 contract (single call before `QApplication`) with a smaller in-file footprint. | source review; `evidence/qa-gates/phase8/pytest.md` per-file table |
| Info | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md | AC-1 (line 202) and lines 103, 176, 180, 206 | Spec consistently uses `resolve_log_dir` (no leading underscore). `_resolve_log_dir` no longer appears in `spec.md` or in any source file. | No change. | Closes cycle-0 F2/AC-1 PARTIAL on the spec side; the audit trail (prior policy-audit, code-review, feature-audit, plan, evidence) intentionally retains the historical `_resolve_log_dir` references. | `grep -nE 'resolve_log_dir' spec.md` |
| Info | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md | full artifact | Phase-4 artifact regenerated with `wc -l` and `awk NR` (both verified), bears an explicit `Correction Note` identifying the prior `Measure-Object -Line` undercount, and now reports `src/gui/app.py = 503` at the pre-R1 state (matching the authoritative count). | No change. | Closes cycle-0 F3 PARTIAL; the artifact now matches the line-count method used to enforce the cap. | phase4 artifact body |
| Info | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md | full artifact | New phase-8 artifact records the post-R1 state and adds `_crash_handler_bootstrap.py` (94 lines). All five production files reported under cap. The artifact does NOT list test files; the F5 Blocking violation in `tests/gui/test_crash_handler.py` is therefore not captured in this evidence. | Extend the phase-8 file-sizes table to include the four test files modified or added on the branch; regenerate after the F5 split. | Evidence integrity: the file-sizes audit should cover any file the 500-line cap applies to, which includes test code. | phase8 artifact body |
| Info | tests/gui/test_crash_handler.py | lines 348-432 (`_FakePath` / `_FakeFileHandle` fixture) | The fixture is a faithful in-memory `Path.open()` stand-in: text-mode `write(str)` and the defensive bytes branch are both modeled. Each method has a docstring. No `tempfile`, no real I/O. | No change beyond the F5 split. | Matches `general-unit-test.md` "Creation and use of temporary files in tests is strictly prohibited" and the AAA structure rules. | source review |
| Info | tests/gui/test_crash_handler.py | lines 435, 473, 511 (R4 tests) | The three R4 tests reach into private module symbols via `vars(crash_handler)["_make_sys_excepthook"]` / `["_make_threading_excepthook"]` / `["_append_traceback"]`. This avoids Pyright `reportPrivateUsage` and Ruff `B009`, so no `# pyright: ignore` or `# noqa: B009` is needed. | No change. | This is the explicit pattern the cycle-0 F4 remediation called for; the agent-memory entry `pyright-ignore-authorization-scope` reinforces that `# pyright: ignore` is not pre-authorized in this repo. | source review; `evidence/qa-gates/phase7/suppression-diff.md` |
| Info | src/gui/_crash_handler.py | unchanged in this cycle | The four cycle-0 "Suggestion" items (top-level imports, single f-string, explicit `Qt.ConnectionType` on `thread.quit`, `@dataclass(frozen=True)` for `_State`) were not addressed in cycle 1. They were not blocking and remain low-value nits; the prior recommendation stands but is not re-raised here. | No change required. | Acknowledges that suggestions are not regressions. | cycle-0 code-review |

## Design Principles Review

- **Simplicity first:** `_crash_handler_bootstrap.py` is a single 94-line module with one public function and one explanatory docstring; it does not introduce indirection beyond the minimum required to clear the 500-line cap on `app.py`.
- **Reusability:** The bootstrap module could be reused by an alternative entry point (e.g., a Velopack first-run script); the public name is short and discoverable.
- **Extensibility:** No public-API change beyond the additive `install_for_main()`. `install_crash_handlers` keyword-only signature with `enable: bool = True` remains the extension point.
- **Separation of concerns:** Composition wiring (`install_for_main()`) is now distinct from the installer mechanics (`install_crash_handlers`) and from the GUI composition root (`main()` in `app.py`). Each layer has a single responsibility.

## Test Quality

- AAA structure followed in the three R4 tests; each test has a docstring stating the AC linkage and the seam in use.
- All waits remain event-driven (`qtbot.waitSignal`/`waitUntil`); no `time.sleep`/`QThread.sleep` introduced.
- No temporary-file usage; `_FakePath`/`_FakeFileHandle` model the file seam in-memory.
- Coverage on `_crash_handler.py` is now 100% line / 100% branch (was 88% / 100%).
- Pin tests added in cycle 0 (`test_pipeline_worker_run_reraises_keyboard_interrupt`, `test_pipeline_worker_run_reraises_system_exit`) remain correctly documented as baseline-passing pins.

## File-Size Compliance

| File | Lines (`awk NR`) | Under 500 | Notes |
|---|---|---|---|
| src/gui/_crash_handler.py | 495 | Yes (5 lines of headroom) | New; near cap |
| src/gui/_crash_handler_bootstrap.py | 94 | Yes | NEW in R1 |
| src/gui/runners.py | 270 | Yes | +114 vs baseline |
| src/gui/workers/pipeline_worker.py | 116 | Yes | +37 vs baseline |
| src/gui/app.py | 499 | Yes (1 line of headroom) | Post-R1 reduction (503 -> 499) |
| tests/gui/test_crash_handler.py | 549 | **No** (49 lines over) | NEW; R4 fixture + 3 tests pushed file over cap |
| tests/gui/test_runners_threaded.py | 151 | Yes | New |
| tests/gui/test_pipeline_worker.py | 244 | Yes | +99 vs baseline |
| tests/gui/test_app_composition.py | 480 | Yes (20 lines of headroom) | +79 vs baseline; near cap |

## Final Code-Review Verdict

**Changes Requested** — one Blocking finding remains (`tests/gui/test_crash_handler.py` at 549 lines violates the 500-line cap that applies to test code). All cycle-0 findings (F1-F4) are cleared. The structural design and the single-pass toolchain outcome are sound. A short cycle-2 should split `tests/gui/test_crash_handler.py` into two cohesive files.
