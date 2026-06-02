# Remediation Summary — Cycle 2 (Issue #48 / PR #49)

Timestamp: 2026-06-02T01-06

## Finding F1 (Blocking) — Status: RESOLVED

Defect: `src/gui/runners.py:ThreadedRunner` stored the active thread/worker/receiver
in single overwriteable attributes, never wired `thread.finished -> worker.deleteLater`,
never waited on worker threads, and had no application-shutdown cleanup. The worker
`QObject` (worker-thread affinity) was therefore destroyed by GUI-thread Python GC,
raising `QBasicTimer::stop: Failed. Possibly trying to stop from a different thread`.

Fix delivered:
- `thread.finished.connect(worker.deleteLater)` and `thread.finished.connect(thread.deleteLater)`
  so the worker and thread are destroyed on the worker thread.
- Single-attribute storage replaced with a `set[_ActiveDispatch]` of live dispatch
  records; each record is added before `thread.start()` and removed on `thread.finished`,
  so a second dispatch cannot drop a still-running prior thread.
- New public `ThreadedRunner.await_active(timeout_ms=5000)` quits and waits every live
  worker thread at shutdown (with a defensive guard for the deleteLater/await race).
- New sibling module `src/gui/_shutdown_wiring.py` connects `QApplication.aboutToQuit`
  to `runner.await_active()`; wired from `app.py` with one import + one call. `app.py`
  remains at the 500-line cap.
- The existing queued-connection `_RunnerReceiver` pattern (AC-6) is unchanged; no
  direct cross-thread outcome delivery was reintroduced.

## R-AC-7 — Status: PASS

R-AC-7: `ThreadedRunner` performs no cross-thread `QObject` destruction.

| Part | Statement | Verifying evidence |
|---|---|---|
| (a) | Worker `deleteLater` on `thread.finished` | `tests/gui/test_runners_threaded_lifecycle.py::test_worker_deletelater_wired_to_thread_finished` (P3-T2) |
| (b) | Second dispatch does not drop a running prior thread | `::test_second_dispatch_does_not_drop_running_prior_thread` (P3-T3) |
| (c) | Shutdown quits + waits active threads | `::test_await_active_quits_and_waits_then_no_running_thread` (P3-T4); `tests/gui/test_shutdown_wiring.py::test_about_to_quit_calls_await_active` and `::test_wire_shutdown_cleanup_noop_for_runner_without_await_active` (P3-T6) |
| (d) | Existing queued GUI-thread delivery preserved | `::test_queued_outcome_still_delivers_on_gui_thread` (P3-T5) |

Full-suite confirmation (P4-T4): 818 passed, 0 failed; `src/gui/runners.py` 100% line/100% branch;
`src/gui/_shutdown_wiring.py` 100% line/100% branch. Coverage delta:
`evidence/qa-gates/coverage-delta.2026-06-02T01-06.md` (no regression on changed lines;
TOTAL line 99.48%, branch 96.63%).

Prior acceptance criteria AC-1..AC-15 and cycle-1 R-AC-1..R-AC-6 remain `- [x]` with no
regression (verified at P4-T4 / P4-T7).

## F2 (Major) — Status: DEFERRED (out of scope this cycle)

`SourceSelectionPresenter.on_schema_discovery` has no production caller. Per the
Scope-change Rule, F2 was NOT fixed in this cycle; no task wired `on_schema_discovery`.
It is recommended as a separate follow-up cycle and must be raised to the user.

## Pointers
- Coverage delta: `evidence/qa-gates/coverage-delta.2026-06-02T01-06.md`
- Final QA gates: `evidence/qa-gates/black-final`, `ruff-final`, `pyright-final`, `pytest-final` (.2026-06-02T01-06.md)
- File-size verification: `evidence/qa-gates/final-file-sizes.2026-06-02T01-06.md`, `evidence/qa-gates/app-py-size-postchange.2026-06-02T01-06.md`
