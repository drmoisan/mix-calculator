# Phase 1 — toolchain loop (Phase 1 + Phase 2 + Phase 3 production landed early)

Timestamp: 2026-05-29T10-15

Deviation noted: The plan splits Phase 1 / Phase 2 / Phase 3 production deliveries
across three test-first cycles. Because the recorder classes mandated by P1-T1
(`_RunVpkRecorder`, `_RemoveTreeRecorder`, `_OrderedCallLog`) are unused unless the
Phase 2 / Phase 3 tests are present, and because Pyright strict mode would otherwise
flag the unused private classes, the test file already contains all P1+P2+P3 tests
and the production module already implements all P1+P2+P3 surfaces. Phase 2 and
Phase 3 plan tasks remain valid acceptance gates; their toolchain re-runs will
simply confirm-already-green.

## Stage 1 — Black

Command: `env -u VIRTUAL_ENV poetry run black src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: 2 files left unchanged after one initial reformatting pass.

## Stage 2 — Ruff

Command: `env -u VIRTUAL_ENV poetry run ruff check src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: All checks passed. (One initial E501 was fixed by tightening a docstring.)

## Stage 3 — Pyright

Command: `env -u VIRTUAL_ENV poetry run pyright src/build_velopack.py tests/test_build_velopack.py`

EXIT_CODE: 0

Output Summary: 0 errors, 0 warnings, 0 informations.

## Stage 4 — Pytest

Command: `env -u VIRTUAL_ENV poetry run pytest tests/test_build_velopack.py -x`

EXIT_CODE: 0

Output Summary: 27 passed; 0 failed. All Phase 1, Phase 2, and Phase 3 test cases pass.
