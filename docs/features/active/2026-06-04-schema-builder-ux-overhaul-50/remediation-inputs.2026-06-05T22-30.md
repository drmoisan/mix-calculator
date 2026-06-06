# Remediation Inputs — schema-builder-ux-overhaul (Issue #50) — Cycle 3 Entry

- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main`; Head: `fd8a022` (+ audit/docs commits); PR #51 (open, CI green)
- Source: user-reported runtime crash (post-PR), not a CI failure.
- Timestamp: 2026-06-05T22-30
- Consolidated blocking_count (entry): 1 blocking defect with two coupled gaps.

## Symptom

Running `mix-pipeline-gui` and activating a source tab raises, repeatedly:

```
File "src/gui/_schema_discovery_wiring.py", line 121, in _on_tab_activated
  presenter.on_schema_discovery(widget.current_path(), widget.current_sheet())
File "src/gui/presenters/source_selection_presenter.py", line 233, in on_schema_discovery
  rows = self._reader.read_sheet_preview(path, sheet, max_rows=_HEADER_PREVIEW_ROWS)
File "src/gui/services/workbook_reader.py", line 151, in read_sheet_preview
  worksheet = workbook[sheet_name]
KeyError: 'Worksheet  does not exist.'
```

The empty worksheet name in the message (`'Worksheet  does not exist.'`) shows the
sheet argument is the empty string. The auto-selection wiring (Decision 9, AC-2)
fires `currentTextChanged` on tab-combo activation/population before a worksheet
is selected, so discovery runs with a blank `sheet` (and possibly a blank `path`).

## Root Cause

### B1 (primary) — discovery is not guarded against empty path/sheet
- `_on_tab_activated` (`src/gui/_schema_discovery_wiring.py:111-121`) calls
  `presenter.on_schema_discovery(...)` unconditionally on every
  `currentTextChanged`, including when the widget has no file and/or no worksheet
  selected (placeholder / combo-population events).
- `SourceSelectionPresenter.on_schema_discovery`
  (`src/gui/presenters/source_selection_presenter.py:224-249`) guards
  `self._schema_service is None` and empty `rows`, but does NOT no-op when `path`
  or `sheet` is empty/blank before calling the reader.

### B2 (coupled) — reader/presenter error-type contract mismatch
- `WorkbookReader.read_sheet_preview` (`src/gui/services/workbook_reader.py:124-162`)
  does `workbook[sheet_name]`, which openpyxl raises as `KeyError` for an unknown
  or blank sheet (documented in its own docstring, lines 141-144).
- `on_schema_discovery` only catches `ValueError` (line 236), so the `KeyError`
  propagates uncaught and crashes the handler. Even a valid file with a stale or
  nonexistent sheet name would crash, not just the blank-sheet case.

## Remediation-Required Findings (blocking)

### B1 — Guard schema discovery against empty/blank path or sheet
- Make tab-activation discovery a no-op when there is no file selected or no
  worksheet selected (blank/whitespace `path` or `sheet`). Place the guard so the
  reader is never called with a blank sheet. Prefer guarding inside
  `on_schema_discovery` (so the presenter contract is safe for any caller), and
  optionally also short-circuit in `_on_tab_activated`.
- Acceptance: an integration test drives tab activation (the production
  `currentTextChanged` path / `build_application` wiring) with (a) no file and
  (b) a file but no worksheet selected, asserting NO exception is raised, the
  reader is not called with a blank sheet, and the dropdown stays on the
  `<Choose Schema>` placeholder with Import disabled.

### B2 — Make the unknown/blank-sheet reader error non-crashing
- Resolve the error-contract mismatch so a missing/blank worksheet does not crash
  discovery. Either have `read_sheet_preview` raise `ValueError` (consistent with
  the presenter's reader-error policy and `on_file_selected`/`on_render_tab`) when
  the sheet is absent, or have `on_schema_discovery` also handle `KeyError`. Keep
  one clear contract; update the reader docstring to match.
- Acceptance: a unit test asserts the chosen contract (reader raises `ValueError`
  for an unknown sheet, OR the presenter routes a `KeyError` to `view.show_error`
  without propagating); discovery with a nonexistent sheet name shows an error
  rather than crashing.

## Verification on Re-Review

- Confirm the production activation path cannot raise out of `_on_tab_activated`
  for any combination of empty/blank path, empty/blank sheet, or nonexistent
  sheet, proven by integration tests that exercise the real wiring (not isolated
  unit mocks that pre-set a valid sheet).
- Full toolchain green (Black/Ruff/Pyright/Pytest); coverage line>=85% /
  branch>=75% no regression; masking scan clean; no new file over 500 lines.
- AC-2 (auto-selection on activation) re-confirmed against the integrated tests.
