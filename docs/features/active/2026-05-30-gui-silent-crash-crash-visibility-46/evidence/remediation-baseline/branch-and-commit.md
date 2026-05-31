# Remediation Baseline — Branch and Commit

- Timestamp: 2026-05-31T02-43
- Command:
  - `git rev-parse --abbrev-ref HEAD`
  - `git rev-parse HEAD`
- EXIT_CODE: 0
- Output Summary:
  - Branch: `bug/gui-silent-crash-crash-visibility-46`
  - HEAD: `666e84a32aa158a4554cb0305c5695512e35f0cd`

## In-scope file list

- `src/gui/app.py`
- `src/gui/_crash_handler.py`
- `tests/gui/test_crash_handler.py`
- `tests/gui/test_app_composition.py`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/spec.md`
- `docs/features/active/2026-05-30-gui-silent-crash-crash-visibility-46/evidence/qa-gates/phase4/file-sizes.md`
