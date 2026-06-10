# Baseline — File Sizes (Issue #62, Cycle 1)

Timestamp: 2026-06-10T12-24

Output Summary (line counts of at-risk files, 500-line cap):
- src/gui/_schema_discovery_wiring.py: 245 lines
- src/gui/widgets/schema_builder_dialog.py: 493 lines (closest to cap; high risk for Fix C)
- src/gui/widgets/_schema_builder_tabs.py: 275 lines
- src/gui/presenters/source_selection_presenter.py: 379 lines

All four files are under the 500-line cap at baseline. schema_builder_dialog.py at 493 has only 7 lines of headroom; Fix C will extract a helper if it would reach or exceed 500.
