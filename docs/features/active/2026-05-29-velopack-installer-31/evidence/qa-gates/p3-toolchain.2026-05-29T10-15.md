# Phase 3 — toolchain loop with coverage

Timestamp: 2026-05-29T10-15

## Stage 1 — Black

Command: `env -u VIRTUAL_ENV poetry run black src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: 2 files left unchanged.

## Stage 2 — Ruff

Command: `env -u VIRTUAL_ENV poetry run ruff check src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: All checks passed.

## Stage 3 — Pyright

Command: `env -u VIRTUAL_ENV poetry run pyright src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: 0 errors, 0 warnings, 0 informations.

## Stage 4 — Pytest + targeted coverage

Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -x --cov=src.build_velopack --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
- 30 tests passed; 0 failed.
- src/build_velopack.py coverage: 98% (Stmts 91, Miss 1, Branch 24, BrPart 1).
- Line coverage: 98% (>> AC15 threshold of 85%).
- Branch coverage on file: 23/24 reached = ~95.8% (>> AC15 threshold of 75%).
- Missing line: 541 (defensive `raise RuntimeError` inside `if github_token is None` guard — unreachable in practice because the upstream `args.upload` branch always populates the token or returns 2).
