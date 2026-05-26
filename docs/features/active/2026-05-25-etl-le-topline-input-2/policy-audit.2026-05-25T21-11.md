# Policy Audit — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature
- Base branch (resolved): `main`
- Merge-base SHA: `2d86e836f89f43df011ed7528ac8decbd82cd761`
- Head SHA: `74743671ae26e42e74e039fa5f33e90d2e4b3294`
- Range: `2d86e836f89f43df011ed7528ac8decbd82cd761..74743671ae26e42e74e039fa5f33e90d2e4b3294`
- Audit timestamp: 2026-05-25T21-11
- Auditor: feature-review agent

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: The MCP tool
> `mcp__drm-copilot__resolve_policy_audit_template_asset` (asset `template`) and the
> validator `mcp__drm-copilot__validate_orchestration_artifacts` are not available in
> this environment, and no repository policy-audit template file exists. Per the
> `policy-audit-template-usage` fail-closed guidance, this artifact is constructed
> directly with the canonical major headings. This does not affect the audit verdicts
> below, which are derived from the branch diff and from toolchain runs executed by the
> auditor.

## Executive Summary

The branch adds a single-file Python CLI (`src/normalize_le.py`) that normalizes an
Excel "LE-8 + 4" topline planning sheet into one row per business key and persists the
result to SQLite, plus three test modules and the supporting dependency/doc changes.

The only language with changed code files in the branch diff is Python. The auditor
re-ran the full Python toolchain (Black, Ruff, Pyright, Pytest with coverage) and all
four stages passed in a single clean pass. Repo-wide coverage is 100% line and 100%
branch; the coverage artifact `artifacts/python/lcov.info` is present.

Overall verdict: PASS. No Blocking findings. One non-blocking observation is recorded
in Section 8 (absence of a repo-root `quality-tiers.yml`); this is a pre-existing
repository-infrastructure gap and does not change any coverage verdict because coverage
thresholds are uniform across tiers.

## 1. General Unit Test Policy Compliance

Verdict: PASS

- Independence/Isolation: Tests are function-scoped and use `monkeypatch` for the
  SQLite and `load_source` boundaries; no shared mutable global state. Evidence:
  `tests/test_normalize_le_io.py` (`patch_connect`, `patch_load_source`).
- Determinism: No wall-clock, `sleep`, or unseeded randomness. Property tests use
  Hypothesis with bounded strategies. The module under test has no `datetime`/`time`/
  `random` usage (spec Implementation Strategy; confirmed by reading `src/normalize_le.py`).
- No temp files / no external services: Excel fixtures use `io.BytesIO`; SQLite
  round-trips use `sqlite3.connect(":memory:")` via a `PersistentConnection` whose
  `close` is neutralized. Evidence: `tests/le_fixtures.py:111-127`, docstring lines 1-10.
- Scenario completeness: positive, negative (schema mismatch, tie-out perturbation,
  FY mismatch, missing `--output`), edge (singleton key, 3+ rows, NaN-as-0,
  empty-output branch), and property-based flows present.
- AAA structure and descriptive names: each test uses Arrange/Act/Assert comments and a
  behavior-descriptive name. Evidence: `tests/test_normalize_le.py`,
  `tests/test_normalize_le_io.py`.
- Property-test density (T2 self-classified module): property tests exist for
  `coerce_sku`, `rebuild_key`, `compute_ytg`, `normalize`, and `validate_tieouts`
  (the round-trip property). Meets ">= 1 per pure function" for the pure transforms.

## 2. General Code Change Policy Compliance

Verdict: PASS

- Simplicity / separation of concerns: pure transforms (`coerce_sku`, `rebuild_key`,
  `validate_schema`, `normalize`, `compute_ytg`, `validate_tieouts`) are separated from
  I/O boundaries (`load_source`, `write_sqlite`) and CLI glue (`_build_parser`, `main`).
  Evidence: module docstring "Boundaries" section, `src/normalize_le.py:17-21`.
- Fail-fast error handling: schema and tie-out failures raise `ValueError` with
  column/row-naming messages; `main` maps `ValueError` to exit code 1; missing
  `--output` triggers argparse `SystemExit`. Evidence: `src/normalize_le.py:191-199`,
  `337-360`, `484-490`.
- File size limit (<= 500 lines): `src/normalize_le.py` is 498 lines. PASS (within
  limit, with no margin). Test files are 470 / 299 / 264 lines.
- Naming: `snake_case` functions/variables, `CONSTANT_CASE` module constants,
  `PascalCase` class (`PersistentConnection`). PASS.
- Dependencies: `pandas`, `openpyxl` runtime and `hypothesis`, `pandas-stubs` dev added
  in `pyproject.toml`; each is documented in spec "Dependency changes and rationale".
  `sqlite3` is stdlib. The dependency additions were explicitly planned (issue.md /
  spec.md) and lock file regenerated. PASS.
- I/O boundary isolation: Excel read and SQLite write are isolated; core logic is
  testable without filesystem/network. PASS.

## 3. Language-Specific Code Change Policy Compliance (Python)

Verdict: PASS

- Strong typing: all public functions carry full parameter/return type hints; module
  declares `from __future__ import annotations`. Pyright reports 0 errors/0 warnings
  (auditor run, see Appendix B).
- Suppressions: two `# pyright: ignore[reportUnknownMemberType]` directives in
  `src/normalize_le.py` (lines 230, 388) and one in `tests/le_fixtures.py` (line 87),
  each at a pandas I/O boundary where pandas-stubs resolves an unstubbed connection /
  openpyxl overload as partially unknown. Each is single-line, narrowly scoped, and
  carries an explanatory comment. These are Pyright directives, not `# type: ignore` or
  `# noqa`; the `python-suppressions` policy governs `# noqa`/`# type: ignore`. They are
  justified and compliant. Observation only.
- One `# noqa: S608 - trusted test table name` in `tests/le_fixtures.py:83` on a
  parameterized `SELECT` over a trusted test table name in test code. Consistent with
  the test-fixture rationale of the authorized S108/S105 test-only patterns; the table
  name originates from test constants, not user input. Acceptable in test code.
- Docstrings: every function/class has a Google-style docstring with Args/Returns/
  Raises/Side effects as applicable; loops and branches carry intent comments per
  `self-explanatory-code-commenting.md`. PASS.
- Logging vs print: `print` is used for the CLI tie-out summary by design (CLI tool
  output, not library logging); spec Definition of Done documents this as N/A for
  library logging. Acceptable for a CLI entry point.

## 4. Language-Specific Unit Test Policy Compliance (Python)

Verdict: PASS

- Pytest runner, `tests/test_<module>.py` layout, `parametrize` used for the
  `coerce_sku` matrix, `monkeypatch` for module attributes and `sqlite3.connect`.
- No network/DB/external-process/temp-file dependencies; in-memory only.
- Patch location is the import location used by the unit under test
  (`src.normalize_le.load_source`, `sqlite3.connect`). PASS.
- Coverage thresholds satisfied (see Section 5).

## 5. Test Coverage Detail

Verdict: PASS

Coverage artifact (Python): `artifacts/python/lcov.info` — present (auditor-confirmed,
generated 2026-05-25T21-10 and re-confirmed by the auditor's pytest run).

Auditor `pytest --cov --cov-branch` results (Appendix B):

| Scope | Line | Branch | Threshold (line>=85 / branch>=75) | Verdict |
|---|---|---|---|---|
| Repo TOTAL | 100% (133 stmts, 0 miss) | 100% (38 br, 0 part) | met | PASS |
| `src/normalize_le.py` (new file) | 100% (129 stmts, 0 miss) | 100% (36 br, 0 part) | new-file >=85/>=75 met | PASS |
| `src/calculator.py` (unchanged) | 100% | 100% | no regression | PASS |

- New-file thresholds (line >= 85%, branch >= 75%): met (100%/100%).
- No regression on changed lines: the only pre-existing module (`src/calculator.py`)
  remains at 100%/100%; baseline was 100% per
  `evidence/qa-gates/coverage-delta.md`. PASS.

Coverage verdict per language with changed files:
- Python: PASS (explicit).

## 6. Test Execution Metrics

- Total tests: 46 passed, 0 failed, 0 skipped (auditor run).
  - `tests/test_normalize_le.py`: 32 tests.
  - `tests/test_normalize_le_io.py`: 12 tests.
  - `tests/test_calculator.py`: 2 pre-existing tests.
- Runtime: ~7.1s (auditor run).
- Determinism: deterministic; no retries observed.

## 7. Code Quality Checks

| Stage | Command | Result | Verdict |
|---|---|---|---|
| Format | `poetry run black --check .` | 7 files unchanged | PASS |
| Lint | `poetry run ruff check .` | All checks passed | PASS |
| Type check | `poetry run pyright` | 0 errors, 0 warnings, 0 informations | PASS |
| Tests + coverage | `poetry run pytest --cov --cov-branch --cov-report=term-missing` | 46 passed; 100%/100% | PASS |

All stages completed in a single clean pass with no auto-fixes (no loop restart needed).

## 8. Gaps and Exceptions

- Observation (non-blocking): No `quality-tiers.yml` exists at the repository root.
  `.claude/rules/quality-tiers.md` states every project must be classified there and
  that adding an unclassified project fails CI. This branch adds the `normalize_le`
  module; the spec self-classifies it as T2 (spec.md Implementation Strategy). The
  classification file itself is absent repo-wide (it did not exist at the merge-base
  baseline either), so this is a pre-existing repository-infrastructure gap rather than
  a defect introduced by this feature. It does not change any coverage verdict because
  coverage thresholds are uniform across tiers (T1–T4). Recommend adding a repo-root
  `quality-tiers.yml` entry as repository housekeeping; not a Blocking finding for this
  PR.
- Exception: MCP template-resolution and orchestration-artifact validators are
  unavailable in this environment (see header note). Artifacts were built with the
  canonical headings and validated structurally by the auditor.

## 9. Summary of Changes

Core logic (Python):
- `src/normalize_le.py` (+498) — new CLI module.
- `tests/test_normalize_le.py` (+470) — pure-transform tests.
- `tests/test_normalize_le_io.py` (+299) — I/O / CLI tests.
- `tests/le_fixtures.py` (+264) — shared in-memory fixtures.

Configuration / docs:
- `pyproject.toml`, `poetry.lock` — pandas/openpyxl runtime, hypothesis/pandas-stubs
  dev, `normalize-le` script entry.
- `README.md` — usage section.
- `docs/features/.../*` (spec, user-story, issue, plan, promoted note, evidence) — docs.

No `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**` paths
changed; the `modified-workflow-needs-green-run` rule does not fire.

## Rejected Scope Narrowing

None. The caller prompt set the full feature-vs-base scope and did not attempt to narrow
to a plan, task, phase, file subset, or to mark any language out of scope. The audit was
performed against the full branch diff `2d86e836..74743671`.

## Evidence Location Compliance

The branch diff was scanned for files written under `artifacts/baselines/`,
`artifacts/qa/`, `artifacts/evidence/`, `artifacts/post-change/`, or
`artifacts/coverage/`. None were found. All feature evidence is written to the canonical
`docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/` scheme
(`evidence/baseline/`, `evidence/qa-gates/`). The only `artifacts/` path written is
`artifacts/python/lcov.info`, which is the language coverage artifact path mandated by
the feature-review-workflow SKILL coverage table, not an evidence artifact; it is not a
violation.

- Validator note: `validate_evidence_locations.py` is not present in this repository;
  the PreToolUse hook `.claude/hooks/enforce-evidence-locations.ps1` exists. The scan
  above was performed against the branch diff name-status output. No FAIL-level
  evidence-location findings.

## 10. Compliance Verdict

Overall: PASS

- General unit test policy: PASS
- General code change policy: PASS
- Python code change policy: PASS
- Python unit test policy: PASS
- Coverage (Python, only changed language): PASS
- Workflow green-run rule: not applicable (no matching paths changed)
- Blocking findings: 0
- Non-blocking observations: 1 (missing repo-root `quality-tiers.yml`)

Remediation: not triggered.

## Appendix A: Test Inventory

`tests/test_normalize_le.py`:
- `coerce_sku`: parametrized branch matrix (int, np.int64, integer-float, fractional
  float, np.float64 whole, NaN, None, two string codes, True, False); integer property.
- `rebuild_key`: whole-number SKU, non-numeric SKU verbatim, property.
- `validate_schema`: exact match, missing column, extra column, out-of-order.
- `load_source`: header/columns, blank-Customer drop, KEY rebuild ignoring stale value.
- `compute_ytg`: May..Dec sum, property.
- `normalize`: singleton passthrough, 2-row pair sum, 3+ rows with NaN-as-0, column
  order / no YTD-YTG, first-appearance order, Super Category/PPG quirk, non-numeric SKU
  preserved, property (row count + per-key sums).

`tests/test_normalize_le_io.py`:
- `validate_tieouts`: pass path, row-count mismatch, column-total perturbation, FY
  mismatch, property round-trip.
- `write_sqlite`: round-trip columns/rows, replace-if-exists no duplication.
- `main`: end-to-end success, missing `--output` non-zero, schema mismatch non-zero,
  custom sheet/table name.
- `print_summary`: empty-output branch omits row samples.

`tests/test_calculator.py`: 2 pre-existing tests (unchanged).

## Appendix B: Toolchain Commands Reference

All commands run from repo root with the VIRTUAL_ENV quirk prefix
(`env -u VIRTUAL_ENV poetry run ...`) per the project's Poetry virtual-env note.

```
env -u VIRTUAL_ENV poetry run black --check .
# -> All done. 7 files would be left unchanged.

env -u VIRTUAL_ENV poetry run ruff check .
# -> All checks passed!

env -u VIRTUAL_ENV poetry run pyright
# -> 0 errors, 0 warnings, 0 informations

env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
# -> 46 passed in ~7.1s
# -> src/normalize_le.py 100% line (129 stmts), 100% branch (36 br)
# -> TOTAL 100% line (133 stmts), 100% branch (38 br)
# -> Coverage LCOV written to artifacts/python/lcov.info
```
