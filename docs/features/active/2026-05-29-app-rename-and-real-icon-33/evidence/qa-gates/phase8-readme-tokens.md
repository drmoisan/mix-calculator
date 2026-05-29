# Phase 8 — README token check (AC9)

Timestamp: 2026-05-29T20-43
Command: env -u VIRTUAL_ENV poetry run python -c "import pathlib;t=pathlib.Path('packaging/velopack/README.md').read_text();print(all(s in t for s in ['MixCalculator','MixCalculator.exe','Mix Calculator','icon-source.svg','convert_icon.py','Pillow']))"
EXIT_CODE: 0
Output Summary: True. The updated README contains all required tokens: `MixCalculator`, `MixCalculator.exe`, `Mix Calculator`, `icon-source.svg`, `convert_icon.py`, `Pillow`. AC9 verified.

Sections rewritten:
- Pack identity table: `--packId` is now `MixCalculator`, `--mainExe` is `MixCalculator.exe`.
- Icon section: placeholder description removed; now records that the ICO is generated from `icon-source.svg` via `convert_icon.py`.
- New top-level section `## Icon source and regeneration`: documents the source file, converter, exact regeneration command, the Pillow dev dependency note, and the produced ICO frame sizes / magic bytes.
- Outputs section: `mix-calculator-*` filenames replaced with `MixCalculator-*`; release name updated to `Mix Calculator <version>`.
