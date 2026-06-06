# File-size compliance (P5-T4, AC-7)

Timestamp: 2026-06-06T12-50

Command: for each file, `(Get-Content <file>).Count` (PowerShell physical lines)

EXIT_CODE: 0

Output Summary (all <= 500 lines):
- src/etl_key.py: 313
- src/normalize_le.py: 450  (was 495 pre-change; extraction kept it under cap)
- src/_normalize_le_columns.py: 166  (new module)
- src/load_aop.py: 396
- src/gui/pipeline_service.py: 493
- src/gui/_key_mismatch_seam.py: 85
- src/gui/_key_mismatch_dialog.py: 159
- src/gui/_key_mismatch_bridge.py: 187  (new module)
- src/gui/app.py: 500  (exactly at cap; restructured comments to stay <= 500)

All nine changed/added source files are <= 500 physical lines. AC-7 satisfied.
