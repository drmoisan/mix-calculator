# Code Review: Pipeline GUI Hardening and Schema Selection — #48 (cycle-2 re-audit)

**Review Date:** 2026-06-02
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
**Feature Folder Selection Rule:** Suffix `-48` matches the canonical issue number for this branch.
**Base Branch:** `main` (merge-base `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`)
**Head Branch:** `feature/pipeline-gui-hardening-schema-select-48` (head `176289e`)
**Review Type:** Post-remediation re-review (cycle 2)

---

## Executive Summary

This re-review covers the full feature-vs-base diff, with focus on the cycle-2 delta (commit `176289e`) that resolves Blocking finding F1 from `remediation-inputs.2026-06-02T01-06.md`: the `ThreadedRunner` cross-thread `QObject` lifecycle defect that emitted `QBasicTimer::stop: Failed. Possibly trying to stop from a different thread`. The full branch also includes cycle-1 work (commits `c526e4f`, `a07bce4`) delivering AC-1..AC-15 and R-AC-1..R-AC-6.

**What changed:**
Cycle 2 reworks `src/gui/runners.py`: dispatch state moves from single overwriteable attributes (`_thread`/`_worker`/`_receiver`) to a `set[_ActiveDispatch]` of identity-hashed records; `thread.finished` is wired to `worker.deleteLater` and `thread.deleteLater` so the worker `QObject` is destroyed on its own thread; a new `await_active(timeout_ms)` quits and waits every live thread; and a read seam `active_dispatches()` is exposed for tests. A new sibling module `src/gui/_shutdown_wiring.py` connects `QApplication.aboutToQuit` to `runner.await_active()`, wired once in `app.py` (line 432). The queued `_RunnerReceiver` delivery (AC-6) is unchanged. Seven tests were added (811 → 818). The cycle-1 implementation across `pipeline_service.py`, `_main_window_view.py`, `_load_aop_helpers.py`, `source_input_widget.py`, presenters, protocols, and the schema/key-mismatch modules was re-verified as still green.

**Top 3 risks:**
1. `SourceSelectionPresenter.on_schema_discovery` has no production caller (deferred finding F2), so the WS2 auto-select-on-tab behavior (AC-11/AC-12) is exercised only by unit tests, not in production. This is out of scope for cycle 2 and recorded for a follow-up cycle.
2. The `# pragma: no cover` guard in `await_active` covers a real shutdown race that cannot be deterministically tested; an incorrect future edit inside that branch would not be caught by coverage. Mitigated by the bounded single-line scope and inline rationale.
3. `app.py` is at the 500-line cap exactly; any further composition-root addition will require extraction first (already the established pattern here).

**PR readiness recommendation:** **Go** — The cycle-2 crash fix is correct, complete against R-AC-7 (a-d), fully covered, and clean across the toolchain. No Blocker or Major findings. The one deferred item (F2) does not affect the crash fix and is tracked separately.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/presenters/source_selection_presenter.py` | `on_schema_discovery` (line 182) | No production signal connects to `on_schema_discovery`; WS2 auto-select runs only under unit tests (deferred finding F2). | Track as a separate follow-up cycle to wire a widget signal to the handler; do not bundle into the crash fix. | "Tested but unwired" means AC-11/AC-12 auto-select does not run in production despite passing tests. | `grep -rn "connect(" src/ \| grep schema_discovery` → `NO_PRODUCTION_CALLER_CONFIRMED`; recorded in `remediation-inputs.2026-06-02T01-06.md` F2. |
| Info | `src/gui/runners.py` | `await_active`, line 343 | `# pragma: no cover` on the defensive `except RuntimeError` shutdown-race guard. | Keep as-is. | The branch guards a real deleteLater/await_active race but can only be forced by deleting a live C++ QThread (interpreter abort), so it is not deterministically testable. | runners.py:340-352; `evidence/qa-gates/coverage-delta.2026-06-02T01-06.md`. |
| Info | `src/gui/app.py` | whole file | File is exactly at the 500-line cap. | Continue the sibling-module extraction pattern for any future additions. | At the cap, any direct addition would violate `general-code-change.md`; cycle 2 correctly added only one import + one call. | `awk 'END{print NR}' src/gui/app.py` → 500; `evidence/qa-gates/app-py-size-postchange.2026-06-02T01-06.md`. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The lifecycle fix matches the required-fix shape precisely and idiomatically. Replacing single overwriteable attributes with a `set[_ActiveDispatch]` directly removes the "second dispatch drops a still-running prior thread" failure mode, and registering the record before `thread.start()` closes the fast-worker race where a worker could finish before its record is tracked.
- Destroying the worker via `thread.finished -> worker.deleteLater` (plus `thread.deleteLater`) is the correct Qt idiom for cross-thread object teardown; it schedules destruction on the worker thread's event loop, which is the precise fix for the `QBasicTimer::stop` abort.
- `await_active` iterates a snapshot (`list(self._active)`) so finished-time record removal from the `thread.finished` handler cannot mutate the set under the loop — a subtle correctness point handled correctly.
- The shutdown wiring lives in its own `_shutdown_wiring.py` module following the `_run_wiring.py`/`_schema_list_wiring.py` precedent, keeping `app.py` at the cap with only one import and one call. The `getattr`-based degradation means `SynchronousRunner` (the test seam, no threads) is a safe no-op rather than an `AttributeError` at shutdown.
- The queued `_RunnerReceiver` delivery (AC-6) is genuinely preserved; the connection types remain `Qt.ConnectionType.QueuedConnection` and `test_queued_outcome_still_delivers_on_gui_thread` asserts both success and error callbacks run on the GUI thread after the refactor.

#### Typing and API notes

- All new surfaces are fully annotated: `await_active(self, timeout_ms: int = 5000) -> None`, `active_dispatches(self) -> tuple[_ActiveDispatch, ...]`, `wire_shutdown_cleanup(app: QApplication, runner: RunnerProtocol) -> None`. No `Any`. Pyright reports 0 errors/0 warnings.
- `_ActiveDispatch` is a `@dataclass(eq=False)` so each record is identity-hashed, which is what allows many concurrent dispatches to coexist in a `set` without value collisions — a correct and well-documented choice.
- `_shutdown_wiring.py` keeps Qt and runner imports under `TYPE_CHECKING`, avoiding a runtime import cycle while preserving annotations.

#### Error handling and logging

- The only new exception handler is the bounded `except RuntimeError` shutdown-race guard, which is a defined Qt object-lifetime boundary, not a broad catch-all. It discards the affected record and continues, leaving teardown robust. This is consistent with the repo's fail-fast/bounded-boundary policy.
- No `print` statements added; no broadened `except Exception` introduced in the cycle-2 delta.

---

## Test Quality Audit

The cycle-2 tests are deterministic, isolated, and target the four R-AC-7 sub-properties plus a repeated-drain edge case. They use a real `QThread` (in-process, offscreen) rather than mocking Qt, which is appropriate because the defect is specifically a Qt object-lifetime/thread-affinity bug that a mock would not expose. Synchronization uses `threading.Event` gates and `qtbot.waitSignal`/`waitUntil` — no sleeps, no temp files.

### Reviewed test and QA artifacts

- `tests/gui/test_runners_threaded_lifecycle.py` — five tests proving deleteLater wiring (worker.destroyed fires), two concurrent records (no overwrite), quit+wait teardown leaves no running thread, GUI-thread queued delivery, and clean repeated drains. Non-vacuous assertions verified by reading the file.
- `tests/gui/test_shutdown_wiring.py` — proves `aboutToQuit` invokes `await_active` exactly once and degrades to a no-op for a runner without `await_active`.
- `tests/gui/test_runners_threaded.py` — updated to join worker threads via the public `await_active` seam instead of reaching for the removed `_thread` attribute; existing AC-6 assertions preserved.
- `evidence/qa-gates/pytest-final.2026-06-02T01-06.md` / `coverage-delta.2026-06-02T01-06.md` — record 818 passed, runners.py 100%/100%, _shutdown_wiring.py 100%/100%, no regression. Independently re-verified this audit.

### Quality assessment prompts

- **Determinism:** Offscreen Qt forced in `conftest.py`; gates are events, not wall-clock; signals awaited via qtbot. No flaky timing.
- **Isolation:** Each test builds a fresh `ThreadedRunner` and drains it; no shared state.
- **Speed:** Runner/shutdown subset ran 26 tests in 1.56s; full suite 23.30s.
- **Diagnostics:** Assertions report concrete values (record counts, `isRunning()` booleans, thread identity), so a regression would localize cleanly.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff inspection; no credentials or workbook figures in the cycle-2 delta. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess in the cycle-2 delta; `build_exe.py` change (cycle 1) adds the console-disable flag only. |
| Input validation at boundaries | ✅ PASS | `await_active` validates nothing user-facing; dispatch registration precedes start. WS3 `can_run()` gate and WS5 identity validation are the boundary checks (cycle 1, re-verified green). |
| Error handling remains explicit | ✅ PASS | The single new `except RuntimeError` is a defined Qt-lifetime boundary; no broadened catch-all. |
| Configuration / path handling is safe | ✅ PASS | No new path or config handling in the cycle-2 delta. |

---

## Research Log

No external research was required. All findings are grounded in diff inspection, the four-stage Python toolchain re-run, coverage re-measurement, and the feature-folder evidence artifacts.

---

## Verdict

The cycle-2 change is ready for normal PR flow. It correctly and completely resolves the cross-thread `QObject` lifecycle crash (Blocking F1) and satisfies R-AC-7 (a-d) with deterministic, well-targeted tests at full coverage. The toolchain passes in a single pass, all touched files are within the 500-line cap, and no unauthorized suppressions were introduced. The two Info-level observations (deferred F2 unwired handler; the bounded `# pragma: no cover` shutdown-race guard) do not affect correctness of the crash fix and do not block merge. This conclusion matches the Findings Table and the Go recommendation above.
