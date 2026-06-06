# Feature Audit: key-mismatch-dialog-thread-fix (#52)

**Audit Date:** 2026-06-06
**Feature Folder:** `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52`
**Base Branch:** `main`
**Head Branch:** `fix/key-mismatch-dialog-thread-fix-52`
**Work Mode:** `full-bug`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `5e659f2` merge-base)
- **Head branch/commit:** `fix/key-mismatch-dialog-thread-fix-52` (commit `1e49546`)
- **Merge base:** `5e659f2`
- **Evidence sources:**
  - Primary: reviewer `git diff main...HEAD` and toolchain runs at 2026-06-06T12-26
  - Secondary baseline diff: `git log main..HEAD` (single commit 1e49546)
  - Feature evidence: `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/evidence/**`
  - Additional evidence: `artifacts/research/key-mismatch-dialog-thread-fix-52.md`
- **Feature folder used:** `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52`
- **Requirements source:** `spec.md` (full-bug -> spec.md only; mirrored in issue.md)
- **Work mode resolution note:** `issue.md` line 10 declares `- Work Mode: full-bug`. Per the AC-source rules, full-bug resolves to `spec.md` only.
- **Scope note:** Full branch diff vs main. No PR context artifacts were stale; the single-commit branch was diffed directly. No scope narrowing applied.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `spec.md` — only source (full-bug)

### Acceptance criteria

1. AC-1: With a threaded (off-UI-thread) runner and a diverging KEY, the KEY-mismatch dialog is shown on the GUI thread and neither button choice produces the `QBasicTimer::stop` cross-thread warning or a crash.
2. AC-2: The dialog displays 2-3 `(source KEY, computed KEY)` example pairs taken from the diverging rows.
3. AC-3: No dialog appears when the source KEY matches the rebuilt pattern or when there is no KEY column; the import proceeds.
4. AC-4: "Keep existing" maps to `trust` and is the default button; "Rebuild" maps to `overwrite`.
5. AC-5: The resolver contract carries example pairs and `resolve_key` invokes the resolver only on divergence; `PipelineService` passes the resolver callable into the loaders (no eager invocation).
6. AC-6: The CLI `--key-mismatch` stdin path (`decide_key_action`) is unchanged and its tests still pass.
7. AC-7: All changed/added source files remain <= 500 lines (notably `normalize_le.py`).
8. AC-8: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Threaded runner + diverging KEY: dialog on GUI thread, no crash/QBasicTimer | PASS | `app.py:318` builds resolver with GUI `window` -> `KeyMismatchBridge` constructed on GUI thread; `pipeline_service.py:301,331` forward callable to loaders; bridge marshals via `Qt.ConnectionType.QueuedConnection` and blocks worker on `threading.Event`; same-thread guard avoids deadlock | `poetry run pytest tests/gui/test_key_mismatch_bridge.py` | `test_cross_thread_path_marshals_to_gui_thread`, `test_same_thread_guard_calls_ask_directly_without_event`, `test_cross_thread_exception_is_surfaced_on_worker` all pass |
| 2 | Dialog shows 2-3 (source, computed) example pairs | PASS | `_collect_diverging_examples` (`etl_key.py:128-159`, limit 3) -> `resolve_key` passes to resolver -> `_qmessagebox_ask` renders `_format_examples` into body (`_key_mismatch_dialog.py:94-96`) | `poetry run pytest tests/test_etl_key.py tests/gui/test_key_mismatch_dialog.py` | `test_collect_diverging_examples_*` (order/truncate/empty), `test_qmessagebox_renders_example_pairs`, `test_resolver_forwards_examples_to_ask` |
| 3 | No dialog when KEY matches or no KEY column; import proceeds | PASS | `resolve_key` matching and no-KEY-column branches return before invoking resolver; loaders forward resolver only | `poetry run pytest tests/test_etl_key.py tests/gui/test_pipeline_service_key_seam.py` | `test_resolve_key_resolver_not_invoked_when_matching`, `test_resolve_key_resolver_not_invoked_when_no_key_column`; forwarding tests assert `resolver.calls == []` on no-divergence path |
| 4 | "Keep existing" -> trust and default button; "Rebuild" -> overwrite | PASS | `_qmessagebox_ask` sets "Keep existing" as accept-role default; resolver maps `True->trust`, `False->overwrite` (`_key_mismatch_dialog.py:115+`) | `poetry run pytest tests/gui/test_key_mismatch_dialog.py` | `test_qmessagebox_default_button_is_keep_existing`, `test_resolver_maps_keep_existing_to_trust`, `test_resolver_maps_rebuild_to_overwrite` |
| 5 | Resolver carries examples; invoked only on divergence; service passes callable (no eager call) | PASS | Contract `Callable[[list[tuple[str,str]]], str]`; `pipeline_service.py:301,331` forward `resolver=self._key_mismatch_resolver` (callable, not result); eager `self._key_mismatch_resolver()` calls removed | `poetry run pytest tests/gui/test_pipeline_service_key_seam.py tests/gui/integration/test_behavioral_composition.py` | `test_import_le_forwards_injected_resolver_callable`, `test_import_aop_forwards_injected_resolver_callable`, `test_build_application_injects_resolver_callable` |
| 6 | CLI `decide_key_action` stdin path unchanged; tests pass | PASS | `decide_key_action` body unchanged (docstring-only edit); `resolve_key` falls back to it when `resolver is None`; loaders default `resolver=None` | `poetry run pytest -k "prompt or tty or key_mismatch or stdin or decide_key"` -> 9 passed | `test_resolve_key_resolver_none_preserves_cli_path` plus existing CLI tests |
| 7 | All changed/added source files <= 500 lines | PASS | normalize_le.py 450 (was 495; extracted constants/`resolve_le_columns` to new `_normalize_le_columns.py` 166); all <= 500; app.py exactly 500 | `awk 'END{print NR}'` per file | `evidence/qa-gates/filesize-compliance.md`; reviewer enumeration matches |
| 8 | Full toolchain pass; coverage >= 85% line / >= 75% branch; no regression on changed lines | PASS | Black clean, Ruff clean, Pyright 0 errors; pytest 834 passed; changed-module coverage 100% (app.py 99%, pre-existing line 297); repo line 99.49% / branch 96.70% | `poetry run black --check`, `ruff check`, `pyright`, `pytest --cov --cov-branch` | No regression on changed lines (executor coverage-delta evidence corroborated) |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 8 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Optional: add a regression note or guard for overlapping concurrent imports sharing the single bridge instance (see code-review MINOR-1); non-blocking.

---

## Acceptance Criteria Check-off

All eight AC items are checkbox-backed and were already marked `[x]` by the executor in
both `spec.md` and `issue.md`. The reviewer verified each as PASS; no source-file change
was required (all already checked).

### AC Status Summary

- Source: `docs/features/active/2026-06-06-key-mismatch-dialog-thread-fix-52/spec.md`
- Total AC items: 8
- Checked off (delivered): 8
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 8 | 8 | 0 | Checkbox-backed; authoritative for full-bug |
| `issue.md` | 8 | 8 | 0 | Checkbox-backed mirror; not the authoritative source for full-bug |

No source-file checkbox change was made because all items were already checked `[x]` and
all were verified PASS by the reviewer.
