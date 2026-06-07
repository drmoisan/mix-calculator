# Baseline — Masking Scan

Timestamp: 2026-06-05T11-20
Command: env -u VIRTUAL_ENV poetry run python scripts/checks/scan_masked_fixtures.py
EXIT_CODE: 0
Output Summary: masking-scan: clean (no forbidden patterns found).

Scan helper: scripts/checks/scan_masked_fixtures.py (211 lines, <= 500 cap; Black/Ruff/Pyright clean).
Default target set: tests/, src/schemas/, docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/.
Forbidden patterns: explicit proprietary-name sentinels and a real-data currency numeric
signature (thousands-separated values with cents). The baseline tree is clean.
