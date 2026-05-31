# Remediation Inputs — gui-silent-crash-crash-visibility (Issue #46)

- **Timestamp:** 2026-05-31T02-43
- **Source audits:**
  - `policy-audit.2026-05-31T02-43.md`
  - `code-review.2026-05-31T02-43.md`
  - `feature-audit.2026-05-31T02-43.md`

## Remediation-Required Findings

### R1 — Restore the 500-line cap in `src/gui/app.py` (Blocking)

- **Source:** Policy audit F1 / Code review Blocking finding / Feature audit AC-12 FAIL.
- **Current state:** `src/gui/app.py` is 503 lines at HEAD (`awk 'END{print NR}'` and `wc -l` agree). Baseline was 493 (under cap); the +10-line change pushed it past 500.
- **Required action:** Reduce `src/gui/app.py` to <= 500 lines. Recommended approach (lowest risk):
  - Extract the four lines that install crash handlers in `main()` (the `_crash_installation = install_crash_handlers(app_name="mix-calculator")` block, plus the `del` line and surrounding comment) into a new helper module, e.g. `src/gui/_crash_handler_bootstrap.py`, exposing `install_for_main() -> None`. Replace the inline block with `install_for_main()`.
  - Alternative: extract one of the closures inside `wire_control_signals` (e.g., `_handle_export`) into a sibling helper module.
- **Definition of done:**
  - `awk 'END{print NR}' src/gui/app.py` returns `<= 500`.
  - All four toolchain stages pass in a single pass.
  - `test_main_entry_point_runs_event_loop`, `test_composition_root_calls_install_crash_handlers_once_with_expected_app_name`, and `test_main_calls_velopack_app_run_before_qapplication` continue to pass without modification (no observable behavior change).
- **Artifact paths:**
  - Code: `src/gui/app.py` (modified), possibly `src/gui/_crash_handler_bootstrap.py` (NEW).
  - Evidence: `evidence/qa-gates/phase8/file-sizes.md` regenerated with `wc -l` or `(Get-Content <path>).Count` (not `Measure-Object -Line`).
  - Spec checkbox: re-evaluate AC-12 after fix.

### R2 — Resolve the `_resolve_log_dir` vs `resolve_log_dir` spec/code drift (Material PARTIAL)

- **Source:** Policy audit F2 / Code review Material finding / Feature audit AC-1 PARTIAL.
- **Current state:** Spec AC-1 says `_resolve_log_dir`; implementation exposes `resolve_log_dir`. The rename is documented in plan P2-T2 as a Pyright `reportPrivateUsage` accommodation.
- **Required action:** Choose one of:
  - **Option A (preferred):** Update `spec.md` AC-1 verbatim text to `resolve_log_dir`. Update the spec only; do not move the symbol back.
  - Option B: Restore the underscore prefix in `src/gui/_crash_handler.py` and add `# pyright: ignore[reportPrivateUsage]` only at the test-import site. Risk: requires a pyright-ignore that is not currently on the python-suppressions pre-authorized list (see persistent agent memory `pyright-ignore-authorization-scope`).
- **Definition of done:**
  - Spec AC-1 text matches the public symbol name in source.
  - Pyright remains clean (no new suppressions).
- **Artifact paths:** `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md` line 202.

### R3 — Regenerate `evidence/qa-gates/phase4/file-sizes.md` with a faithful line-count command (Material PARTIAL)

- **Source:** Policy audit F3 / Code review Material finding.
- **Current state:** The artifact reports `app.py = 439` and attests AC-12 PASS. The actual count is 503; the PowerShell `Measure-Object -Line` cmdlet undercounts by counting line-terminator characters and dropping the trailing partial line.
- **Required action:** Regenerate the artifact using one of:
  - PowerShell: `(Get-Content <path>).Count`
  - Bash/WSL: `wc -l <path>`
  - Python: `sum(1 for _ in open(path))`
- **Definition of done:**
  - Artifact contains line counts matching `wc -l` / `awk NR` to within +/- 1 line.
  - Artifact accurately reflects whether each file is under or over the cap.
- **Artifact paths:** `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md` (and the post-fix counterpart under phase8 if added).

### R4 — Pin the crash-write closure bodies with direct invocation tests (Material PARTIAL, informational)

- **Source:** Policy audit F4 / Code review Material finding / Feature audit AC-10 PARTIAL (informational).
- **Current state:** `_crash_handler.py` lines 254-263 (`_make_sys_excepthook` closure), 290-303 (`_make_threading_excepthook` closure), 374-383 (`_append_traceback`) are never invoked by tests. The numeric coverage threshold (85% line / 75% branch) is met repo-wide and per file, but the actual crash-write path is unverified.
- **Required action:** Add three tests in `tests/gui/test_crash_handler.py`:
  - `test_sys_excepthook_appends_traceback_record`: build the closure via `_make_sys_excepthook(tmp_path, lambda *_: None)` with `crash_log_path` patched so `_append_traceback` writes to a `BytesIO`-backed stream; invoke with a synthetic `(ValueError, ValueError("boom"), None)` and assert the file content contains `sys.excepthook` and the traceback.
  - `test_threading_excepthook_appends_traceback_record`: same pattern using a `threading.ExceptHookArgs` instance (construct via `threading.ExceptHookArgs(...)` or a typed namedtuple).
  - `test_append_traceback_swallows_oserror`: stub the `crash_log_path.open` to raise `OSError`; assert no exception propagates and the module logger records an `exception` call.
- **Definition of done:**
  - The three closures execute under test.
  - `_crash_handler.py` missing-lines list no longer includes 254-263, 290-303, 374-383 (or the residual list is documented and accepted).
- **Artifact paths:** `tests/gui/test_crash_handler.py` (extended), `evidence/qa-gates/phase8/pytest.md` (regenerated coverage report).

## Non-Remediation Items (acknowledged, not blocking)

- Code review "Suggestion" items (top-level imports in `_crash_handler.py`, f-string concatenation, explicit connection type on `thread.quit`, `_State` frozen): minor quality nits; optional.

## Suggested Remediation Order

1. R3 (regenerate file-sizes evidence with correct command) — establishes the verifiable state for R1.
2. R1 (reduce `app.py` under 500 lines) — clears the Blocking AC-12 finding.
3. R2 (update spec AC-1 to `resolve_log_dir`) — documentation-only.
4. R4 (add closure-body tests) — last; depends on no other change.

After R1, R2, R3 land, the feature should be re-audited. R4 may be deferred to a follow-up if scope-constrained, but it is the only remaining material finding once the blockers are cleared.

## Verification Commands for the Remediator

```
awk 'END{print NR}' src/gui/app.py
wc -l src/gui/app.py
poetry run black --check .
poetry run ruff check .
poetry run pyright
poetry run pytest --cov --cov-branch --cov-report=term-missing
git diff --name-only 0b353adcd596ff450db5cfa7ca771ef22565e53a..HEAD -- pyproject.toml poetry.lock
git diff HEAD -- '*.py' | grep -E '^\+[^+]' | grep -E '#\s*(noqa|type:\s*ignore|pyright:\s*ignore)'
```
