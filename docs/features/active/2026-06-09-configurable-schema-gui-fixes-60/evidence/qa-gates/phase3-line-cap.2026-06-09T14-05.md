# Phase 3 — 500-Line Cap Scan (Issue #60)

Timestamp: 2026-06-09T14-05

Command: wc -l src/gui/widgets/source_input_widget.py src/gui/widgets/_source_input_button_wiring.py src/gui/_schema_wiring.py src/gui/_schema_discovery_wiring.py tests/gui/test_source_input_widget.py tests/gui/test_edit_schema_wiring.py
EXIT_CODE: 0

Output Summary (per-file line counts; all <= 500):
- src/gui/widgets/source_input_widget.py: 498 lines (<= 500) — OK (explicit confirmation: source_input_widget.py <= 500)
- src/gui/widgets/_source_input_button_wiring.py: 305 lines (<= 500) — OK
- src/gui/_schema_wiring.py: 417 lines (<= 500) — OK
- src/gui/_schema_discovery_wiring.py: 245 lines (<= 500) — OK
- tests/gui/test_source_input_widget.py: 482 lines (<= 500) — OK
- tests/gui/test_edit_schema_wiring.py: 212 lines (<= 500) — OK (new)

Extraction notes:
- The Edit Schema button surface pushed source_input_widget.py to 535 lines.
  Control construction and layout assembly were extracted into
  _source_input_button_wiring.py (new SourceInputControls dataclass,
  build_source_input_controls, assemble_source_input_layout), restoring the
  widget to 498 lines.
- Adding wire_edit_schema_buttons to _schema_wiring.py pushed it to 504 lines
  (over the cap). The function and its placeholder constant were relocated into
  the already-classified _schema_discovery_wiring.py (its caller), bringing
  _schema_wiring.py to 417 and _schema_discovery_wiring.py to 245. No new
  unclassified production module was created.

Full Python loop re-passed after both extractions: black clean, ruff clean,
pyright 0 errors, pytest 1023 passed, coverage TOTAL unchanged from baseline
(44 missed lines / 54 partial branches — no regression).
