# key-mismatch-dialog-thread-fix (Plan)

- **Issue:** #52
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-06T11-34
- **Status:** Complete
- **Version:** 1.0
- **Work Mode:** full-bug
- **Spec:** docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/spec.md (v1.0, FINAL)
- **Issue/ACs:** docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/issue.md (AC-1..AC-8)

**Fail-closed evidence rule:** Include explicit baseline artifact tasks, final-QA artifact tasks, and coverage-comparison tasks for the in-scope language (Python) because policy requires coverage. If any required baseline artifact, QA artifact, or coverage-comparison artifact is missing, the audit verdict must be BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Record the expected artifact path or location in each evidence-producing task. Do not mark evidence-backed work complete without the artifact.

**Canonical evidence location (non-overridable):** All evidence artifacts MUST be written under
`docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/<kind>/`
using `<kind>` of `baseline`, `regression-testing`, `qa-gates`, `issue-updates`, or `other` per
`.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. Writing to `artifacts/baselines/`,
`artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical path is a policy violation.

## Per-batch budget (python-typed-engineer cap)

Each implementation batch is capped at 3 production files and 3 test files. The mandatory
toolchain gate (Black -> Ruff -> Pyright -> Pytest with `--cov --cov-branch`) runs after each
batch. Phases 2-4 are each one batch and each stays within the cap.

## Critical constraint (verified)

`src/normalize_le.py` is at 495 non-blank / 496 physical lines against the 500-line cap
(verified by the orchestrator with `grep -c`; the research artifact's 412 figure is the
non-blank count and is NOT the controlling number). The `resolver` pass-through addition to
`normalize_le.load_source` MUST be done by EXTRACTION of a cohesive block into a new
`src/_normalize_le_columns.py` helper module so `normalize_le.py` stays <= 500 lines (AC-7).

## AC traceability map

- AC-1 (no cross-thread crash; dialog on GUI thread): P5-T1..P5-T3, P4-T1, P4-T2, P6 QA.
- AC-2 (2-3 example pairs shown): P1-T1, P1-T2, P4-T1, P4-T2.
- AC-3 (no dialog when KEY matches / no KEY column): P1-T1, P1-T2, P4-T2, P3-T2.
- AC-4 ("Keep existing" -> trust default; "Rebuild" -> overwrite): P4-T1, P4-T2.
- AC-5 (example-aware resolver; invoked only on divergence; PipelineService forwards callable): P1-T1, P1-T2, P3-T1, P3-T2.
- AC-6 (CLI stdin path unchanged): P1-T1, P1-T2 (resolver=None branch), P2 gate, P6 QA.
- AC-7 (all files <= 500 lines, notably normalize_le.py): P2-T1, P2-T2, P5-T4, P6-T5.
- AC-8 (full toolchain pass; coverage >= 85% line / >= 75% branch; no regression on changed lines): P0 baseline, P6 QA + coverage delta.

---

### Phase 0 — Baseline Capture & Policy Reads

- [x] [P0-T1] Read the required policy files in precedence order and record a Phase 0 evidence artifact. Files to read, in order: `.claude/rules/general-code-change.md`; `.claude/rules/general-unit-test.md`; `.claude/rules/python.md`; `.claude/rules/python-suppressions.md`; `.claude/rules/self-explanatory-code-commenting.md`; `.claude/rules/quality-tiers.md`. (The repository's standing instructions — the `policy-compliance-order` "CLAUDE.md / always-loaded" layer — are auto-loaded by the harness and are not an openable file; record this in the Policy Order note rather than attempting to open a `CLAUDE.md` file.) Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/baseline/phase0-instructions-read.md` containing `Timestamp:`, `Policy Order:`, and the explicit list of files read. The `Policy Order:` field MUST note that the standing-instructions layer is harness-auto-loaded (not read from a `CLAUDE.md` file on disk).
- [x] [P0-T2] Verify and record the `src/normalize_le.py` line count baseline. Command: `(Get-Content src/normalize_le.py).Count`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/baseline/baseline-normalize-le-linecount.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording the physical line count (expected 496) and the remaining headroom to the 500-line cap.
- [x] [P0-T3] Capture the Black format baseline. Command: `poetry run black --check .`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/baseline/baseline-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T4] Capture the Ruff lint baseline. Command: `poetry run ruff check .`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/baseline/baseline-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P0-T5] Capture the Pyright type-check baseline. Command: `poetry run pyright`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/baseline/baseline-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (error/warning counts).
- [x] [P0-T6] Capture the Pytest + coverage baseline. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/baseline/baseline-pytest-coverage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording the numeric headline values: total tests passed, total line coverage %, and total branch coverage %. These numbers are the no-regression reference for AC-8.

---

### Phase 1 — Resolver Contract Core in etl_key (AC-2, AC-3, AC-5, AC-6)

Batch 1: 1 production file, 1 test file.

- [x] [P1-T1] In `src/etl_key.py`: (a) add a pure helper `_collect_diverging_examples(existing: list[str], rebuilt: list[str], limit: int = 3) -> list[tuple[str, str]]` returning up to `limit` `(existing, rebuilt)` pairs for indices where `existing[i] != rebuilt[i]`, with a Google-style docstring and an intent comment on the collecting loop; (b) add an optional parameter `resolver: Callable[[list[tuple[str, str]]], str] | None = None` to `resolve_key` (keyword-only, default `None`); (c) in the diverging branch of `resolve_key`, when `resolver is not None`, collect examples via `_collect_diverging_examples(existing, rebuilt)` and set `action = resolver(examples)`, otherwise call `decide_key_action(policy, is_tty=is_tty(), prompt=prompt)` exactly as today; (d) preserve the existing trust/overwrite warning logs and the no-KEY-column and matching-KEY branches unchanged; (e) update the `resolve_key` docstring (`Args`/`Raises`) to document the new `resolver` parameter and the divergence-only invocation. Add `Callable` to the runtime/`TYPE_CHECKING` imports as needed. File must stay <= 500 lines.
- [x] [P1-T2] In `tests/test_etl_key.py`: add deterministic unit tests covering: `_collect_diverging_examples` truncation to 3 and correct pair contents (only diverging indices, in order); `resolve_key` invokes an injected recording resolver only on genuine divergence and passes the exact expected example pairs; `resolve_key` maps the injected resolver's `"trust"` and `"overwrite"` returns to keep-existing vs rebuilt KEY respectively (assert the warning log via `caplog`); `resolver=None` (CLI path) behavior is unchanged across trust, overwrite, no-divergence, and no-KEY-column scenarios. No temp files, no real stdin (use injected `is_tty`/`prompt`). Use Arrange-Act-Assert and descriptive `test_...` names.
- [x] [P1-T3] Run the mandatory toolchain gate for Batch 1 and record evidence. Commands in order, restarting from Black on any failure or file change: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest tests/test_etl_key.py --cov=src/etl_key --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/batch1-etl-key-gate.md` with `Timestamp:`, `Command:` (each stage), `EXIT_CODE:` (each stage), and `Output Summary:` (final pass status and `src/etl_key.py` line+branch coverage %).

---

### Phase 2 — Thread resolver through the loaders (AC-5, AC-6, AC-7)

Batch 2: 3 production files (one new helper module via extraction), 0 new test files (loader behavior is covered by existing loader tests plus Phase 1; this batch's gate runs the full loader test modules to confirm no regression).

- [x] [P2-T1] Create new module `src/_normalize_le_columns.py` by EXTRACTING a cohesive block from `src/normalize_le.py` so the parent file stays <= 500 lines after the Phase 2 addition. Extract the column-schema constants and the column-resolution helper into the new module: move `MONTH_COLUMNS`, `YTG_MONTHS`, `QUARTER_COLUMNS`, `QUARTER_TO_MONTHS`, `SUM_COLUMNS`, `TEXT_COLUMNS`, `SOURCE_COLUMNS`, `EXPECTED_COLUMNS`, `TARGET_COLUMNS`, and a new pure helper `resolve_le_columns(actual_columns: list[str]) -> tuple[dict[str, str], str | None]` that performs the KEY-column lookup + `resolve_columns` call (the block currently inline in `load_source`). Give the module a complete module docstring and Google-style docstrings on the helper. The new module must be <= 500 lines.
- [x] [P2-T2] In `src/normalize_le.py`: (a) import the extracted constants and `resolve_le_columns` from `src._normalize_le_columns` and re-export them via `__all__` so existing callers/tests importing them from `normalize_le` keep working; (b) replace the now-extracted inline column-resolution block in `load_source` with a call to `resolve_le_columns(...)`; (c) add a keyword-only optional parameter `resolver: Callable[[list[tuple[str, str]]], str] | None = None` to `load_source` and forward it to `resolve_key(..., resolver=resolver)`; (d) update the `load_source` docstring to document `resolver`. Verify with `(Get-Content src/normalize_le.py).Count` that the file is <= 500 physical lines and record the post-extraction count in the batch gate artifact. File must stay <= 500 lines.
- [x] [P2-T3] In `src/load_aop.py`: add a keyword-only optional parameter `resolver: Callable[[list[tuple[str, str]]], str] | None = None` to `load_aop` and forward it to `resolve_key(..., resolver=resolver)`; update the `load_aop` docstring to document `resolver`. The CLI `main` path passes no resolver (unchanged, AC-6). File is 388 lines; addition is safe in place and must stay <= 500 lines.
- [x] [P2-T4] Run the mandatory toolchain gate for Batch 2 and record evidence. Commands in order, restarting from Black on any failure or file change: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest tests/test_normalize_le.py tests/test_load_aop.py tests/test_etl_key.py --cov=src/normalize_le --cov=src/_normalize_le_columns --cov=src/load_aop --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/batch2-loaders-gate.md` with `Timestamp:`, `Command:` (each stage), `EXIT_CODE:` (each stage), and `Output Summary:` recording final pass status, the post-extraction physical line count of `src/normalize_le.py` (must be <= 500), and line+branch coverage % for the three loader modules.

---

### Phase 3 — PipelineService forwards the resolver callable (AC-3, AC-5)

Batch 3: 1 production file, 1 test file.

- [x] [P3-T1] In `src/gui/pipeline_service.py`: (a) change the `_key_mismatch_resolver` attribute type and the `__init__` `key_mismatch_resolver` parameter type from `Callable[[], str]` to `Callable[[list[tuple[str, str]]], str]` and update the attribute/parameter docstrings to describe the example-aware contract and divergence-only invocation; (b) in `import_le`, pass `resolver=self._key_mismatch_resolver` (the callable itself) to `normalize_le.load_source(...)` instead of the current eager `key_mismatch=self._key_mismatch_resolver()` call; keep `is_tty=never_tty` and `prompt=no_stdin_prompt` and the default `key_mismatch` policy on the loader (the resolver branch takes precedence on divergence); (c) in `import_aop`, pass `resolver=self._key_mismatch_resolver` to `load_aop.load_aop(...)` the same way (remove the eager call at the current line ~317); (d) update the inline comments that describe the eager-policy behavior to describe the callable-forwarding behavior. File must stay <= 500 lines.
- [x] [P3-T2] In `tests/gui/test_pipeline_service_key_seam.py`: add deterministic unit tests asserting that `import_le` and `import_aop` forward the resolver CALLABLE (not its result) to the loaders — patch `normalize_le.load_source` and `load_aop.load_aop` at their import location in `pipeline_service` and assert the `resolver=` kwarg is the same object as the injected resolver; assert the injected resolver is NOT invoked when the loader reports no divergence (use a recording resolver whose call count stays 0 in a no-divergence path). No real Excel reads (patch the loaders), no temp files.
- [x] [P3-T3] Run the mandatory toolchain gate for Batch 3 and record evidence. Commands in order, restarting from Black on any failure or file change: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest tests/gui/test_pipeline_service_key_seam.py tests/gui/test_pipeline_service.py --cov=src/gui/pipeline_service --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/batch3-pipeline-service-gate.md` with `Timestamp:`, `Command:` (each stage), `EXIT_CODE:` (each stage), and `Output Summary:` (final pass status and `pipeline_service` line+branch coverage %).

---

### Phase 4 — Example-aware GUI seam & dialog (AC-1, AC-2, AC-3, AC-4)

Batch 4: 2 production files, 1 test file.

- [x] [P4-T1] In `src/gui/_key_mismatch_seam.py`: change `default_key_mismatch_resolver` to accept and ignore an `examples` argument matching the new contract — signature `default_key_mismatch_resolver(_examples: list[tuple[str, str]]) -> str` returning `"trust"`; update the docstring to document the ignored `examples` parameter and the example-aware contract. Use the `ARG001`/`ARG002` handling only if Ruff flags the unused parameter and only per the pre-authorized suppression format in `.claude/rules/python-suppressions.md`; otherwise prefer the `_examples` underscore-prefixed name to avoid a suppression. `never_tty` and `no_stdin_prompt` are unchanged. File must stay <= 500 lines.
- [x] [P4-T2] In `src/gui/_key_mismatch_dialog.py`: (a) make the `ask` seam example-aware — change `_qmessagebox_ask` and the `ask` callable type to accept the example pairs (`ask: Callable[[MainWindow | None, list[tuple[str, str]]], bool]`) and render the 2-3 `(source KEY, computed KEY)` pairs in the `QMessageBox` body text below the existing explanation, keeping "Keep existing" as the `AcceptRole` default button and "Rebuild" as `DestructiveRole`; (b) change `build_key_mismatch_resolver` to return a `Callable[[list[tuple[str, str]]], str]` that, when invoked, dispatches via the new bridge from Phase 5 (`src/gui/_key_mismatch_bridge.py`): construct/hold a bridge bound to the example-aware `ask` and the parent window, and the returned resolver delegates to `bridge.resolve(examples)`; map the bridge's boolean result to `"trust"` (Keep existing) / `"overwrite"` (Rebuild); (c) update the module and function docstrings to describe the example-aware contract and the bridge dispatch. (Phase 5 creates the bridge; this task wires `build_key_mismatch_resolver` to it. If executor sequencing requires the bridge first, swap the order of Phase 4 and Phase 5 batches; the per-batch cap is preserved either way.) File must stay <= 500 lines.
- [x] [P4-T3] In `tests/gui/test_key_mismatch_dialog.py`: add deterministic unit tests asserting the example-aware `ask` seam renders the example pairs in the dialog body (use the existing recording `QMessageBox` stand-in pattern, extended to capture the rendered text and assert each pair appears); the trust/overwrite mapping ("Keep existing" -> `"trust"`, "Rebuild" -> `"overwrite"`); "Keep existing" is the default button; and that the resolver produced by `build_key_mismatch_resolver` returns the correct policy for each choice. No real modal (inject `ask`), no real threads (same-thread invocation), no temp files.
- [x] [P4-T4] Run the mandatory toolchain gate for Batch 4 and record evidence. Commands in order, restarting from Black on any failure or file change: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest tests/gui/test_key_mismatch_dialog.py --cov=src/gui/_key_mismatch_dialog --cov=src/gui/_key_mismatch_seam --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/batch4-dialog-seam-gate.md` with `Timestamp:`, `Command:` (each stage), `EXIT_CODE:` (each stage), and `Output Summary:` (final pass status and dialog+seam line+branch coverage %).

---

### Phase 5 — Cross-thread bridge & composition-root wiring (AC-1)

Batch 5: 2 production files (one new), 1 test file.

- [x] [P5-T1] Create new module `src/gui/_key_mismatch_bridge.py` defining a `QObject` bridge (mirroring the `_RunnerReceiver` + queued-connection pattern in `src/gui/runners.py`). The bridge is constructed on the GUI thread, holds the example-aware `ask` callable and the parent window, and exposes `resolve(examples: list[tuple[str, str]]) -> bool`. Behavior: (a) SAME-THREAD GUARD — if `QThread.currentThread()` is the bridge's GUI thread (the application/GUI thread captured at construction), call `ask(window, examples)` directly with no `threading.Event` and no blocking (prevents deadlock under `SynchronousRunner` and in tests); (b) CROSS-THREAD PATH — when invoked from a worker thread, marshal the dialog onto the GUI thread via a Qt signal connected to a GUI-thread slot with `Qt.ConnectionType.QueuedConnection`, and block the worker on a `threading.Event` until the slot stores the result and sets the event; (c) EXCEPTION SAFETY — the GUI-thread slot must NOT swallow exceptions raised while showing the dialog: capture the exception, set the event, and re-raise it on the worker side after `event.wait()` returns. Provide a complete class docstring (purpose, responsibilities, thread-affinity invariant, exception-surfacing contract) and Google-style method docstrings. File must stay <= 500 lines.
- [x] [P5-T2] In `src/gui/app.py`: update the composition-root wiring so the bridge is constructed on the GUI thread and injected. Confirm the `key_mismatch_resolver=build_key_mismatch_resolver()` injection (current line ~316) produces a resolver matching the new `Callable[[list[tuple[str, str]]], str]` contract and that the parent `MainWindow` is passed to `build_key_mismatch_resolver(window=...)` so the bridge has a GUI-thread parent. Update any affected import or docstring. File must stay <= 500 lines.
- [x] [P5-T3] In `tests/gui/test_key_mismatch_bridge.py` (NEW): add deterministic unit tests, headless under `QT_QPA_PLATFORM=offscreen` via `tests/gui/conftest.py`, covering: the same-thread guard calls the injected `ask` directly and returns its result WITHOUT creating a `threading.Event` or blocking (invoke on the GUI/calling thread); the cross-thread path marshals to the GUI thread and unblocks the worker with the correct result (drive deterministically without a real modal — inject an `ask` stand-in and pump the Qt event loop with `qtbot`/`QApplication.processEvents`, not a real `exec()`); an exception raised inside `ask` on the GUI thread is surfaced (re-raised) on the worker side and NOT swallowed. No real modal, no `time.sleep`, no temp files; use a seeded/deterministic event-loop pump.
- [x] [P5-T4] Verify file-size compliance for every changed/added source file (AC-7). Command: for each of `src/etl_key.py`, `src/normalize_le.py`, `src/_normalize_le_columns.py`, `src/load_aop.py`, `src/gui/pipeline_service.py`, `src/gui/_key_mismatch_seam.py`, `src/gui/_key_mismatch_dialog.py`, `src/gui/_key_mismatch_bridge.py`, `src/gui/app.py`, run `(Get-Content <file>).Count`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/filesize-compliance.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` listing each file's physical line count and confirming all <= 500.
- [x] [P5-T5] Run the mandatory toolchain gate for Batch 5 and record evidence. Commands in order, restarting from Black on any failure or file change: `poetry run black .` -> `poetry run ruff check .` -> `poetry run pyright` -> `poetry run pytest tests/gui/test_key_mismatch_bridge.py --cov=src/gui/_key_mismatch_bridge --cov=src/gui/app --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/batch5-bridge-gate.md` with `Timestamp:`, `Command:` (each stage), `EXIT_CODE:` (each stage), and `Output Summary:` (final pass status and bridge+app line+branch coverage %).

---

### Phase 6 — Final Full QA Loop & Coverage Delta (AC-6, AC-7, AC-8)

Full Python toolchain over the whole repository; restart from step 1 on any failure or file change until one clean pass completes.

- [x] [P6-T1] Run the full-repository Black format check. Command: `poetry run black --check .`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/final-black.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. If files change, reformat and restart the loop from this task.
- [x] [P6-T2] Run the full-repository Ruff lint check. Command: `poetry run ruff check .`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/final-ruff.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (0 errors required; any suppression must match `.claude/rules/python-suppressions.md`). On failure, fix and restart from P6-T1.
- [x] [P6-T3] Run the full-repository Pyright type check. Command: `poetry run pyright`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/final-pyright.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (0 errors required). On failure, fix and restart from P6-T1.
- [x] [P6-T4] Run the full Pytest suite with coverage. Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/final-pytest-coverage.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording numeric headline values: total tests passed, total line coverage %, total branch coverage %. Confirm the CLI `--key-mismatch` stdin-path tests in `tests/test_etl_key.py`, `tests/test_normalize_le.py`, and `tests/test_load_aop.py` still pass (AC-6). On failure or file change, restart from P6-T1.
- [x] [P6-T5] Verify the coverage delta and file-size invariants (AC-7, AC-8). Compare the Phase 0 baseline coverage (P0-T6) against the final coverage (P6-T4) and confirm: total line coverage >= 85%; total branch coverage >= 75%; no regression on changed lines for the changed modules; every changed/added source file <= 500 lines (cross-reference P5-T4). Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/coverage-delta.md` with `Timestamp:`, `Command:` (the comparison performed), `EXIT_CODE:`, and `Output Summary:` reporting: baseline line/branch %, post-change line/branch %, changed-module new-code coverage %, and the file-size compliance result. If any threshold is unmet, the outcome is remediation-required, not PASS.
- [x] [P6-T6] Record the AC verification summary mapping AC-1..AC-8 to the evidence artifacts that demonstrate each. Write `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/qa-gates/ac-verification-summary.md` with `Timestamp:` and one line per AC citing the satisfying artifact path(s) and a pass/remediation verdict.

---

## Notes for the executor

- Phase ordering: Phase 4 (dialog wiring to the bridge) references the Phase 5 bridge module. If the executor prefers to land the bridge first, swap the Phase 4 and Phase 5 batches; each batch independently respects the 3-production / 3-test cap and the toolchain gate.
- The CLI stdin path (`decide_key_action`, the loaders' `main`, and `--key-mismatch`) must remain behaviorally unchanged; the new `resolver` parameter defaults to `None` on every loader and is only supplied by the GUI composition root (AC-6).
- No new third-party dependencies. PySide6 and pytest-qt are already present.
- All evidence artifacts go under `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/<kind>/`; non-canonical paths fail preflight.
