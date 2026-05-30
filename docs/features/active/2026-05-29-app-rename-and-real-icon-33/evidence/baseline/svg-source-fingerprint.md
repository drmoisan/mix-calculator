# Baseline — Source SVG fingerprint

Timestamp: 2026-05-29T20-01
Command: env -u VIRTUAL_ENV poetry run python -c "from xml.etree import ElementTree as ET; ET.parse('artifacts/realgood_calculator_icon.svg')" && env -u VIRTUAL_ENV poetry run python -c "import hashlib,pathlib;print(hashlib.sha256(pathlib.Path('artifacts/realgood_calculator_icon.svg').read_bytes()).hexdigest())"
EXIT_CODE: 0
Output Summary:
- File: artifacts/realgood_calculator_icon.svg
- Size: 47010 bytes
- SHA256: 4632e39860ee686a83b3f77111d999e871499dc531222560b2c86f7a323aab42
- Root tag: {http://www.w3.org/2000/svg}svg (parses as valid XML)
