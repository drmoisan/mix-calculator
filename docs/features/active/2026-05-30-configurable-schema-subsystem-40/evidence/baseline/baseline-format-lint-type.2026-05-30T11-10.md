# Baseline — Format / Lint / Type (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

## black --check
Command: `poetry run black --check .`
EXIT_CODE: 0
Output Summary: All done. 166 files would be left unchanged.

## ruff check
Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: All checks passed (E402 currently suppressed by 9 `# noqa: E402` directives that this cycle removes).

## pyright (strict)
Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.
