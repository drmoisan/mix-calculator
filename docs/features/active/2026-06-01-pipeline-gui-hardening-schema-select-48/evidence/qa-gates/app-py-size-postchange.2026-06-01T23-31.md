# app.py Size — Post-change Verification (P3-T3)

Timestamp: 2026-06-01T23-31

File: src/gui/app.py
Line count: 500

Result: 500 <= 500 cap satisfied. The Phase 3 wiring added an import line plus a
single call site (a local `_source_views` list and one `populate_schema_lists`
call). The population logic itself lives in src/gui/_schema_list_wiring.py
(62 lines), so app.py remains at or under the 500-line cap.

Command: wc -l src/gui/app.py
