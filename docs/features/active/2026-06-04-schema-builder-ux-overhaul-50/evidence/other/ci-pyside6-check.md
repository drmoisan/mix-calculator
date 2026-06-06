# CI PySide6 Provisioning Check (P14-T1 / P14-T2)

Timestamp: 2026-06-05T13-25

## P14-T1 — Inspection result

Workflow file inspected: `.github/workflows/_python-quality.yml`.

The pytest job already provisions all required PySide6 Ubuntu system libraries and
sets the offscreen platform:

- Lines 47–55 (step "Install Qt platform runtime libraries") install all five
  libs: `libegl1`, `libgl1`, `libxkbcommon0`, `libdbus-1-3`, `libfontconfig1`.
- Lines 81–85 (step "Test with coverage (Pytest)") set `QT_QPA_PLATFORM: offscreen`
  for the pytest run.

Both the required libs and the env var are present.

## P14-T2 — Outcome

EXIT_CODE: SKIPPED — already present.

The CI workflow already installs the PySide6 libs and sets
`QT_QPA_PLATFORM=offscreen`, so no workflow edit is made. Because no
`scripts/benchmarks/**` or workflow file is modified by this feature, the
`modified-workflow-needs-green-run` rule is not triggered.
