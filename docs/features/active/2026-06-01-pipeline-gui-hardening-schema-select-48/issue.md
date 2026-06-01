# pipeline-gui-hardening-schema-select (Issue #48)

- Date captured: 2026-06-01
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/pipeline-gui-hardening-schema-select/ (Issue #48)

- Issue: #48
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/48
- Last Updated: 2026-06-01
- Work Mode: full-feature

## Problem / Why

A `poetry run mix-pipeline-gui` run against a real partial-year ("8+4") workbook
failed in several distinct ways, and the failure handling was poor. Five defects
plus one missing capability were identified (research:
`artifacts/research/pipeline-gui-robustness-diagnosis.md`):

- WS1a — A `trust`/`overwrite` KEY-mismatch prompt was read from the terminal
  (stdin), not the GUI. The GUI never injects the `etl_key` prompt seam, so the
  loaders fall back to the `prompt` policy and the built-in `input()`.
- WS1b — A console window opens on launch because `mix-pipeline-gui` is a
  `console_scripts` entry point.
- WS3 — After the AOP import failed, the pipeline still ran and raised a
  cascading `KeyError: 'aop'`, because `pipeline_presenter.can_run()` only
  checks that *some* table imported, not that all three required keys
  (`LE`, `aop`, `sku_lu`) are present.
- WS4 — Every error reaches only the one-line status bar; long, diagnostic
  messages are effectively invisible. No modal error surface is wired.
- WS5 (root data defect, confirmed via openpyxl) — `validate_aop` asserts
  `YTD == sum(Jan..Dec)`, but in an 8+4 sheet YTD is year-to-date through April.
  Over 1522 rows: `YTD == sum(Jan..Apr)` and `YTG == sum(May..Dec)` and
  `YTD + YTG == sum(Jan..Dec)` all hold for every row; the current check passes
  only the 648 rows where YTG is zero. The module already defines
  `YTG_MONTHS = MONTHS[4:]`, so the YTD check is internally inconsistent with the
  YTG split. This is a latent validation bug, not bad data.
- WS2 (missing capability) — There is no per-tab import-schema selector, although
  the matching/discovery/builder machinery already exists.

## Proposed Behavior

- All user interaction goes through Qt dialogs. The KEY-mismatch decision is a
  modal (Keep existing / Rebuild), defaulting to Keep existing; no stdin prompt.
- Packaged builds launch with no console window; developer runs may keep a
  console for logs only (never for interaction).
- A failed import aborts the run cleanly and surfaces a diagnostic
  `QMessageBox.critical` modal (plus a status-bar summary); the Run action is
  gated until all three sources import successfully.
- `validate_aop` validates the correct identity for partial-year sheets: when a
  `YTG` column is present, `YTD == sum(non-YTG months)` and
  `YTG == sum(YTG_MONTHS)`; when absent, `YTD == sum(all months)`. Validation is
  corrected, not relaxed.
- Each source tab has an import-schema dropdown that auto-selects a matching
  schema on tab activation, shows a `<Choose Schema>` placeholder when none
  matches, and a "Build new schema" button that opens the existing schema
  builder.

## Acceptance Criteria (early draft)

- [ ] No stdin prompt ever occurs in a GUI session; the KEY-mismatch decision is
      a Qt modal defaulting to Keep existing (trust).
- [ ] Packaged builds open no console window; interaction is dialog-only.
- [ ] A failed import disables Run and shows a diagnostic modal; no cascading
      `KeyError` can occur from a partial import.
- [ ] All import/run errors are surfaced to the user via a modal plus status bar.
- [ ] `validate_aop` accepts the 8+4 workbook (YTD = Jan..Apr when YTG present)
      and still rejects genuine identity violations; full-year sheets unaffected.
- [ ] Each source tab shows a schema dropdown with auto-select, `<Choose Schema>`
      placeholder, and a working "Build new schema" button.

## Constraints & Risks

- `src/gui/app.py` is at 499/500 lines and `pipeline_presenter.py` at 490/500;
  the 500-line cap is enforced hard, so additions require extraction first.
- WS5 touches financial validation logic (correct, do not weaken); confidential
  workbook figures must never be committed.
- Schema selection wires previously-unused scaffolding (`import_with_schema`,
  `discover_schema`); ensure the known-file loaders remain the default path.

## Test Conditions to Consider

- [ ] Unit: corrected `validate_aop` identity (YTG present vs absent; genuine
      violation still fails); `can_run()` gate with partial imports; error-modal
      surfacing; KEY-mismatch dialog seam.
- [ ] Integration: GUI import-failure path shows modal and disables Run; schema
      auto-select / placeholder / build-new-schema flow (offscreen Qt).
- [ ] Packaging: entry-point / console-mode change for packaged builds.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create active feature folder from the template