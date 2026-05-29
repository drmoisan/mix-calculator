# Phase 2 — toolchain loop (confirmation; production landed in Phase 1)

Timestamp: 2026-05-29T10-15

## Stage 1 — Black

Command: `env -u VIRTUAL_ENV poetry run black --check src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: 2 files would be left unchanged.

## Stage 2 — Ruff

Command: `env -u VIRTUAL_ENV poetry run ruff check src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: All checks passed.

## Stage 3 — Pyright

Command: `env -u VIRTUAL_ENV poetry run pyright src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: 0 errors, 0 warnings, 0 informations.

## Stage 4 — Pytest

Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -x`

EXIT_CODE: 0

Output Summary: 27 passed; 0 failed.
