# key-mismatch-dialog-thread-fix (Spec)

- **Issue:** #52
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-06
- **Status:** Final
- **Version:** 1.0

## Context
- The GUI crashes when importing the LE (or AOP) source if the source `KEY`
  column diverges from the rebuilt pattern. The KEY-mismatch modal appears, and
  selecting either button crashes the worker thread.
- Observed environment(s): Windows desktop GUI (PySide6), production import path
  using `ThreadedRunner` (off-UI-thread import).
- Customer impact and severity: High for the affected workflow — the import
  cannot complete and the application thread crashes whenever a source KEY
  diverges. Reproduced by the user 2026-06-06.
- First observed: 2026-06-06 on `main` (the KEY-mismatch seam and `ThreadedRunner`
  originate from issue #48, merged in PR #49).

## Repro & Evidence
- Steps to reproduce: launch the GUI, select an LE workbook whose `KEY` column
  diverges from `Customer + coerce_sku(SKU #) + Type`, click Import (LE). The
  KEY-mismatch modal appears; click "Keep existing" or "Rebuild".
- Expected vs actual: expected the chosen policy to apply and the import to
  proceed; actual is a worker-thread crash.
- Logs/error snippets: `WARNING:src.gui._crash_handler.qt:Qt: QBasicTimer::stop:
  Failed. Possibly trying to stop from a different thread`.
- Frequency / determinism: deterministic whenever the source KEY diverges and the
  import runs through the threaded runner.

## Scope & Non-Goals
- In scope:
  - Eliminate the cross-thread Qt crash by rendering the KEY-mismatch dialog on
    the GUI thread while the off-thread import worker blocks for the answer.
  - Invoke the resolver only on genuine KEY divergence (remove the eager
    per-import policy evaluation in `PipelineService`).
  - Extend the resolver contract so the dialog shows 2-3 (source KEY, computed
    KEY) example pairs taken from the diverging rows.
- Out of scope / non-goals:
  - Changing the CLI `--key-mismatch` stdin prompt path (must remain unchanged).
  - Changing the trust/overwrite semantics or the loader transform logic.
  - Any change to the schema-builder work in PR #51 (#50).

## Root Cause Analysis
- Confirmed root cause (three coupled parts):
  1. Cross-thread Qt dialog: `app.py` injects the `QMessageBox`-backed resolver
     (`_key_mismatch_dialog.build_key_mismatch_resolver`) into `PipelineService`
     and injects `ThreadedRunner`. The import task runs on a worker `QThread`
     (`_import_dispatch_wiring` -> `runner.run` -> `PipelineWorker.run`), and the
     resolver constructs/`exec()`s a `QMessageBox` on that worker thread. Showing
     a Qt widget off the GUI thread is the documented cross-thread violation.
  2. Eager invocation: `pipeline_service.py` calls `self._key_mismatch_resolver()`
     unconditionally (lines ~288, ~317) to compute the policy string before any
     per-row comparison, so the modal fires on every import.
  3. Zero-arg contract: the resolver is `Callable[[], str]`, so it cannot carry
     diverging example pairs to the dialog.
- Affected components: `src/etl_key.py`, `src/normalize_le.py`, `src/load_aop.py`,
  `src/gui/pipeline_service.py`, `src/gui/_key_mismatch_seam.py`,
  `src/gui/_key_mismatch_dialog.py`, `src/gui/app.py`.

## Proposed Fix

### Design summary (what changes where):
- Change the resolver contract from `Callable[[], str]` to an example-aware
  callable `Callable[[list[tuple[str, str]]], str]` that returns `"trust"` or
  `"overwrite"`, invoked only on divergence.
- `etl_key.resolve_key` gains an optional `resolver` parameter. On divergence,
  it collects up to three diverging `(existing, rebuilt)` example pairs and calls
  `resolver(examples)`. When `resolver` is `None` (the CLI path), behavior is
  unchanged (uses `decide_key_action` with `policy`/`is_tty`/`prompt`).
- `normalize_le.load_source` and `load_aop.load_aop` thread the optional
  `resolver` through to `resolve_key`.
- `pipeline_service.py` passes the resolver callable itself into the loaders
  (`resolver=self._key_mismatch_resolver`) instead of eagerly calling it.
- The GUI resolver (`_key_mismatch_dialog`) is example-aware and renders the
  pairs. A new cross-thread bridge marshals the dialog onto the GUI thread when
  the resolver is invoked from a worker thread, blocking the worker for the
  result. When already on the GUI thread (e.g. `SynchronousRunner` and tests),
  the dialog is called directly with no blocking (deadlock guard).

### Boundaries and invariants to preserve:
- CLI stdin prompt path (`decide_key_action`) is unchanged.
- "Keep existing" maps to `trust` and is the default button; "Rebuild" maps to
  `overwrite`.
- No dialog when the KEY matches or there is no KEY column.
- All source files remain <= 500 lines.

### Dependencies or blocked work:
- None blocking. PR #51 (#50) is open against main and is independent; potential
  merge-order conflicts in `pipeline_service.py` are resolvable at PR time.

### Implementation strategy (what changes, not sequencing):

#### Files/modules to change:
- `src/etl_key.py` — add a pure `_collect_diverging_examples` helper; add the
  optional `resolver` parameter to `resolve_key`.
- `src/normalize_le.py` — thread `resolver` through `load_source`. **The file is
  at 495/500 lines; the addition MUST be done by extraction** (move a cohesive
  block to a `_normalize_le_*` helper module) so the file stays <= 500.
- `src/load_aop.py` — thread `resolver` through `load_aop` (387 lines; safe).
- `src/gui/pipeline_service.py` — pass `resolver=self._key_mismatch_resolver`
  (the callable) into the loaders; update the `_key_mismatch_resolver` type.
- `src/gui/_key_mismatch_seam.py` — `default_key_mismatch_resolver` accepts and
  ignores the examples argument, still returning `"trust"`.
- `src/gui/_key_mismatch_dialog.py` — example-aware resolver/`ask` seam; render
  2-3 example pairs; same-thread vs cross-thread dispatch via the bridge.
- New module `src/gui/_key_mismatch_bridge.py` — `QObject` bridge that marshals
  the dialog onto the GUI thread from a worker thread (signal + `threading.Event`
  wait), keeping the dialog module under 500 lines and independently testable.

#### Functions/classes/CLI commands impacted:
- `etl_key.resolve_key` (signature add), new `etl_key._collect_diverging_examples`.
- `normalize_le.load_source`, `load_aop.load_aop` (signature add).
- `PipelineService.import_le`/`import_aop`/`__init__` (type + call change).
- `_key_mismatch_seam.default_key_mismatch_resolver` (signature change).
- `_key_mismatch_dialog.build_key_mismatch_resolver`, `_qmessagebox_ask`.
- CLI `mix_pipeline`/loader stdin path: unchanged.

#### Data flow and validation changes:
- Examples are `list[tuple[str, str]]` of `(source_key, computed_key)` for rows
  where `existing[i] != rebuilt[i]`, truncated to the first three.

#### Error handling and logging updates:
- Preserve existing trust/overwrite warning logs in `resolve_key`.
- The cross-thread bridge must not swallow exceptions raised while showing the
  dialog; surface them on the worker thread after the wait completes.

#### Rollback/feature-flag considerations:
- None; the default resolver behavior (trust) is preserved for callers that do
  not inject a GUI resolver.

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:
- Resolver type: `Callable[[list[tuple[str, str]]], str]` returning `"trust"` or
  `"overwrite"`.
- `resolve_key(..., resolver: Callable[[list[tuple[str, str]]], str] | None = None)`.

#### Required configuration keys and defaults:
- None.

#### Backward-compatibility expectations:
- CLI and any non-GUI caller using `policy`/`is_tty`/`prompt` is unchanged
  (resolver defaults to `None`).
- The GUI seam default remains `"trust"`.

#### Performance constraints:
- Example collection is O(rows) over already-computed series; negligible.

## Assumptions, Constraints, Dependencies
- Assumptions: production import runs through `ThreadedRunner`; tests use
  `SynchronousRunner` on the GUI/calling thread.
- Constraints: 500-line file cap; no new third-party dependencies; Pyright-clean;
  coverage >= 85% line / >= 75% branch on changed lines.
- External dependencies: PySide6 (already present), pytest-qt (already present).

## Data / API / Config Impact
- User-facing: the dialog now lists concrete example pairs and no longer crashes.
- Data/migration: none.
- Logging/telemetry: unchanged except the bridge must not mask exceptions.
- Compatibility: CLI flags/config unchanged.

## Test Strategy
- Unit (`tests/test_etl_key.py`): `_collect_diverging_examples` truncation and
  pair contents; `resolve_key` invokes the injected resolver only on divergence
  and passes correct examples; CLI path (resolver=None) unchanged for
  trust/overwrite/no-divergence/no-KEY-column.
- Unit (`tests/gui/test_key_mismatch_dialog.py`): example-aware `ask` seam renders
  pairs; trust/overwrite mapping; "Keep existing" default; no dialog when no
  divergence.
- Unit (`tests/gui/test_key_mismatch_bridge.py`, new): same-thread guard calls
  the dialog directly without blocking; cross-thread path marshals and unblocks
  on result; exceptions surfaced not swallowed. Use the GUI/calling thread for
  the same-thread case; drive the cross-thread case deterministically without a
  real modal.
- Unit (`tests/gui/test_pipeline_service_key_seam.py`): the resolver callable
  (not its result) is forwarded to the loaders; the resolver is not invoked when
  no divergence occurs.
- Toolchain: `poetry run black .` -> `poetry run ruff check .` -> `poetry run
  pyright` -> `poetry run pytest --cov --cov-branch --cov-report=term-missing`.
- Manual validation: not required for merge (no real dialog in CI); covered by
  deterministic seams.

## Acceptance Criteria
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

## Risks & Mitigations
- Risk: cross-thread marshaling deadlock if the resolver is invoked on the GUI
  thread. Mitigation: same-thread guard calls the dialog directly.
- Risk: `normalize_le.py` exceeding the 500-line cap. Mitigation: extract a
  cohesive helper module rather than adding in place.
- Risk: merge-order conflict with PR #51 in `pipeline_service.py`. Mitigation:
  small, localized change; resolve at PR time.

## Rollout & Follow-up
- Rollout: standard PR to main with green CI.
- Follow-up: none anticipated.
- Links: issue #52; research `artifacts/research/key-mismatch-dialog-thread-fix-52.md`.
