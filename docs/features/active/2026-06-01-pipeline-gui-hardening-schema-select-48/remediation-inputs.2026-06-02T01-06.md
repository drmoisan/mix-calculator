# Remediation Inputs — Issue #48, Cycle 2

- Entry timestamp: 2026-06-02T01-06
- Branch: `feature/pipeline-gui-hardening-schema-select-48`
- Predecessor: Cycle 1 (2026-06-01T23-31 → 23-52) complete; committed locally at `a07bce4` (not pushed). PR #49 open.
- Canonical issue number: 48.

## Trigger

A functional crash surfaced when running the in-flight feature (`poetry run
mix-pipeline-gui`) after cycle 1. Observed terminal output:

```
VelopackApp: Error loading manager/locator: NotInstalled(...)   # benign
WARNING:src.gui._crash_handler.qt:Qt: QBasicTimer::stop: Failed. Possibly trying to stop from a different thread
   (repeated 5x)
```

The `QBasicTimer::stop: Failed. Possibly trying to stop from a different thread`
warning is a Qt cross-thread object-lifecycle violation. It is the same defect
class issue #46 addressed for widget mutation, but here it originates from the
worker-thread teardown, not from outcome delivery.

## Root-cause analysis (Blocking)

**Finding F1 (Severity: Blocking) — `ThreadedRunner` QThread/worker lifecycle is
incomplete; worker `QObject`s are destroyed cross-thread.**

Evidence in `src/gui/runners.py:ThreadedRunner` (lines ~156-224):

- `run()` connects `worker.finished`/`worker.error` to the GUI-thread
  `_RunnerReceiver` via `QueuedConnection` (correct, from #46 — keep this) and
  connects `worker.finished`/`worker.error` to `thread.quit` (runners.py:216-217).
- It does **not** connect `thread.finished` to `worker.deleteLater`, nor to
  `thread.deleteLater`, and never calls `thread.wait()`. `grep` over `src/gui`
  confirms there is no `deleteLater`, no `.wait(`, and no `aboutToQuit` /
  `closeEvent` thread cleanup anywhere.
- The runner stores the active thread/worker/receiver in **single overwriteable
  attributes** `_thread`/`_worker`/`_receiver` (runners.py:160-162, 221-223).
  This same `ThreadedRunner` instance is shared by both `wire_import_dispatch`
  and `wire_run` (`app.py:181-182`). Each new dispatch overwrites the prior
  attributes.

Consequence: a `PipelineWorker` is a `QObject` whose thread affinity is the
worker `QThread` (`worker.moveToThread(thread)`, runners.py:198). Because it is
never `deleteLater()`-ed on its own thread, its last Python reference is dropped
either (a) when the next dispatch overwrites `_worker`/`_thread`/`_receiver`, or
(b) when the application exits and the `ThreadedRunner` is garbage-collected.
Python then destroys the worker (and the `QThread`) from the **GUI thread** while
the worker's affinity is the (finished) worker thread. Destroying a timer-owning
`QObject` from a foreign thread raises precisely `QBasicTimer::stop: Failed.
Possibly trying to stop from a different thread`. The single-attribute design can
also drop a still-running thread's references on a second dispatch ("QThread:
Destroyed while thread is still running"). The five repetitions are consistent
with multiple dispatches (e.g. per-tab imports and/or a run) and/or app-exit
teardown.

This was latent before cycle 1: the empty-schema-dropdown defect (cycle 1) likely
blocked the user from reaching the threaded import/run path; with that fixed, the
threaded path is now exercised and the lifecycle defect manifests.

## Required fix (shape, not prescription)

Correct the `QThread` lifecycle in `src/gui/runners.py:ThreadedRunner` while
preserving the existing queued-connection `_RunnerReceiver` pattern (do not
reintroduce direct cross-thread outcome delivery):

1. Destroy the worker on its own thread: `thread.finished.connect(worker.deleteLater)`.
2. Manage the `QThread` object lifetime so it is not garbage-collected while
   running and is itself cleaned up after `finished` (e.g. `thread.deleteLater`
   and/or an explicit `wait()`), and so a second dispatch does not drop a
   still-running prior thread — track active dispatches in a collection rather
   than single overwriteable attributes, removing each entry on `thread.finished`.
3. Add an application-shutdown hook (e.g. `QApplication.aboutToQuit` or the main
   window `closeEvent`) that quits and `wait()`s any active worker threads so no
   thread is destroyed while running at exit.

## Regression test (required)

Add a deterministic test for the `ThreadedRunner` threading path (pytest-qt
`qtbot`, offscreen Qt) that:

- drives a real `QThread` dispatch to completion and asserts the worker is
  scheduled for destruction on its own thread (`deleteLater` wired to
  `thread.finished`), and that the thread is finished/cleaned up;
- exercises a second dispatch and app-shutdown teardown without leaving a running
  thread (no "destroyed while running");
- preserves the existing queued-outcome behavior (success/error callbacks still
  fire on the GUI thread).

The existing `SynchronousRunner` test seam does not cover the `QThread` lifecycle;
this regression must target `ThreadedRunner` specifically.

## Constraints

- Toolchain per task: Black → Ruff → Pyright → Pytest (`env -u VIRTUAL_ENV`
  prefix), zero-regression, coverage ≥85% line / ≥75% branch.
- Hard 500-line cap. `src/gui/runners.py` is ~271 lines (ample headroom);
  `src/gui/app.py` is at the cap (500) — any shutdown-hook wiring added to
  `app.py` must be extracted to a sibling `_*.py` module to stay ≤500.
- Tiers: `runners.py` and `pipeline_worker.py` are T3 (Adapters & UI).
- No new third-party dependencies (PySide6, pytest-qt already present).
- Suppressions only per the pre-authorized patterns in `.claude/rules/python-suppressions.md`.

## Out of scope for this cycle (separate finding, do NOT fix here)

**F2 (Severity: Major, deferred) — `SourceSelectionPresenter.on_schema_discovery`
has no production caller.** No widget signal is connected to it (`grep` confirms
no `.connect(...on_schema_discovery)` in `src/`), so the WS2 auto-select-on-tab
behavior (AC-11/AC-12) does not run in production despite passing unit tests. This
is the same "tested but unwired" failure mode recorded in orchestrator memory
(`audit-verify-production-call-site`). Per the Scope-change Rule it belongs to a
separate cycle; it is recorded here for traceability and must be raised to the
user as a recommended follow-up, not bundled into the crash fix.
