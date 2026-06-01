# Code Review — gui-silent-crash-crash-visibility (Issue #46) — Reaudit Cycle 2

- **Timestamp:** 2026-05-31T03-52
- **Issue:** #46
- **Base:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Head:** `bug/gui-silent-crash-crash-visibility-46` @ `b59bb3660ce9fa510a450d326f92ffd46a1776aa`
- **Prior reviews:** `code-review.2026-05-31T02-43.md` (Cycle 0), `code-review.2026-05-31T03-25.md` (Cycle 1)
- **Files reviewed:** 5 production (`src/gui/_crash_handler.py`, `src/gui/_crash_handler_bootstrap.py`, `src/gui/app.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`) + 5 test files (`tests/gui/test_crash_handler.py`, `tests/gui/test_crash_handler_closures.py` [NEW in R5], `tests/gui/test_app_composition.py`, `tests/gui/test_pipeline_worker.py`, `tests/gui/test_runners_threaded.py`).

## Executive Summary

The cycle-2 remediation (R5) cleared the sole Blocking finding from cycle 1. `tests/gui/test_crash_handler.py` is now 332 lines (was 549), and the `_FakePath`/`_FakeHandle` fixture pair plus the three R4 closure-invocation tests live in a new sibling at `tests/gui/test_crash_handler_closures.py` (258 lines). Both files are well under the 500-line cap. The relocation is behaviorally invariant: the relocated tests still access private symbols via `vars(crash_handler)[name]`, still use the in-memory `BytesIO` sink, and continue to assert the cycle-1 contract. The full test suite still reports 737 passed; `src/gui/_crash_handler.py` coverage stays at 100% line / 100% branch; the four-stage Python toolchain (black, ruff, pyright, pytest) passes in a single pass. No new suppression markers were added across the entire branch diff.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | tests/gui/test_crash_handler_closures.py | whole file (258 lines, NEW in R5) | New sibling test file holds the relocated `_FakePath`/`_FakeHandle` fixture pair (classes at lines 55, 97) and the three R4 closure tests (`test_sys_excepthook_appends_traceback_record` line 144; `test_threading_excepthook_appends_traceback_record` line 182; `test_append_traceback_swallows_oserror` line 220). Imports are organized with `pytest` and `pathlib.Path` correctly placed inside a `TYPE_CHECKING` block to satisfy ruff TC002/TC003. Module docstring documents purpose, responsibilities, and the no-temp-files determinism note. | No change. | The split exactly follows the cycle-2 remediation-inputs design (R5). The relocated tests use the same `vars(crash_handler)[name]` private-symbol access that avoids `# pyright: ignore` and `# noqa: B009`. | `wc -l tests/gui/test_crash_handler_closures.py` -> 258; `grep -nE "^class _Fake\|^def test_" tests/gui/test_crash_handler_closures.py` |
| Info | tests/gui/test_crash_handler.py | whole file (332 lines, post-R5) | Original file trimmed to retain installer-contract, idempotency, `resolve_log_dir` parametric, Qt message-handler routing, and the public-surface assertion. The `_Fake*` classes and the three R4 tests are gone; imports were pruned (the file still uses `logging`, `threading`, `BytesIO`, `Any`, etc. for the retained `test_install_crash_handlers_installs_all_four_hooks` and routing tests). | No change. | The retained tests cover AC-1..AC-4 and AC-7. The split preserved the relevant fixtures and seam patterns. | `wc -l tests/gui/test_crash_handler.py` -> 332; `grep -nE "^def test_\|^class _" tests/gui/test_crash_handler.py` shows zero `_Fake*` classes and the four retained `test_*` functions |
| Info | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/file-sizes.md | full artifact | Regenerated for cycle 2: the post-fix table now lists all five production files plus all five test files (the bootstrap module and the new closures file are both present). Every row shows `PASS` under the 500-line cap. The Notes section cites `.claude/rules/general-code-change.md`, the R5 driver, and back-references the cycle-1 corrected phase-4 artifact. | No change. | Closes the evidence-coverage gap cycle 1 noted: the file-sizes audit now includes test files within scope of the cross-cutting cap. | phase8 artifact body |
| Info | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase8/pytest.md | full artifact | Regenerated for cycle 2: headline `737 passed`, total line coverage 99% (3636/3656), branch ~96.5% (637/660). Per-file: `_crash_handler.py` 100%/100%, `_crash_handler_bootstrap.py` 100%, `runners.py` 100%/100%, `pipeline_worker.py` 100%/100%, `app.py` 99%/92%. Notes confirm that the three relocated tests are now collected from `tests/gui/test_crash_handler_closures.py` and the total suite count is unchanged versus the cycle-1 post-state. | No change. | The R5 split is behaviorally invariant; the post-state matches the cycle-1 coverage profile exactly. | phase8 artifact body; cross-check `evidence/qa-gates/phase6/pytest-cross-check.md` |
| Info | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/single-pass-summary.md | full artifact | Records `Single-Pass Result: PASS` with EXIT_CODE 0 from each of black/ruff/pyright/pytest in the same loop iteration. Documents one intermediate ruff failure (TC002/TC003) caused by `pytest` and `pathlib.Path` being imported at runtime in the new closures file; the fix moved those into the `TYPE_CHECKING` block and restarted the loop. | No change. | Demonstrates the executor handled an intermediate failure correctly per the repository toolchain-loop rule (restart from format on any stage change). | phase4 summary body |
| Info | src/gui/_crash_handler.py | unchanged in cycle 2 | The four cycle-0 "Suggestion" items (top-level imports, single f-string, explicit `Qt.ConnectionType` on `thread.quit`, `@dataclass(frozen=True)` for `_State`) remain unchanged. They were not blocking in cycle 0 or cycle 1; raising them again here would be churn. | No change required. | Acknowledges that suggestions are not regressions and the spec does not require them. | cycle-0 code-review |
| Info | tests/gui/test_app_composition.py | whole file (480 lines, unchanged in cycle 2) | The file remains 20 lines from the cap. R5 did not modify it. The cycle-1 review flagged it as near-cap; consider this when adding further composition-root tests. | If a future change adds more than 20 lines to this file, plan a split mirroring the R5 pattern. | Avoids re-triggering an over-cap finding in a future cycle. | `wc -l tests/gui/test_app_composition.py` -> 480 |
| Info | tests/gui/test_crash_handler_closures.py | imports block (lines 28-41) | Imports correctly distinguish runtime vs type-only usage: `logging`, `threading`, `BytesIO`, `TYPE_CHECKING`, `Any`, `cast`, and `crash_handler` are runtime imports; `Callable`, `Path`, and `pytest` live inside `if TYPE_CHECKING:`. This is the fix recorded in `evidence/qa-gates/phase4/single-pass-summary.md` for the intermediate ruff TC002/TC003 failure. | No change. | Confirms that the cycle-2 executor resolved the ruff finding by restructuring imports (per `python-suppressions.md` workaround) rather than by adding a `# noqa` marker. | source review at lines 28-41 |

## Implementation Audit

### Design Principles Review

- **Simplicity first:** The split moves only the fixture pair and the three closure tests into a sibling file. No abstraction, no helper module, no test-helper module is introduced; the duck-typed `_FakePath`/`_FakeHandle` classes travel with the tests that use them.
- **Reusability:** Not applicable in this cycle — the relocation does not change any shared seam.
- **Extensibility:** The original module structure of `_crash_handler.py` and `_crash_handler_bootstrap.py` is unchanged; the public installer surface (`install_crash_handlers`, `install_for_main`, `CrashHandlerInstallation`, `resolve_log_dir`) is unchanged.
- **Separation of concerns:** The split improves test-file separation of concerns. `test_crash_handler.py` is now focused on the installer-contract surface (AC-1..AC-4 / AC-7); `test_crash_handler_closures.py` is focused on direct invocation of the private crash-write closures. Each file's docstring states this focus.

## Test Quality Audit

- AAA structure preserved in all three relocated tests (visible at lines 144-180, 182-218, 220-258 of `test_crash_handler_closures.py`).
- Determinism: `_FakePath`/`_FakeHandle` continue to use `BytesIO` as the sink; no `tempfile` usage; no real I/O.
- Private-symbol access continues to use `vars(crash_handler)["_make_sys_excepthook"]` / `["_make_threading_excepthook"]` / `["_append_traceback"]`, preserving the cycle-1 pattern that avoids `# pyright: ignore` and `# noqa: B009`.
- Coverage: `src/gui/_crash_handler.py` 100% line / 100% branch (verified against `artifacts/python/lcov.info`: LF=99 LH=99 BRF=8 BRH=8). No regression versus cycle-1.
- Test count invariant: `13 = 10 (test_crash_handler.py) + 3 (test_crash_handler_closures.py)`; total suite remains at 737.

## Security / Correctness Checks

- No security-impacting code surface was touched in cycle 2. The R5 split is a pure relocation of two duck-typed test fixtures and three private-symbol-access tests; no production code, no auth code, no I/O boundary, no input handling, no logging code was modified.
- Correctness invariants verified by phase-4 pytest evidence: 737/737 tests passing; `_crash_handler.py` 100% line / 100% branch (matching the cycle-1 post-state); the three relocated tests still pin the on-disk traceback write path (`_make_sys_excepthook`, `_make_threading_excepthook`, `_append_traceback`) with identical assertions and the same `BytesIO` sink.
- No new third-party dependencies (verified by empty diff on `pyproject.toml` and `poetry.lock`).
- No new suppression markers (`# noqa`, `# type: ignore`, `# pyright: ignore`) anywhere in the branch diff (verified by `git diff 0b353ad..b59bb36 -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'` returning EXIT_CODE 1, no matches).

## Research Log

- Cycle-2 caller prompt verbatim recorded; no scope narrowing attempted by the caller. Full feature-vs-base scope applied.
- Cross-checked R5 definition-of-done against `remediation-inputs.2026-05-31T03-25.md` lines 27-37; each item verified independently by line counts, grep, and pytest evidence.
- Cross-checked `artifacts/python/lcov.info` SF records for the four changed production files plus the two new modules to confirm coverage matches what `evidence/qa-gates/phase8/pytest.md` reports.

## File-Size Compliance

| File | Lines (`awk NR`) | Under 500 | Notes |
|---|---|---|---|
| src/gui/_crash_handler.py | 495 | Yes (5 lines of headroom) | Near cap; unchanged |
| src/gui/_crash_handler_bootstrap.py | 94 | Yes | Unchanged |
| src/gui/runners.py | 270 | Yes | Unchanged |
| src/gui/workers/pipeline_worker.py | 116 | Yes | Unchanged |
| src/gui/app.py | 499 | Yes (1 line of headroom) | Unchanged |
| tests/gui/test_crash_handler.py | 332 | Yes (168 lines of headroom) | Post-R5 split |
| tests/gui/test_crash_handler_closures.py | 258 | Yes (242 lines of headroom) | NEW in R5 |
| tests/gui/test_runners_threaded.py | 151 | Yes | Unchanged |
| tests/gui/test_pipeline_worker.py | 244 | Yes | Unchanged |
| tests/gui/test_app_composition.py | 480 | Yes (20 lines of headroom) | Near cap; unchanged |

All ten files under the 500-line cap. The R5 split also reduced `test_crash_handler.py` headroom to 168 lines, eliminating its over-cap state without disturbing the adjacent test files.

## Cycle-2 Diff Summary

- Cycle-2 commit `b59bb36` adds `tests/gui/test_crash_handler_closures.py` (+258 / -0) and trims `tests/gui/test_crash_handler.py` (332 lines after the split; net -217 lines from the cycle-1 head). No other source files were modified.
- Evidence artifacts updated in cycle 2: phase 8 `file-sizes.md` and `pytest.md` regenerated in place; phase 4 single-pass summary added; phase 1/2/3/5/6/7 artifacts added under the cycle-2 plan.

## Verdict

**Approved** — zero Blocking and zero Material findings. The cycle-2 R5 split closes the only outstanding finding from cycle 1, preserves the cycle-1 coverage profile (100%/100% on `_crash_handler.py`), preserves the suite size (737 passed), and introduces no new suppression markers. The structural fix for issue #46 (crash visibility + cross-thread Qt mutation) remains delivered and verified. The branch is ready to merge from a code-review perspective.
