# Feature Audit: Pipeline GUI Hardening and Schema Selection (Issue #48)

**Audit Date:** 2026-06-01
**Feature Folder:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
**Base Branch:** `main`
**Head Branch:** `feature/pipeline-gui-hardening-schema-select-48`
**Work Mode:** `full-feature`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`)
- **Head branch/commit:** `feature/pipeline-gui-hardening-schema-select-48` (commit `c526e4f1cf988c02fcfbc2571249148327ad765e`)
- **Merge base:** `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/evidence/**`
  - Additional evidence: reviewer-reproduced `poetry run black --check . / ruff check . / pyright / pytest --cov --cov-branch`; `poetry run coverage report`
- **Feature folder used:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
- **Requirements source:** `spec.md` (AC-1..AC-15) and `user-story.md` (per `full-feature` work mode)
- **Work mode resolution note:** `issue.md` and `spec.md` both carry `- Work Mode: full-feature`. Per the work-mode contract, `spec.md` and `user-story.md` are the authoritative AC sources.
- **Scope note:** Full branch-vs-base audit. PR-context artifacts were present and current for the head SHA; no narrowing was applied. The branch touches Python only.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `spec.md` — primary (numbered AC-1..AC-15, checkbox-backed)
- `user-story.md` — secondary (user-facing summary mapping to the spec ACs, checkbox-backed)

### Acceptance criteria (from spec.md)

1. AC-1: In any GUI session, no stdin prompt occurs. The KEY-mismatch decision is resolved through a Qt modal; the `PipelineService` import path never reaches the `etl_key`/loader stdin `input()` path. (WS1a)
2. AC-2: The KEY-mismatch Qt modal presents "Keep existing" (trust) and "Rebuild" (overwrite) options and defaults to "Keep existing"; the selected option maps to the corresponding loader policy. (WS1a)
3. AC-3: The LE import path receives the same dialog-based KEY-mismatch handling as the AOP path and never reaches stdin. (WS1a)
4. AC-4: Packaged builds open no console window (Nuitka `--windows-console-mode=disable` and/or a `gui`-style entry point); developer `poetry run` launches may retain a console for logs only, with no stdin interaction in any launch mode. (WS1b)
5. AC-5: `pipeline_presenter.can_run()` returns `True` only when all three required import keys (`LE`, `aop`, `sku_lu`) are present (or a derived-table set from a prior successful run exists) and no job is running. (WS3)
6. AC-6: After a partial import failure (one or two of the three sources failed), Run is disabled and no cascading `KeyError` (for example `KeyError: 'aop'`) can be produced by `run_pipeline`. (WS3)
7. AC-7: Every import and run error is surfaced through a `QMessageBox.critical` modal AND a status-bar summary, routed through the `MainWindowPipelineView` error surface. (WS4)
8. AC-8: `validate_aop` accepts the partial-year ("8+4") sheet: when a `YTG` column is present, it asserts `YTD == sum(months not in YTG_MONTHS)` (Jan..Apr) AND `YTG == sum(YTG_MONTHS)` (May..Dec). (WS5)
9. AC-9: `validate_aop` leaves full-year sheets unaffected: when no `YTG` column is present, it asserts `YTD == sum(MONTHS)` (Jan..Dec). (WS5)
10. AC-10: `validate_aop` still rejects genuine identity violations: a row where the corrected identity does not hold within `TIEOUT_TOL` raises `ValueError`. Validation is corrected, not relaxed. (WS5)
11. AC-11: Each source tab shows an import-schema dropdown that auto-selects a matching schema on tab activation when `discover_schema` returns `action="proceed"`. (WS2)
12. AC-12: When no schema matches (`discover_schema` returns `action="resolve"`), the dropdown shows the `<Choose Schema>` placeholder and does not auto-select a schema. (WS2)
13. AC-13: Each source tab has a working "Build new schema" button that opens the existing schema builder dialog. (WS2)
14. AC-14: Schema selection is additive: the known-file loaders (`import_le`/`import_aop`/`import_skulu`) remain the default import path and their default behavior is unchanged. (WS2)
15. AC-15: No confidential workbook figures appear in any committed artifact (spec, tests, fixtures, or evidence); WS5 tests use synthetic values. (WS5)

### From user-story.md (user-facing summary)

- No stdin prompt in a GUI session; Qt modal defaulting to "Keep existing", applied to AOP and LE. (spec AC-1, AC-2, AC-3)
- Packaged builds open no console window; dialog-only interaction. (spec AC-4)
- A partial import leaves Run disabled and produces no cascading `KeyError`. (spec AC-5, AC-6)
- All import/run errors surfaced via a modal plus a status-bar summary. (spec AC-7)
- `validate_aop` accepts the 8+4 workbook, leaves full-year sheets unaffected, and rejects genuine violations. (spec AC-8, AC-9, AC-10)
- Per-tab schema dropdown with auto-select, placeholder, build-new-schema button; additive. (spec AC-11..AC-14)
- No confidential workbook figures in any committed artifact. (spec AC-15)

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC-1 no stdin; KEY decision via Qt modal | PASS | `pipeline_service.import_le`/`import_aop` forward `is_tty=never_tty`, `prompt=no_stdin_prompt`; `no_stdin_prompt` raises if reached. | `poetry run pytest tests/gui/test_pipeline_service_key_seam.py` | Loaders cannot reach `input()`. |
| 2 | AC-2 modal "Keep existing"/"Rebuild", default Keep existing | PASS | `_key_mismatch_dialog.build_key_mismatch_resolver`: `setDefaultButton(keep_button)`; True->`"trust"`, False->`"overwrite"`. | `poetry run pytest tests/gui/test_key_mismatch_dialog.py` | Default and mapping tested. |
| 3 | AC-3 LE path same dialog handling, no stdin | PASS | `import_le` forwards the same resolver/seam trio to `normalize_le.load_source`. | `poetry run pytest tests/gui/test_pipeline_service_key_seam.py` | AOP + LE both covered. |
| 4 | AC-4 packaged build no console | PASS | `build_exe.resolve_nuitka_command` includes `--windows-console-mode=disable`. | `poetry run pytest tests/test_build_exe.py` | Verified by build-config inspection per spec testing strategy; no runtime console assertion required. |
| 5 | AC-5 can_run requires all three keys (or derived) and not running | PASS | `import_dispatch.required_keys_present`: `all(key in imported ...) or bool(derived)`, `and not is_running`; `can_run` delegates. | `poetry run pytest tests/gui/test_pipeline_presenter_run_gate.py` | |
| 6 | AC-6 partial import disables Run; no cascading KeyError | PASS | Import-error callbacks recompute Run via `can_run()`; gate False on partial import so `run_pipeline` is unreachable. | `poetry run pytest tests/gui/test_pipeline_presenter_run_gate.py` | Closes `KeyError: 'aop'`. |
| 7 | AC-7 error via QMessageBox.critical modal AND status bar | PASS | `MainWindowPipelineView.show_error` calls `show_dialog_error` (QMessageBox.critical) then `set_status` with a truncated summary. | `poetry run pytest tests/gui/test_main_window_view.py` | Both surfaces driven. |
| 8 | AC-8 8+4 sheet: YTD=Jan..Apr, YTG=May..Dec | PASS | `build_per_row_checks` returns YTD=non-YTG months and YTG=`YTG_MONTHS` when YTG present; `validate_aop` checks both. | `poetry run pytest tests/test_load_aop_helpers.py` | |
| 9 | AC-9 full-year unaffected: YTD=Jan..Dec when no YTG | PASS | `build_per_row_checks` returns `{"YTD": MONTHS, ...}` when YTG absent. | `poetry run pytest tests/test_load_aop_helpers.py` | |
| 10 | AC-10 genuine violations still raise; corrected not relaxed | PASS | Three negative-path tests raise `ValueError` (bad YTD with YTG, bad YTG, bad full-year YTD); `total_vs_months_violations` unchanged. | `poetry run pytest tests/test_load_aop_helpers.py` | Non-Goal honored. |
| 11 | AC-11 dropdown auto-selects on proceed | PASS | `source_selection_presenter.on_schema_discovery`: on `action=="proceed"` calls `view.set_selected_schema(...)`. | `poetry run pytest tests/gui/test_source_selection_presenter.py` | |
| 12 | AC-12 resolve leaves `<Choose Schema>` placeholder | PASS | On `action=="resolve"` no `set_selected_schema` call; combo first item is `<Choose Schema>`. | `poetry run pytest tests/gui/test_source_selection_presenter.py` `tests/gui/test_source_input_widget.py` | |
| 13 | AC-13 working Build-new-schema button opens builder | PASS | `SourceInputWidget` build button emits `build_schema_requested`; `_schema_wiring.open_schema_builder` shows the dialog. | `poetry run pytest tests/gui/integration/test_behavioral_schema_import.py` | |
| 14 | AC-14 schema selection additive; loaders unchanged | PASS | `import_le`/`import_aop`/`import_skulu` unchanged as the default path; `import_with_schema` is a separate additive method. | `poetry run pytest tests/gui/test_pipeline_service.py` | |
| 15 | AC-15 no confidential figures; synthetic test values | PASS | `tests/test_load_aop_helpers.py` and `tests/aop_fixtures.py` use synthetic `range(1,13)`-derived values; no committed workbook figures (diff scan). | `git diff 1df33019..c526e4f1 -- tests/` | Confirmed by inspection of fixtures, tests, and evidence. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 15 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. After PR creation, confirm the CI run against the head SHA is green (standard S9 gate; this feature touches no CI-gate paths so `modified-workflow-needs-green-run` does not require a pre-merge run).
2. Optional manual smoke of the packaged Nuitka build to visually confirm no console window (AC-4 is satisfied by build-config inspection per the spec's stated strategy).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules:
- All 15 spec.md criteria were evaluated PASS. In `spec.md` they were already represented as `[x]` by the executor; no further change was required there.
- The `user-story.md` summary checkboxes (which map to the spec ACs) were unchecked `[ ]`; since every mapped spec AC is PASS and the items are checkbox-format, they were checked off in `user-story.md`.

### AC Status Summary

- Source: `spec.md` (AC-1..AC-15) and `user-story.md` (summary)
- Total AC items: 15 (spec) + 7 (user-story summary)
- Checked off (delivered): 15 (spec, already checked) + 7 (user-story, checked off this review)
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `spec.md` | 15 | 15 | 0 | Checkbox-backed; already `[x]` from executor. |
| `user-story.md` | 7 | 7 | 0 | Checkbox-backed summary mapping to spec ACs; checked off this review. |
