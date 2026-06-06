# Baseline — Cap-Sensitive File Sizes (Remediation Cycle 1)

Timestamp: 2026-06-05T20-28
Command: wc -l on each cap-sensitive file
Cap: 500 lines (production/test/reusable script). Extraction-at-risk window: within 60 lines of cap (>= 440 lines).

| File | Lines | Status |
|---|---|---|
| src/gui/app.py | 497 | EXTRACTION-AT-RISK (3 below cap) |
| src/gui/widgets/schema_builder_dialog.py | 452 | EXTRACTION-AT-RISK (48 below cap) |
| src/gui/_schema_wiring.py | 403 | within risk window (97 below cap) |
| src/gui/widgets/_schema_builder_tabs.py | 241 | OK |
| src/gui/_schema_discovery_wiring.py | 124 | OK |

Decision impact:
- P4-T1: app.py at 497 lines is at-risk; provider construction must be extracted before wiring (gated by P4-T1).
- P1-T1: schema_builder_dialog.py (452) and _schema_builder_tabs.py (241) flagged for projection check before Phase 1-3 wiring.
