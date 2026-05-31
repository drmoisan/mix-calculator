# Code Review — gui-silent-crash-crash-visibility (Issue #46)

- **Timestamp:** 2026-05-31T02-43
- **Issue:** #46
- **Base:** main @ `0b353adcd596ff450db5cfa7ca771ef22565e53a`
- **Head:** `bug/gui-silent-crash-crash-visibility-46` @ `666e84a32aa158a4554cb0305c5695512e35f0cd`
- **Files reviewed:** 4 production (`src/gui/_crash_handler.py` [NEW], `src/gui/app.py`, `src/gui/runners.py`, `src/gui/workers/pipeline_worker.py`) + 4 test files.

## Summary

The structural fix is well-factored: a new self-contained crash-handler module owns the four crash hooks; the threaded runner introduces a GUI-thread receiver with queued connections; the worker boundary widens to `BaseException` with explicit re-raise of interpreter-level signals; the composition root installs the handlers before constructing any Qt object. Code is Pyright-clean, ruff-clean, black-formatted, with no new suppressions. Docstrings are present and follow the repository's commenting policy. The implementation is generally faithful to the spec, with one symbol-rename drift and one file-size regression.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Blocking | src/gui/app.py | whole file (503 lines) | File exceeds the 500-line cap after this change (baseline 493 -> head 503). | Extract the crash-handler bootstrap call (and optionally one of the closures inside `wire_control_signals`) into a sibling module so app.py returns under 500 lines. | `general-code-change.md` "No production code... may exceed 500 lines." | `awk 'END{print NR}' src/gui/app.py` -> 503 |
| Material | src/gui/_crash_handler.py | line 126 (definition) | Public symbol `resolve_log_dir` does not match spec AC-1 wording (`_resolve_log_dir`). | Update spec AC-1 to the new name, since the rename is the cleaner approach (private-via-underscore would force `# pyright: ignore[reportPrivateUsage]` in tests). | Spec/code naming should be consistent; readers comparing AC-1 to the implementation will be misled. | spec.md line 202 vs `_crash_handler.py` line 126 |
| Material | src/gui/_crash_handler.py | lines 254-263, 290-303, 374-383 | Inner closures returned by `_make_sys_excepthook` / `_make_threading_excepthook` and the `_append_traceback` helper are never invoked by tests; only the recorded contract (hook names) is asserted. | Add three tests that invoke each closure with a patched `_append_traceback` (or with `crash_log_path` redirected to a `BytesIO` via a wrapped `Path.open`) so the formatting branch and the OSError catch are pinned. | AC-5 / AC-7 behavioral contract relies on these closures running correctly; missing tests leave the crash-write path unverified. | `evidence/qa-gates/phase7/pytest.md` per-file missing-lines |
| Material | docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md | whole artifact | Reported counts disagree with `awk NR` / `wc -l` (PowerShell `Measure-Object -Line` undercount); the artifact reports app.py = 439 when the actual count is 503. | Regenerate using `(Get-Content <path>).Count` or `wc -l`; the artifact should reflect the same line-count method tools use to enforce the cap. | Evidence integrity: the artifact concealed the F1 cap violation. | Phase4 evidence vs `awk NR` output |
| Suggestion | src/gui/_crash_handler.py | line 438 | `import os` and `import platform as platform_module` are performed inside `install_crash_handlers` (function-local) rather than at module top. | Hoist both imports to the module top; they have no side effects and are unconditionally required when the installer is enabled. The current local import increases the function body line count and complicates static analysis of imports. | Repo Python style prefers top-level imports; function-local imports are reserved for breaking circular dependencies (not the case here). | source review |
| Suggestion | src/gui/_crash_handler.py | line 376 | F-string concatenation joins two adjacent string literals with a stray empty pair: `f"--- {timestamp} {source} thread={thread_name} ---\n" f"{formatted}\n"`. | Inline as a single f-string for readability: `f"--- {timestamp} {source} thread={thread_name} ---\n{formatted}\n"`. | The implicit-concat form is correct but unconventional; black does not auto-merge it. Minor readability nit. | source review |
| Suggestion | src/gui/runners.py | lines 207-217 | `worker.finished.connect(thread.quit)` and `worker.error.connect(thread.quit)` use the default (auto) connection type rather than an explicit `Qt.ConnectionType.QueuedConnection` or `Qt.ConnectionType.DirectConnection`. | Pass an explicit connection type — `Qt.ConnectionType.QueuedConnection` is appropriate here too because `thread.quit` is documented thread-safe but explicit-is-better-than-implicit matches the surrounding code style (AC-6 makes the queued-connection pattern explicit for the receiver dispatch). | The existing comment ("QThread.quit is thread-safe") justifies the default but invites a future regression where someone removes the comment and the behavior changes silently. | source review |
| Suggestion | src/gui/_crash_handler.py | _State (line 100-120) | The `_State` instance is a mutable dataclass even though no field is reassigned after construction; safer as `@dataclass(frozen=True)` like `CrashHandlerInstallation`. | Mark `_State` frozen to enforce the "set once on install, never mutated" invariant the surrounding doc string already promises. | Defensive design; prevents accidental mutation of process-wide singleton state. | source review |
| Info | tests/gui/test_crash_handler.py | line 22 (docstring) | The docstring claims tests do not touch the filesystem; idempotency test allocates a real `Path("C:/fake/crash/dir")` that is never opened thanks to monkeypatched seams. | No change; documenting that the seam pattern is correct. | Acknowledges the test's hygienic isolation. | source review |
| Info | src/gui/workers/pipeline_worker.py | lines 108-115 | `except BaseException` widening is correctly paired with an `isinstance(exc, (KeyboardInterrupt, SystemExit)): raise` guard. The boundary is a defined, documented worker-failure boundary per `general-code-change.md`. | No change. | Confirms compliance with "Reserve broad handlers for well-defined boundaries". | source review |
| Info | src/gui/runners.py | line 267 | `SynchronousRunner.run` still uses `except Exception` (not widened to `BaseException`). The synchronous test seam is intentionally narrower than the production threaded worker; this is acceptable and documented. | No change. | Symmetry with worker boundary is not required for the synchronous test seam. | source review |

## Design Principles Review

- **Simplicity first:** Crash-handler module is large (495 lines) but each function is small and single-purpose. The "I/O seam helper" pattern (`_open_crash_log`, `_ensure_log_dir`, `_register_faulthandler`, etc.) keeps each function trivially patchable.
- **Reusability:** `make_qt_message_handler` is decoupled from the installer (accepts a `Logger`) so it can be reused or unit-tested in isolation. `resolve_log_dir` is pure.
- **Extensibility:** `install_crash_handlers` keyword-only signature with `enable: bool = True` provides a documented rollback hook without changing the public contract.
- **Separation of concerns:** Pure helpers (`resolve_log_dir`, `_make_*_excepthook`, `make_qt_message_handler`) are cleanly separated from I/O helpers (`_ensure_log_dir`, `_open_crash_log`, `_register_*`). The composition root is a single call site.

## Test Quality

- AAA structure followed consistently.
- All waits are event-driven (`qtbot.waitSignal`, `qtbot.waitUntil`); no `time.sleep`/`QThread.sleep`.
- No temporary-file usage; I/O seams are patched.
- Pin tests (`test_pipeline_worker_run_reraises_keyboard_interrupt`, `test_pipeline_worker_run_reraises_system_exit`) are correctly documented as baseline-passing pins, not fail-before regressions.
- Coverage thresholds met; see F4 in policy audit for the closure-body gap.

## File-Size Compliance

| File | Lines (`awk NR`) | Under 500 | Notes |
|---|---|---|---|
| src/gui/_crash_handler.py | 495 | Yes (5 lines of headroom) | New module; near the cap |
| src/gui/runners.py | 270 | Yes | +114 lines vs baseline |
| src/gui/workers/pipeline_worker.py | 116 | Yes | +37 lines vs baseline |
| src/gui/app.py | 503 | **No** | Baseline 493 -> head 503 |
| tests/gui/test_crash_handler.py | 332 | Yes | New |
| tests/gui/test_runners_threaded.py | 151 | Yes | New |
| tests/gui/test_pipeline_worker.py | 244 | Yes | +99 lines |
| tests/gui/test_app_composition.py | 474 | Yes (26 lines of headroom) | +73 lines |

## Final Code-Review Verdict

**Changes Requested** — one Blocking finding (app.py 503 lines > 500-line cap) and three Material findings (spec/code symbol drift, closure-body coverage gap, evidence-artifact line-count undercount) require remediation before merge. The structural design and the toolchain-loop outcome are otherwise sound.
