# Code Review — key-mismatch-dialog-thread-fix (Issue #52)

- Timestamp: 2026-06-06T12-26
- Branch: fix/key-mismatch-dialog-thread-fix-52
- HEAD: 1e49546
- Base: main (merge-base 5e659f2)
- Reviewer: feature-review agent

## Executive Summary

The change resolves the cross-thread Qt crash in the KEY-mismatch dialog and adds
example pairs to the dialog body. The design follows the spec: the resolver contract
becomes example-aware (`Callable[[list[tuple[str, str]]], str]`), `resolve_key`
invokes the resolver only on genuine divergence, `PipelineService` forwards the
resolver callable (not its result), and a new `KeyMismatchBridge` marshals the modal
onto the GUI thread with a same-thread deadlock guard and a non-swallowing
exception path.

The cross-thread bridge is correct for the production usage pattern: the same-thread
guard prevents GUI-thread deadlock, the queued-connection signal delivers the slot on
the GUI thread, `threading.Event.set/wait` provides the happens-before barrier for the
shared result/error fields, and the slot sets the event in a `finally` so the worker
can never block forever. The full production wiring chain is present (app.py builds the
resolver with the GUI window and injects it; the service forwards it to both loaders;
the loaders forward it to `resolve_key`), so the tested seams have real production
callers.

No behavior change was found outside the issue scope. The CLI `decide_key_action`
stdin path is preserved (resolver defaults to `None`). One Minor concurrency note and
two Nits are recorded; none are blocking.

Reviewer-run toolchain: Black, Ruff, Pyright all clean; full pytest suite 834 passed;
changed-module coverage 100% (app.py 99%, pre-existing uncovered line).

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | src/gui/_key_mismatch_bridge.py | 138-176 | Shared instance fields `_result`/`_error` are reused per `resolve` call. Within one import run the two loader resolver calls are sequential, so this is safe; two overlapping import runs hitting divergence simultaneously could race the fields. | Document the single-flight assumption in the class docstring, or guard `resolve` with a `threading.Lock` so overlapping cross-thread calls serialize. | `import_sources` runs LE/AOP/SKU_LU sequentially in one worker task, so the common path is single-flight; the race requires two concurrent import runs, an uncommon modal-blocked UI path. | pipeline_service.py:402-406 (sequential imports); runners.py:174-217 (ThreadedRunner allows concurrent dispatches) |
| Nit | src/gui/app.py | end of file | File is exactly 500 lines (at the cap) after the window-build reorder. Any future addition will breach the limit. | When app.py next changes, extract the composition steps into a helper module to restore headroom. | The 500-line cap is a hard policy limit; zero headroom invites a future violation. | app.py line count = 500 (awk) |
| Nit | src/gui/_key_mismatch_dialog.py | 57-72 | `_format_examples` hardcodes the `\n\n` separator and "Examples (source KEY -> computed KEY):" header inline. | Optional: promote the header to a module constant alongside `_DIALOG_TEXT` for symmetry. | Cosmetic; the current form is readable and tested. | dialog diff |

## Correctness Review (per caller obligations)

### Cross-thread bridge

- Same-thread guard (`_key_mismatch_bridge.py:138-141`): when
  `QThread.currentThread() is self._gui_thread`, `ask` is called directly with no
  Event and no blocking. This prevents the deadlock that would occur if the GUI thread
  blocked on `done.wait()` while also being the only thread that could pump the event
  loop delivering the queued slot. Correct.
- Cross-thread path (`:155-176`): emits the queued signal with a fresh
  `threading.Event`, resets `_error` before emit, blocks on `done.wait()`, and
  re-raises `_error` if set. Correct.
- Exception surfacing (`:178-204`): `_on_request` wraps `ask` in try/except, stores the
  exception (does not swallow), and sets `done` in `finally`. `resolve` re-raises it on
  the worker side. Verified by `test_cross_thread_exception_is_surfaced_on_worker`.
- Memory-visibility: `_result`/`_error` are written on the GUI thread before
  `done.set()` and read on the worker after `done.wait()` returns;
  `threading.Event` provides the happens-before barrier. Correct.
- Qt thread-affinity: the bridge is constructed on the GUI thread (at the composition
  root in `app.py` and in each test), is never `moveToThread`'d, and connects
  `_request -> _on_request` with `Qt.ConnectionType.QueuedConnection`, so a
  worker-thread emit delivers the slot on the GUI thread's event loop. The class
  docstring states the invariant explicitly. Correct.
- No resource leak: no widgets are created on the worker thread; the `QMessageBox` is
  constructed inside `ask` on the GUI thread only.

### Resolver-only-on-divergence

`resolve_key` (`etl_key.py:289-303`) computes the divergence branch first; the resolver
is invoked only inside that branch. The matching and no-KEY-column paths return before
reaching the resolver. Verified by `test_resolve_key_resolver_not_invoked_when_matching`
and `test_resolve_key_resolver_not_invoked_when_no_key_column`. The eager
`self._key_mismatch_resolver()` calls were removed from `PipelineService.import_le`
and `import_aop`; the callable is now forwarded as `resolver=`.

### Example-pair collection and truncation

`_collect_diverging_examples` (`etl_key.py:128-159`) walks the aligned existing/rebuilt
lists with `zip(..., strict=True)`, appends only diverging pairs, and breaks at
`limit` (default 3). `strict=True` raises if the lists differ in length, which is the
correct fail-fast posture. Verified by the order, truncation, and identical-list tests.

### Loader threading

`normalize_le.load_source` (`:181`) and `load_aop.load_aop` (`:255`) forward
`resolver=resolver` to `resolve_key` and default it to `None`, preserving the CLI path.

### CLI path preservation

`decide_key_action` body is unchanged (only the surrounding docstring was edited). With
`resolver=None` the diverging branch falls back to
`decide_key_action(policy, is_tty=is_tty(), prompt=prompt)` exactly as before. CLI
stdin-path tests pass (`pytest -k "prompt or tty or key_mismatch or stdin or decide_key"`
-> 9 passed). Verified by `test_resolve_key_resolver_none_preserves_cli_path`.

### Behavior change outside scope

The only out-of-scope edit is the `app.py` reorder that builds `MainWindow()` before the
`PipelineService` so the resolver/bridge is parented to the GUI-thread window. The window
was previously built later in the same function; the variable is still used by the same
downstream code. No functional change to other composition steps. The full GUI
composition test suite passes (834 total). No behavior change found outside scope.

## Code Review Verdict: PASS

No FAIL findings and no blocking-PARTIAL findings. 1 Minor, 2 Nit (all non-blocking).
