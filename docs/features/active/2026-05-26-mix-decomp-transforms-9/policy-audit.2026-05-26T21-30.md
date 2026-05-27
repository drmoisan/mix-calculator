# Policy Compliance Audit — mix-decomp-transforms (Issue #9)

- Timestamp: 2026-05-26T21-30
- Reviewer: feature-review agent
- Base branch (resolved): `main` @ `4c1e8faf8166c2ff1da680fb83dd3c4998adc187`
- Head: `feature/mix-decomp-transforms-9` @ `2932427f0dc91f59c03553c8b393dce0c79c2dc1`
- Range: `4c1e8faf8166c2ff1da680fb83dd3c4998adc187..2932427f0dc91f59c03553c8b393dce0c79c2dc1`
- Work mode: `full-feature` (from `issue.md`)
- Scope: full feature-vs-base branch diff (44 files, +5918 lines)

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: the review-artifact MCP template tools
> (`resolve_policy_audit_template_asset`) are not available in this environment.
> Per the documented fallback, this artifact uses the canonical major headings
> and Appendix B command reference directly.

## Languages With Changed Files

- Python: changed (10 new `src/` modules, 8 new test modules). Coverage mandatory.
- TypeScript: zero changed files — N/A.
- PowerShell: zero changed files — N/A.
- C#: zero changed files — N/A.

## Rejected Scope Narrowing

None. The caller prompt supplied the full set of new `src/` modules and tests
and did not attempt to narrow scope to a plan, task, phase, or file subset, nor
to mark any language's coverage as out of scope. The audit covers the full
feature-vs-base diff.

## Verdict Summary

| Policy area | Verdict | Evidence |
|---|---|---|
| Confidentiality (HARD constraint) | PASS | No real customer/SKU/category/price/discount values; only fabricated literals |
| File size limit (<= 500 lines) | PASS | Largest file 388 lines (`_mix_transforms_helpers.py`) |
| Black formatting | PASS | `poetry run black --check .` exit 0, 37 files unchanged |
| Ruff lint | PASS | `poetry run ruff check .` exit 0, all checks passed |
| Ruff/Pyright suppressions | PASS | Zero `noqa`/`type: ignore`/`pyright: ignore` in new src or test files |
| Pyright (strict) | PASS | `poetry run pyright` exit 0, 0 errors / 0 warnings / 0 informations |
| Pytest + coverage | PASS | 185 passed; line 100% / branch 100% (verified live) |
| Coverage (Python) | PASS | Repo-wide 100% line / 100% branch; all new files 100%/100% |
| I/O routing through `pandas_io` | PASS | All reads/writes via `read_table`/`write_table`/`read_excel_sheet` |
| Loader reuse (no duplication) | PASS | `mix_pipeline` reuses `normalize_le`, `load_aop`, `load_skulu` |
| `quality-tiers.yml` classification | PASS | 10 new T2 entries added for the new modules |
| Evidence location compliance | PASS | No diff files under non-canonical `artifacts/{baselines,qa,evidence,coverage}/` |
| `modified-workflow-needs-green-run` | N/A (not triggered) | No `.github/workflows/**`, `scripts/benchmarks/**`, `.github/actions/**` changes |

Overall: PASS. No Blocking findings.

## Confidentiality (Hard Constraint) — PASS

The hard confidentiality constraint prohibits real customer names, SKU
descriptions, category names, SKU numbers, prices, and discounts in any source
file, test, fixture, or doc. `US`/`Canada` country values are explicitly not
secret.

Evidence:

- Customer literals in tests are fabricated: `Acme Foods`, `Globex Market`,
  `Initech Grocers` (the spec-sanctioned fabricated set).
- SKU codes are synthetic placeholders: `SKU-001`, `SKU-002`, `SKU-003`,
  `SKU-200`, `SKU-300`.
- SKU Description values are placeholders: `Widget A`, `Widget B`.
- Category values are placeholders: `Category X`, `Category Y`.
- No dollar-amount literals (`$nn.nn`) appear in `src/` or `tests/`
  (`rg '\$\s*[0-9]+\.[0-9]'` returned no matches).
- The `$`-bearing strings in source and docs are schema column names
  (`Off Invoice $`, `Trade Spend $`, `Net-Revenue $`, `Calc Net Price Impact`),
  not data values. Column/attribute names and classification labels are schema,
  not secret, per the spec.
- The large feature doc (`2026-05-26-mix-decomp-transforms-9.md`) and `README.md`
  contain only formula/column-name references and an explicit confidentiality
  note ("No real SKU descriptions, category names, product numbers, sales
  prices, or discounts").
- `src/load_skulu.py` includes an explicit confidentiality docstring confirming
  `SKU Description` and `Category` are confidential and only schema labels appear
  in the module.

No suspected confidential data leakage detected.

## File Size Limit (<= 500 lines) — PASS

All production, test, and reusable-script files are within the 500-line limit.
Line counts (`wc -l`):

| File | Lines |
|---|---|
| src/_mix_transforms_helpers.py | 388 |
| src/mix_rollups.py | 317 |
| src/mix_pipeline.py | 250 |
| src/_mix_rollups_helpers.py | 224 |
| src/mix_lookups.py | 220 |
| src/mix_transforms.py | 210 |
| src/load_skulu.py | 143 |
| src/mix_rate_impacts.py | 123 |
| src/mix_pipeline_run.py | 97 |
| src/mix_q1.py | 91 |
| tests/test_mix_transforms.py | 374 |
| tests/test_mix_lookups.py | 360 |
| tests/test_mix_rollups.py | 338 |
| tests/test_mix_pipeline.py | 270 |
| tests/test_load_skulu.py | 172 |
| tests/test_mix_pivots.py | 165 |
| tests/test_mix_rate_impacts.py | 159 |
| tests/test_mix_q1.py | 120 |

The decomposition into `_mix_transforms_helpers.py`, `_mix_rollups_helpers.py`,
`mix_pipeline_run.py`, and `test_mix_pivots.py` keeps every file comfortably
under the limit. This is a different posture than the issue #2 test files that
clustered near 500 lines.

## Python Toolchain Gates

All gates verified live on HEAD `2932427` (`env -u VIRTUAL_ENV` prefix per the
repo Poetry virtual-env quirk):

- Black: `poetry run black --check .` -> exit 0; "37 files would be left unchanged." PASS.
- Ruff: `poetry run ruff check .` -> exit 0; "All checks passed!" PASS.
- Pyright (strict): `poetry run pyright` -> exit 0; "0 errors, 0 warnings, 0 informations." PASS.
- Pytest + coverage: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  -> exit 0; "185 passed"; TOTAL 100% line (881 stmts, 0 miss), 100% branch
  (192 branch, 0 partial). PASS.

### Suppressions — PASS

No `# noqa`, `# type: ignore`, or `# pyright: ignore` suppressions appear in any
new `src/` module or new test file (`Grep` over `src/*.py` and `tests/test_mix*.py`,
`tests/test_load_skulu.py` returned no matches). No suppression-authorization
review is required.

## Coverage Verification (Python) — PASS

The Python coverage artifact `artifacts/python/lcov.info` exists and was
regenerated by the live pytest run. Coverage was verified live (not only from
prior evidence).

- Repo-wide: 100% line, 100% branch — exceeds 85% line / 75% branch thresholds.
- New files (all at 100% line / 100% branch):
  - src/load_skulu.py (32 stmts, 4 branch)
  - src/mix_transforms.py (43 stmts, 14 branch)
  - src/_mix_transforms_helpers.py (97 stmts, 26 branch)
  - src/mix_lookups.py (43 stmts, 4 branch)
  - src/mix_rate_impacts.py (21 stmts, 0 branch)
  - src/mix_rollups.py (61 stmts, 0 branch)
  - src/_mix_rollups_helpers.py (49 stmts, 8 branch)
  - src/mix_q1.py (20 stmts, 4 branch)
  - src/mix_pipeline.py (68 stmts, 4 branch)
  - src/mix_pipeline_run.py (20 stmts, 0 branch)
- Modified files: `quality-tiers.yml` and `README.md` are not executable Python
  and carry no coverage obligation. No pre-existing Python module was modified.
- No regression on changed lines: pre-existing modules (`normalize_le`,
  `load_aop`, `etl_*`, `pandas_io`, `calculator`) remain at 100%/100%, matching
  the Phase-0 baseline recorded in `coverage-delta.2026-05-26T20-00.md`.

Coverage verdict for Python: PASS.

## I/O Boundary and Loader Reuse — PASS

- `src/load_skulu.py` reads via `src.pandas_io.read_excel_sheet` and writes via
  `src.pandas_io.write_table`; the rename/cast/country-map logic is pure.
- `src/mix_pipeline.py` reads via `src.pandas_io.read_table` and writes via
  `src.pandas_io.write_table`; the `sqlite3.connect` calls open the connection
  passed to the typed boundary, consistent with the existing loader pattern.
- The pure transform modules (`mix_transforms`, `mix_lookups`,
  `mix_rate_impacts`, `mix_rollups`, `mix_q1`, and the `_*_helpers`) contain no
  Excel/SQLite I/O (Grep for read/write APIs returned no matches).
- `mix_pipeline._import_sources` reuses `normalize_le.load_source/normalize/
  validate_tieouts/write_sqlite`, `load_aop.load_aop/persist_aop`, and
  `load_skulu.load_skulu/persist_skulu` rather than re-implementing ingestion.

## quality-tiers.yml — PASS

Ten new T2 entries were added (the spec named seven modules; the implementation
split two helper modules and a pipeline-run module out for the 500-line limit
and classified each, which is consistent with the same T2 rationale):
`load_skulu`, `mix_transforms`, `_mix_transforms_helpers`, `mix_lookups`,
`mix_rate_impacts`, `mix_rollups`, `_mix_rollups_helpers`, `mix_q1`,
`mix_pipeline`, `mix_pipeline_run`. Each new module is classified; no
unclassified project remains in the diff.

## Evidence Location Compliance — PASS

- The branch diff contains no files written under `artifacts/baselines/`,
  `artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`.
  (`git diff --name-only ... | rg '^artifacts/(baselines|qa|evidence|coverage)/'`
  returned no matches.)
- Feature evidence is written to the canonical
  `docs/features/active/2026-05-26-mix-decomp-transforms-9/evidence/<kind>/`
  paths (`baseline/`, `qa-gates/`, `other/`).
- The Python validator `scripts/validate_evidence_locations.py` referenced by
  the agent contract is absent in this repository; only the PowerShell
  PreToolUse hook `.claude/hooks/enforce-evidence-locations.ps1` is present.
  The diff scan above is the substituted evidence. No violation found.

## Appendix B — Command Reference

| Check | Command | Exit | Result |
|---|---|---|---|
| Format | `env -u VIRTUAL_ENV poetry run black --check .` | 0 | 37 files unchanged |
| Lint | `env -u VIRTUAL_ENV poetry run ruff check .` | 0 | All checks passed |
| Type | `env -u VIRTUAL_ENV poetry run pyright` | 0 | 0/0/0 |
| Tests + Coverage | `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | 0 | 185 passed; 100% line / 100% branch |
| File sizes | `wc -l <src and test files>` | 0 | max 388 lines |
| Suppression scan | `Grep noqa\|type: ignore\|pyright: ignore` | — | no matches |
| Confidentiality scan | `rg` for customer/SKU/category/price literals | — | only fabricated values |
| Evidence-location scan | `git diff --name-only ... \| rg '^artifacts/(baselines\|qa\|evidence\|coverage)/'` | — | no matches |
| Workflow-rule trigger | `git diff --name-only ... \| rg '.github/workflows/\|scripts/benchmarks/\|.github/actions/'` | — | no matches |
