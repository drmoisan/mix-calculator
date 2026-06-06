# key-mismatch-dialog-thread-fix (Issue #52)

- Date captured: 2026-06-06
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/key-mismatch-dialog-thread-fix/ (Issue #52)

- Issue: #52
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/52
- Last Updated: 2026-06-06
- Work Mode: full-bug

## Problem / Why

Clicking "Import" on the LE source raises the KEY-mismatch modal ("The source
KEY column does not match the rebuilt pattern"), and clicking either button
("Keep existing" or "Rebuild") crashes the worker thread. The crash is
accompanied by the Qt diagnostic `QBasicTimer::stop: Failed. Possibly trying to
stop from a different thread`.

Root cause (traced 2026-06-06):

1. **Cross-thread Qt dialog (crash).** Production wiring injects
   `build_key_mismatch_resolver()` (a `QMessageBox`-backed modal) into
   `PipelineService` and injects `ThreadedRunner` as the runner. An import click
   dispatches the loader task off the UI thread (`_import_dispatch_wiring` ->
   `runner.run` -> `PipelineWorker.run` on a `QThread`). Inside that worker
   thread, `PipelineService.import_le`/`import_aop` calls the resolver, which
   constructs and `exec()`s a `QMessageBox`. Creating/showing a Qt widget off the
   GUI thread is undefined behavior and produces the `QBasicTimer::stop` warning
   and the crash.

2. **Eager invocation (modal fires every import; no examples possible).**
   `pipeline_service.py` evaluates `self._key_mismatch_resolver()`
   unconditionally to compute the policy string, before `etl_key.resolve_key`
   does the per-row comparison. The modal therefore appears on every LE/AOP
   import, not only on a genuine divergence, and it has no per-row data, so the
   dialog text is static with no examples.

3. **Missing examples (enhancement request).** The user wants the dialog to show
   two to three concrete examples of the source `KEY` versus the computed
   (rebuilt) `KEY`. The current resolver contract is zero-arg
   (`Callable[[], str]`) and cannot carry example pairs.

## Proposed Behavior

- The KEY-mismatch dialog appears only when the source `KEY` genuinely diverges
  from the rebuilt pattern.
- The dialog displays two to three example rows, each showing the source `KEY`
  and the computed `KEY` so the user can diagnose the divergence. Real values are
  shown in the live dialog (confidentiality policy governs committed files, not a
  runtime dialog).
- Selecting "Keep existing" (the default) or "Rebuild" returns the matching
  loader policy and does not crash. The dialog renders on the GUI thread while
  the off-thread import worker blocks for the answer.

## Acceptance Criteria

Canonical AC list (mirrors spec.md v1.0):

- [x] AC-1: With a threaded (off-UI-thread) runner and a diverging KEY, the
      KEY-mismatch dialog is shown on the GUI thread and neither button choice
      produces the `QBasicTimer::stop` cross-thread warning or a crash.
- [x] AC-2: The dialog displays 2-3 `(source KEY, computed KEY)` example pairs
      taken from the diverging rows.
- [x] AC-3: No dialog appears when the source KEY matches the rebuilt pattern or
      when there is no KEY column; the import proceeds.
- [x] AC-4: "Keep existing" maps to `trust` and is the default button; "Rebuild"
      maps to `overwrite`.
- [x] AC-5: The resolver contract carries example pairs and `resolve_key` invokes
      the resolver only on divergence; `PipelineService` passes the resolver
      callable into the loaders (no eager invocation).
- [x] AC-6: The CLI `--key-mismatch` stdin path (`decide_key_action`) is
      unchanged and its tests still pass.
- [x] AC-7: All changed/added source files remain <= 500 lines (notably
      `normalize_le.py`).
- [x] AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Constraints & Risks

- `src/normalize_le.py` is at 495/500 lines; the loader pass-through change must
  be done by extraction, not in-place addition (file-size cap).
- Cross-thread marshaling must block the worker thread for the user's answer
  without deadlocking the GUI event loop.
- The resolver contract change touches `etl_key`, both loaders, the service, and
  the dialog seam; CLI behavior (stdin prompt path) must be preserved.

## Test Conditions to Consider

- [ ] Unit: `etl_key.resolve_key` collects example pairs and invokes the resolver
      only on divergence; CLI stdin path unchanged.
- [ ] Unit: dialog renders example pairs; trust/overwrite mapping; default button.
- [ ] Integration: threaded-runner import with diverging KEY does not crash and
      resolves through the UI-thread dialog.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create active feature folder from the template