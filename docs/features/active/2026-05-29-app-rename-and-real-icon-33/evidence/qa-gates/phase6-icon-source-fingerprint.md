# Phase 6 — Icon source SVG fingerprint (AC4)

Timestamp: 2026-05-29T20-30
Command: env -u VIRTUAL_ENV poetry run python -c "import shutil;shutil.copy('artifacts/realgood_calculator_icon.svg','packaging/velopack/icon-source.svg')" && env -u VIRTUAL_ENV poetry run python -c "import hashlib,pathlib;b=pathlib.Path('packaging/velopack/icon-source.svg').read_bytes();print(hashlib.sha256(b).hexdigest(), len(b))"
EXIT_CODE: 0
Output Summary:
- File: packaging/velopack/icon-source.svg
- Size: 47010 bytes (matches baseline)
- SHA256: 4632e39860ee686a83b3f77111d999e871499dc531222560b2c86f7a323aab42 (equals Phase 0 baseline -> byte-exact copy of artifacts/realgood_calculator_icon.svg)
- Head bytes: `<svg ` (starts with `<svg`, so AC4 requirement "valid SVG (starts with `<svg`)" is satisfied)

AC4 verified.
