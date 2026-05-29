# Phase 4 — PIL py.typed marker probe

Timestamp: 2026-05-29T20-15
Command: env -u VIRTUAL_ENV poetry run python -c "import PIL,pathlib;p=pathlib.Path(PIL.__file__).parent / 'py.typed';print(p, p.is_file())"
EXIT_CODE: 0
Output Summary: py.typed marker present at .venv/Lib/site-packages/PIL/py.typed (True). Pillow ships type stubs. Decision for P5-T9: do NOT add `# type: ignore[import-untyped]` on the PIL import.
