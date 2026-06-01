# `pipeline-gui-hardening-schema-select` — User Story (Issue #48)

- Issue: #48
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/48
- Owner: drmoisan
- Work Mode: full-feature
- Status: Draft
- Last Updated: 2026-06-01
- Spec: `spec.md` (same folder)

## Story Statement

- As a pipeline operator using the mix-calculator GUI, I want all decisions and
  errors to appear in the GUI rather than a terminal, so that I can run the
  pipeline without watching a console or losing diagnostic messages.
- As a pipeline operator loading a partial-year ("8+4") workbook, I want the AOP
  validation to accept correct year-to-date and year-to-go totals, so that valid
  data is not rejected while genuinely inconsistent data is still flagged.
- As a pipeline operator importing a non-standard source file, I want to select
  or build an import schema per source tab, so that I can map files the
  known-file loaders do not already recognize.

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

## Personas & Scenarios

- Persona: Pipeline operator (analyst running the mix calculator)
  - Who they are: an analyst who loads the LE, AOP, and SKU lookup sources into
    the GUI, runs the pipeline, and reviews the derived output.
  - What they care about: completing a run without dropping to a terminal,
    seeing clear errors when an import fails, and trusting that validation
    flags real data problems rather than valid partial-year layouts.
  - Constraints: works from packaged builds and from `poetry run`; handles
    confidential workbook figures that must not leak into committed artifacts.
  - Goals and frustrations: wants the GUI to be self-contained; the current
    behavior forced terminal interaction, hid errors in the status bar, crashed
    on a partial import, and rejected a valid 8+4 workbook.

- Scenario: Loading a partial-year ("8+4") workbook
  - Who is acting: the pipeline operator.
  - Trigger: the operator opens the GUI and imports the LE, AOP, and SKU lookup
    sources.
  - Steps: the operator selects each source file and worksheet; the GUI
    auto-selects a matching schema per tab where one is found; the operator
    imports each source. If the AOP source carries a diverging KEY, a Qt modal
    asks whether to keep the existing KEY or rebuild it, defaulting to "Keep
    existing".
  - Obstacles/decisions: if an import fails, a modal shows the full diagnostic
    message, a status-bar summary appears, and the Run action stays disabled
    until all three sources import successfully. The AOP validation accepts the
    8+4 sheet (YTD covers Jan..Apr because YTG covers May..Dec).
  - Expected outcome: with all three sources imported, the operator runs the
    pipeline and reviews the derived output, with no terminal interaction and no
    cascading error.

## Acceptance Criteria

The authoritative, numbered acceptance criteria are maintained in `spec.md`
(AC-1 through AC-15). The user-facing summary below maps to those criteria.

- [ ] No stdin prompt ever occurs in a GUI session; the KEY-mismatch decision is
      a Qt modal defaulting to "Keep existing" (trust), applied to both the AOP
      and LE import paths. (spec AC-1, AC-2, AC-3)
- [ ] Packaged builds open no console window; interaction is dialog-only, and a
      developer console is for logs only. (spec AC-4)
- [ ] A partial import leaves Run disabled and produces no cascading `KeyError`;
      Run is permitted only when all three required keys are present. (spec AC-5,
      AC-6)
- [ ] All import and run errors are surfaced to the user via a modal plus a
      status-bar summary. (spec AC-7)
- [ ] `validate_aop` accepts the 8+4 workbook (YTD = Jan..Apr when YTG present),
      leaves full-year sheets unaffected, and still rejects genuine identity
      violations. (spec AC-8, AC-9, AC-10)
- [ ] Each source tab shows a schema dropdown with auto-select, a
      `<Choose Schema>` placeholder when none matches, and a working "Build new
      schema" button; schema selection is additive to the known-file loaders.
      (spec AC-11, AC-12, AC-13, AC-14)
- [ ] No confidential workbook figures appear in any committed artifact.
      (spec AC-15)

## Non-Goals

- Do NOT relax or remove AOP validation; WS5 corrects the checked identity only.
- Do NOT change the known-file loader defaults; schema selection is additive.
- Do NOT alter the financial transform math.
- No new third-party dependencies; no changes to branch protection or required
  checks.
