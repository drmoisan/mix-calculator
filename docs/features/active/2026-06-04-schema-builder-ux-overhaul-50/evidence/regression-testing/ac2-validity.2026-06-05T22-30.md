# AC-2 Validity After Cycle-3 Fix

Timestamp: 2026-06-05T23-08

## AC-2 (from spec.md section "Behavior", item 2; user-story.md "Acceptance Criteria")

> Activating a source tab auto-selects the best-matching schema; placeholder shown
> when none matches.

## Determination

AC-2 remains VALID and UNCHANGED by this fix.

The cycle-3 change is a defensive guard plus an error-contract alignment. It preserves AC-2
behavior for the populated-selection case:

- When a file AND a real worksheet are selected and the header matches a schema, activation
  auto-selects the matched schema and enables Import (the proceed path).
- When none matches, the `<Choose Schema>` placeholder is shown and Import stays disabled
  (the no-match path).

The guard only suppresses discovery when `path` or `sheet` is blank/whitespace-only — the
placeholder / combo-population events that fire `currentTextChanged` before a worksheet is
chosen. That window is not a legitimate AC-2 activation; it is the crash trigger reported in
the field (issue #50 cycle 3).

## Supporting test names

- AC-2 populated-selection proceed (build_application, real signal):
  tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables
- B1 wiring-level, no file selected (placeholder stays, Import disabled):
  tests/gui/test_schema_discovery_wiring.py::test_tab_activation_no_file_selected_does_not_call_reader
- B1 wiring-level, file but no worksheet (placeholder stays, Import disabled):
  tests/gui/test_schema_discovery_wiring.py::test_tab_activation_file_but_no_worksheet_never_calls_reader_blank_sheet
