# Phase 6 — Produced ICO fingerprint (AC5)

Timestamp: 2026-05-29T20-30
Command: env -u VIRTUAL_ENV poetry run python -c "import hashlib,pathlib;from PIL import Image;p=pathlib.Path('packaging/velopack/icon.ico');b=p.read_bytes();im=Image.open(p);sizes=sorted({(e.width,e.height) for e in im.ico.entry});print(len(b), hashlib.sha256(b).hexdigest(), b[:4].hex(), sizes)"
EXIT_CODE: 0
Output Summary:
- File: packaging/velopack/icon.ico
- Size: 12813 bytes
- SHA256: 087fd737af5201d0ed4ed7a271d706160284dfc59ffb654e04fe8444a4cc3dcc
- Magic bytes: 00000100 (0x00 0x00 0x01 0x00 -- valid Windows ICO header)
- Frame sizes: [(16, 16), (32, 32), (48, 48), (256, 256)] -- all four expected sizes present

AC5 verified: multi-size Windows ICO container with frames at 16x16, 32x32, 48x48, and 256x256, magic bytes 0x00 0x00 0x01 0x00.
