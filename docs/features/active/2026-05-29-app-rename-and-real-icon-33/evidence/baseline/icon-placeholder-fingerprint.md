# Baseline — Placeholder ICO fingerprint

Timestamp: 2026-05-29T20-01
Command: env -u VIRTUAL_ENV poetry run python -c "import hashlib,pathlib;b=pathlib.Path('packaging/velopack/icon.ico').read_bytes();print(hashlib.sha256(b).hexdigest(),b[:4].hex())"
EXIT_CODE: 0
Output Summary:
- File: packaging/velopack/icon.ico
- Size: 1402 bytes (placeholder; will be replaced in Phase 6)
- SHA256: 2dee984e71d535c223ecc4a28d0846c233d99c0c217afc0b8b0ccb687bb2b6ff
- Magic bytes: 00000100 (valid ICO header)
