# Baseline — E402 / sys.path.insert Inventory (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

Command:
- `poetry run ruff check . --select E402`
- `git grep -n "noqa: E402" -- tests`
- `git grep -n "sys.path.insert" -- tests`

EXIT_CODE:
- ruff E402: 0 (passes because the `# noqa: E402` directives suppress the findings)
- git grep noqa: 0 (matches found)
- git grep sys.path.insert: 0 (matches found)

Output Summary:
9 `# noqa: E402` directives across 6 test files, and 6 fixture-tied `sys.path.insert` lines.

`# noqa: E402` occurrences (9):
- tests/gui/integration/test_behavioral_schema_import.py:35 (aop_fixtures)
- tests/gui/integration/test_behavioral_schema_import.py:36 (le_fixtures)
- tests/test_schema_loader_core.py:34 (aop_fixtures)
- tests/test_schema_loader_core.py:35 (le_fixtures)
- tests/test_schema_loader_derived.py:32 (le_fixtures)
- tests/test_schema_loader_integration.py:28 (aop_fixtures)
- tests/test_schema_loader_integration.py:29 (le_fixtures)
- tests/test_schema_loader_parity_aop.py:29 (aop_fixtures)
- tests/test_schema_loader_parity_le.py:30 (le_fixtures)

Fixture-tied `sys.path.insert` lines (6):
- tests/gui/integration/test_behavioral_schema_import.py:33 (parents[2])
- tests/test_schema_loader_core.py:32 (parent)
- tests/test_schema_loader_derived.py:30 (parent)
- tests/test_schema_loader_integration.py:26 (parent)
- tests/test_schema_loader_parity_aop.py:27 (parent)
- tests/test_schema_loader_parity_le.py:28 (parent)

Additional: one lazy in-function `import aop_fixtures` at tests/test_schema_loader_derived.py:154 depends on the same sys.path.insert and must also be converted (per plan F1).
