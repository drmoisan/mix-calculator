# schema-builder-ux-overhaul — Spec

- **Issue:** #72
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-16
- **Status:** Approved (design decisions resolved)
- **Version:** 1.0

## Overview

Issue #72 is a usability follow-up on the drag-and-drop Schema Builder delivered
in issue #50/#62 (`SchemaBuilderDialog` plus its tab/state/presenter helpers).
Eight work items refine the dialog's resize behavior, the Identity, Derived, and
Columns tabs, clarify the Key and Dedup tabs, and make the Preview tab render a
result table. Research findings are in
`artifacts/research/schema-builder-ux-overhaul-72.md`.

## Resolved Design Decisions

These decisions were confirmed by the owner before planning:

- **D-1 (Bracket convention).** Bracketed column references `[Name]` in derived
  expressions are a **display-only** convention. On entry/storage they are
  stripped to `col("Name")` before reaching the formula engine; on display they
  are re-added around known column names. The `FormulaEvaluator`/`asteval`
  grammar is **not** modified.
- **D-2 (Key tab → Option C).** The Key tab is **simplified to a multi-select of
  the declared canonical columns** that compose the key, replacing the
  drag-and-drop + Generic Text token UI. The `KeySpec`/`KeyPart` model and the
  loader's key resolution are **unchanged**: the selected columns become ordered
  `column-ref` parts, joined by a default literal-text separator. No new model
  role, no serialization change, no loader change.
- **D-3 (Dedup tab → Option B).** A new **"auto" dedup mode** is added: when
  selected, the loader groups by all `dimension`-role columns and sums all
  `measure`-role columns, with **no explicit discriminator required**. The
  existing `none`/`collapse`/`aggregate` modes and the LE schema's explicit
  `select_from`/discriminator behavior are **preserved unchanged**. The
  `DedupPolicy` invariant is relaxed only for the new `auto` mode.

## Behavior

1. **Window resize (vertical).** The dialog is a fully resizable top-level window
   (vertical and horizontal) with standard min/max/close controls. Fix the
   window-flag combination that suppresses the drag-resize grip and set a sane
   `minimumSize` so the user can size below the 900x700 default.

2. **Identity tab — wrapping description.** Replace the single-line `QLineEdit`
   description with a `QPlainTextEdit` that wraps text and expands/contracts
   vertically with the window. `get_identity`/`set_identity` keep their
   `tuple[str, str, str]` / three-`str` contract; only the internal control type
   and accessor calls change.

3. **Derived tab — separator and bracketing.**
   - Render and parse derived rows as `name = expression` (replacing `name|expression`).
   - In displayed expressions, known column references are wrapped as `[Name]`,
     with the comma separator between references outside the brackets
     (e.g. `[col a], [col b]`). On store/validate, `[Name]` is stripped to
     `col("Name")` per D-1.
   - In the "New derived column" dialog, double-clicking an available column name
     inserts the bracketed name at the cursor in the expression input.

4. **Columns tab — row chooser and value display.**
   - A row-number chooser (spinner) selects a source row index `0..len(rows)-1`
     from the masked preview slice.
   - For the chosen row, each canonical row displays, to the right of the blue
     assignment object, the assigned source column's value for that row instead
     of the dtype checkmark. Values come from the already-masked
     `PreviewSlice.rows`; no new I/O and no unmasked values are shown.

5. **Key tab (D-2).** A multi-select list of declared canonical columns. Selecting
   columns composes the ordered key (`column-ref` parts joined by a default
   separator). The SKU-coercion checkbox is retained. Round-trips through
   `KeySpec` unchanged.

6. **Dedup tab (D-3).** The mode control offers `auto` (new), `aggregate`,
   `collapse`, `none`. When `auto` is selected the discriminator control is not
   required; the loader derives the groupby from `dimension` roles and sums
   `measure` roles. Other modes are unchanged.

7. **Preview tab.** The Preview tab renders the result table produced by applying
   the in-progress schema to the masked preview slice. It is triggered when the
   user navigates to the Preview tab (or via an explicit refresh). When a required
   input is missing or the schema fails to assemble, the tab shows a specific
   message describing what is missing (sourced from the existing
   `SchemaValidationError`/loader errors), rather than rendering nothing. Rendering
   uses a tabular widget (`QTableWidget`/`QTableView`), not a plain label.

## Constraints & Risks

- PySide6/Qt GUI; tests run under `QT_QPA_PLATFORM=offscreen` with the CI system
  libraries (orchestrator memory `pyside6-ci-system-libs`).
- 500-line file cap applies to all production and test files. `_columns_tab_drag.py`
  is at the cap (498 lines) — item 4 requires extracting a helper module rather
  than adding in place. `schema_builder_dialog.py` is at 500 lines — items 2/3/7
  must be replacements or extracted helpers, not net additions.
- D-1 keeps the formula grammar unchanged; bracket handling is isolated to a UI
  display/format helper.
- D-3 relaxes the `DedupPolicy` invariant only for the new `auto` mode; the LE
  schema path (explicit discriminator/`select_from`) must not regress.
- GUI acceptance tests must drive the real user path and masked preview slice, not
  a synthetic-only alias path (memory `ac-must-reproduce-real-user-path`,
  `gui-activation-seam-guards`).
- Preview rendering must not regress confidentiality masking of source values.

## Acceptance Criteria

- [x] **AC-1** The schema-builder window can be resized vertically and horizontally and retains min/max/close controls; the user can size below the default.
- [x] **AC-2** The Identity description is a multi-line widget that wraps text and grows/shrinks vertically with the window; identity get/set round-trips multi-line text.
- [x] **AC-3** Derived rows render and parse as `name = expression`; an existing `name|expression` is no longer produced.
- [x] **AC-4** Displayed derived expressions wrap known column references as `[Name]` with the comma separator outside the brackets; stored/validated expressions use `col("Name")` and the formula engine grammar is unchanged.
- [x] **AC-5** In the New-derived dialog, double-clicking an available column name inserts the bracketed name at the cursor in the expression input.
- [x] **AC-6** The Columns tab has a row-number chooser; changing it updates each canonical row to show the chosen source row's assigned value to the right of the blue object instead of the dtype checkmark; only masked values are shown.
- [x] **AC-7** The Key tab is a multi-select of declared canonical columns; selecting columns composes the key and round-trips through `KeySpec` with the model/loader unchanged.
- [x] **AC-8** The Dedup tab offers an `auto` mode; selecting it does not require a discriminator, and the assembled/loaded schema groups by `dimension` columns and sums `measure` columns; existing modes and the LE explicit path are unchanged.
- [x] **AC-9** The Preview tab renders the result table from the configured tabs against the masked preview slice using a tabular widget.
- [x] **AC-10** When a required input is missing or assembly fails, the Preview tab shows a specific message identifying what is missing rather than rendering nothing.
- [x] **AC-11** Full toolchain passes (Black → Ruff → Pyright → Pytest) with coverage >= 85% line / >= 75% branch and no regression on changed lines; all production and test files remain <= 500 lines.

## Definition of Done

- [x] All acceptance criteria AC-1..AC-11 met and mapped to tests.
- [x] Behavior verified under `QT_QPA_PLATFORM=offscreen`.
- [x] Unit + integration tests added/updated; GUI tests drive the real user path with a masked preview slice.
- [x] Edge cases covered: blank/None preview slice (Preview message), invalid schema assembly (specific missing message), names with spaces in bracket round-trip, `auto` dedup with no discriminator.
- [x] Docs/feature folder artifacts updated.
- [x] Toolchain pass completed (format → lint → type-check → test) in a single clean pass.

## Out of Scope / Deferred

- Full "key authored as a derived column + new `key` column role" (Key tab Option
  B). Deferred as a separate issue if still desired; high model/loader/serialization
  risk.
- Removing the Dedup tab entirely (Option C). Not pursued due to LE `select_from`
  regression risk.
