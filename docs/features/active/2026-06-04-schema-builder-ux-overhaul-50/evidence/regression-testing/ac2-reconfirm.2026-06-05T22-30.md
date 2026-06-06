# AC-2 Re-Confirmation — Auto-Selection on Activation (Cycle 3)

Timestamp: 2026-06-05T23-08
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables -v
EXIT_CODE: 0
Output Summary: 1 passed. The production activation path (build_application + real
tab_combo.currentTextChanged) with a file selected, a real worksheet selected, and a
full-match service auto-selects the matched schema ("le_like") in the LE widget dropdown
and enables the LE Import button.

## Test name proving AC-2 after the guards

- tests/gui/test_schema_discovery_wiring.py::test_ac2_full_match_through_build_application_auto_selects_and_enables

## How this proves the guards do not suppress legitimate matching

The test selects a non-blank file path and a non-blank worksheet, so neither the presenter
guard (`[P1-T1]`) nor the wiring short-circuit (`[P1-T2]`) trips. Discovery runs end-to-end
through the composition root and auto-selects the matched schema, enabling Import — the AC-2
behavior. The blank/whitespace guards added in cycle 3 only fire for the placeholder /
combo-population case (blank path or sheet), which is the crash window, not legitimate
activation.
