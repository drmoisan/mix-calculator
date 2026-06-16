# schema-builder-ux-overhaul (Issue #72)

- Date captured: 2026-06-16
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/schema-builder-ux-overhaul/ (Issue #72)

- Issue: #72
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/72
- Last Updated: 2026-06-16
- Work Mode: full-feature

## Problem / Why

The Schema Builder dialog (`SchemaBuilderDialog` plus its tab/state/presenter
helpers) has several usability gaps and at least two tabs whose purpose is
unclear to the user. The window cannot be resized vertically, the Identity
description is a single non-wrapping line, the Derived tab uses a `|` separator
and unbracketed column references, the Columns tab shows a dtype checkmark rather
than the underlying value and offers no way to inspect a specific source row, and
the Preview tab does not render a result table. The Key and Dedup tabs duplicate
or obscure behavior that the user believes should be expressed through the
Derived and Columns tabs.

## Proposed Behavior

Distinct work items from the request:

1. **Window resize (vertical).** The dialog can be minimized/maximized but cannot
   be resized vertically. Allow vertical (and continued horizontal) resizing.
   Current state: `apply_schema_builder_window_flags` sets `Qt.Window` +
   min/max/close hints and a default size; the vertical-resize block is likely a
   fixed size policy or layout constraint to investigate.

2. **Identity tab — wrapping description.** The description is a single-line
   `QLineEdit`. Replace it with a multi-line widget that wraps text and grows or
   shrinks its box with the window size.

3. **Derived tab — separator and bracketing.**
   - Replace the visible `|` separator between name and expression with ` = `
     (render and parse as `name = expression`).
   - Column names referenced in an expression are surrounded with `[` on the left
     and `]` on the right; the comma separator between columns sits outside the
     brackets (e.g. `[col a], [col b]`).
   - In the "New derived column" dialog, double-clicking a name in the available-
     columns list inserts that name, bracketed, into the expression input.

4. **Columns tab — row chooser and value display.**
   - Add a row-number chooser. Selecting a row number changes the assigned values
     shown for every field to that source row's values.
   - Keep the existing blue assignment object, but to its right show the assigned
     source value for the chosen row instead of the current dtype checkmark.

5. **Key tab — purpose unclear (design question).** The user does not understand
   what the Key tab does and asks whether it is another expression builder. Their
   proposed direction: use the Derived tab to create the key, and the Columns tab
   to assign the Key. Requires research into current Key-tab behavior and a design
   decision; may remove or repurpose the Key tab.

6. **Dedup tab — purpose unclear (design question).** The user asks whether, once
   columns are assigned on the Columns tab, Dedup should simply group by the
   non-value column assignments. Requires research into current Dedup semantics
   and a design decision.

7. **Preview tab — does not work.** The Preview tab should render the resulting
   table built from the prior tabs' configuration. If a required input is missing,
   the Preview should call out specifically what is missing.

## Acceptance Criteria (early draft)

- [ ] The schema-builder window can be resized vertically as well as horizontally.
- [ ] The Identity description wraps across multiple lines and resizes with the window.
- [ ] The Derived tab renders/parses `name = expression` and brackets column refs with the comma outside the brackets.
- [ ] Double-clicking a column name in the New-derived dialog inserts the bracketed name into the expression.
- [ ] The Columns tab has a row-number chooser that updates every field's displayed value; the value is shown to the right of the blue object instead of a checkmark.
- [ ] The Key tab purpose is resolved (removed/repurposed) per the agreed design; key authored via Derived and assigned via Columns where decided.
- [ ] The Dedup tab purpose is resolved (groupby on non-value assignments) per the agreed design.
- [ ] The Preview tab renders the result table from the configured tabs and reports specific missing inputs.

## Constraints & Risks

- PySide6/Qt GUI; tests must run under `QT_QPA_PLATFORM=offscreen` with the CI
  system libraries (see orchestrator memory `pyside6-ci-system-libs`).
- 500-line file cap applies to all production and test files; the schema-builder
  modules are already split to stay under it. New behavior may need further
  extraction.
- Items 5 and 6 are design decisions, not pure mechanical changes; they may alter
  the persisted schema model (`KeySpec`, `DedupPolicy`) and round-trip behavior.
  Research must confirm feasibility and scope before planning.
- GUI acceptance tests must drive the real user path and bundled data, not a
  synthetic-only alias path (orchestrator memory `ac-must-reproduce-real-user-path`,
  `gui-activation-seam-guards`).
- Preview rendering must not regress confidentiality masking of source values.

## Test Conditions to Consider

- [ ] Unit coverage areas: window flags/size policy, identity description widget, derived render/parse with `=` and brackets, columns row chooser + value display, preview rendering with complete and missing inputs.
- [ ] Integration scenarios: open builder against bundled schema + masked preview slice, configure tabs, render preview; double-click insert path in the derived dialog.
- [ ] CLI/API examples: not applicable (GUI feature).

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/schema-builder-ux-overhaul/` folder from the template