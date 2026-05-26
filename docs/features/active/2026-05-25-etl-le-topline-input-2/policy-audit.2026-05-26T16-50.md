# Policy Compliance Audit — etl-le-topline-input (Issue #2)

- Artifact type: policy-audit
- Timestamp: 2026-05-26T16-50
- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature
- Reviewer: feature-review agent
- Scope: full branch diff `feature/etl-le-topline-input-2` vs base `main`
- Base branch (resolved): `main`
- Merge-base SHA (resolved via `git merge-base main HEAD`): `03eb801de63e5f39e18c59e8d96706eafde3857c`
- Head SHA: `636c493f6dca28b7a83a1f7069e1dba881ec6e4a`
- Review trigger: re-audit after a defect fix for a real-data tie-out failure (commit `636c493`)

> Template resolution: `MCP_TEMPLATE_RESOLUTION_UNAVAILABLE`. The MCP template
> tools (`resolve_policy_audit_template_asset`) and a repo-side template fallback
> are not present in this environment. Per the workflow fail-closed guidance, this
> artifact is authored directly with the canonical major headings.

## 1. Scope and Baseline

The audit scope is the full branch diff against the resolved base branch `main`,
not any plan, task, or caller-supplied subset.

Note on merge-base: the caller supplied merge-base SHA `2d86e836...`, which is the
prior bootstrap-merge commit recorded in the session-start git snapshot. The
authoritative merge-base computed by `git merge-base main HEAD` is
`03eb801de63e5f39e18c59e8d96706eafde3857c`, which also matches the refreshed PR
context artifacts (`artifacts/pr_context.summary.txt`). This audit uses the
git-computed and PR-context-confirmed merge-base `03eb801`. The discrepancy does
not change scope: the head SHA and the set of changed files are identical under
either base because `2d86e83` is an ancestor of `03eb801` on `main`.

Changed-file languages in the branch diff: **Python only** (`src/*.py`,
`tests/*.py`). No TypeScript, PowerShell, or C# files changed. No
`.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**` paths
changed.

Changed Python source (added):
- `src/le_totals.py` (95 lines) — NEW; the defect fix.
- `src/normalize_le.py` (495 lines) — NEW.
- `src/le_columns.py` (204 lines) — NEW.
- `src/le_key.py` (262 lines) — NEW.
- `src/pandas_io.py` (169 lines) — NEW.

Changed Python tests (added):
- `tests/test_normalize_le.py` (532 lines) — NEW.
- `tests/test_normalize_le_io.py` (428 lines) — NEW.
- `tests/le_fixtures.py` (343 lines) — NEW.
- `tests/test_le_key.py` (209 lines) — NEW.
- `tests/test_le_columns.py` (168 lines) — NEW.

Change under review since the prior PASS (`policy-audit.2026-05-26T14-32.md`):
a defect fix that adds `src/le_totals.py` (`fill_blank_totals`,
`total_vs_months_violations`), calls `fill_blank_totals` in `load_source` before
collapse, and adds per-row `Qn == sum(its months)` checks to `validate_tieouts`,
with corresponding tests.

## 2. Rejected Scope Narrowing

No caller instruction attempted to narrow scope below the full feature-vs-base
audit. The caller explicitly directed "Determine full diff scope yourself vs
`main`; do not narrow scope," which is consistent with the scope invariant. No
verbatim narrowing text to record.

## 3. Confidentiality Compliance (BLOCKING gate)

The upstream source workbook is confidential. This section records the
verification that no real or confidential data was persisted in the repository.

| Check | Verdict | Evidence |
|---|---|---|
| No real customer names in tracked src/tests | PASS | `git grep` of `636c493` for `customer="..."` returns only fabricated names: `A`, `Alpha`, `Zeta`, `CustA`, `CustB`, `Acme Foods`, `Globex Market`, `Initech Grocers`. The three multi-word names are the obviously-fabricated placeholders specified by the caller brief. |
| No real PPG / financial code literals | PASS | PPG values are abstract codes: `P`, `PX`, `PY`, `PPG-A/B/C`, `PPGX`, `PPGZ`, `PPG_VALUE`, `PPG_VALUE`. |
| No real financial figures | PASS | `git grep` for 6+ digit / large-decimal numeric literals in `src/` and `tests/` returns none; test numerics are small synthetic vectors (e.g. `[1.0]*12`, `2.0,4.0,...`). |
| Confidential `.xlsx`/PowerQuery/`.db` not tracked | PASS | `git ls-files artifacts/` returns empty. `git check-ignore artifacts/` confirms the entire `artifacts/` tree is gitignored. The confidential `Input Files.xlsx`, `LE v AOP Gross to Net Decomp.xlsx`, `...xlsx_PowerQuery.m`, and the output `le-norm.db` exist only on disk under `artifacts/` and are untracked. |
| No confidential filename references in tracked docs | PASS | `git grep` of `636c493` in `docs/` for the confidential workbook filenames / `PowerQuery` returns none. |

Confidentiality verdict: **PASS**. No real or confidential data is committed to
the repository; the confidential inputs/outputs are isolated under the gitignored
`artifacts/` tree.

## 4. Toolchain Results

All commands run with the `env -u VIRTUAL_ENV` prefix per the repo Poetry quirk.

| Stage | Command | Exit | Verdict |
|---|---|---|---|
| Formatting (Black) | `env -u VIRTUAL_ENV poetry run black --check .` | 0 | PASS — 13 files unchanged |
| Linting (Ruff) | `env -u VIRTUAL_ENV poetry run ruff check .` | 0 | PASS — all checks passed |
| Type check (Pyright, strict) | `env -u VIRTUAL_ENV poetry run pyright` | 0 | PASS — 0 errors, 0 warnings, 0 informations |
| Tests (Pytest) | `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing` | 0 | PASS — 77 passed |

Architecture-boundary, contract/schema, and integration stages: the integration
scenarios (in-memory SQLite round-trip, CLI end-to-end) are covered within the
Pytest suite (`tests/test_normalize_le_io.py`). No separate architecture or
contract toolchain applies to this single-package Python module.

## 5. Coverage Verification (mandatory — Python)

Coverage artifact: `artifacts/python/lcov.info` (regenerated this run via
`--cov-report=lcov`). Coverage measured with branch coverage enabled.

| Module | Stmts | Branch | Line cov | Branch cov | Verdict |
|---|---|---|---|---|---|
| `src/le_totals.py` (new, the defect fix) | 14 | 2 | 100% | 100% | PASS |
| `src/normalize_le.py` (new) | 124 | 26 | 100% | 100% | PASS |
| `src/le_columns.py` (new) | 48 | 22 | 100% | 100% | PASS |
| `src/le_key.py` (new) | 56 | 30 | 100% | 100% | PASS |
| `src/pandas_io.py` (new) | 15 | 0 | 100% | n/a | PASS |
| `src/calculator.py` (pre-existing, unchanged) | 4 | 2 | 100% | 100% | PASS |
| TOTAL (src) | 261 | 82 | 100% | 100% | PASS |

Thresholds (uniform tier rule, `.claude/rules/quality-tiers.md`): line >= 85%,
branch >= 75%. All new files exceed both. Repo-wide Python coverage is 100% line /
100% branch. No regression on changed lines (all changed lines covered).

Coverage verdict (Python): **PASS**.

Languages with zero changed files on the branch (TypeScript, PowerShell, C#):
coverage **N/A** — no changed files, per the coverage-verdict rule.

## 6. File-Size Limit (500 lines)

No production code, test code, or reusable script file may exceed 500 lines
(`.claude/rules/general-code-change.md`).

| File | Lines | Verdict |
|---|---|---|
| `src/le_totals.py` | 95 | PASS |
| `src/normalize_le.py` | 495 | PASS (under 500) |
| `src/le_columns.py` | 204 | PASS |
| `src/le_key.py` | 262 | PASS |
| `src/pandas_io.py` | 169 | PASS |
| `tests/test_normalize_le_io.py` | 428 | PASS |
| `tests/le_fixtures.py` | 343 | PASS |
| `tests/test_le_key.py` | 209 | PASS |
| `tests/test_le_columns.py` | 168 | PASS |
| `tests/test_normalize_le.py` | **532** | **FAIL** |

File-size verdict: **FAIL** — `tests/test_normalize_le.py` is 532 lines, 32 over
the 500-line hard limit. The limit applies to test code explicitly. This is a
remediation trigger.

## 7. Suppression Authorization

The caller brief enumerates `# noqa`/`# type: ignore`/`# pyright: ignore` as
in-scope for authorization (expanded standard per prior-review feedback).

`git grep`/Grep for `noqa`, `type: ignore`, and `pyright: ignore` across `src/`
and `tests/` returns **zero matches**. The prior re-audit's Option-3 refactor
(typed pandas boundary in `src/pandas_io.py` via `cast`-to-`Protocol`; constant +
quoted-identifier read query) eliminated all four prior suppressions and the new
defect-fix code introduces none.

Suppression verdict: **PASS** — zero suppressions present; no authorization gate
to evaluate.

## 8. Determinism and Temp-File Policy

| Check | Verdict | Evidence |
|---|---|---|
| No temp files in tests | PASS | `git grep` for `tempfile`/`NamedTemporary`/`mkstemp`/`mkdtemp` in `src/`+`tests/` returns none. Excel fixtures use `io.BytesIO`; SQLite uses `sqlite3.connect(":memory:")`. |
| No sleeps / wall-clock waits | PASS | No `time.sleep`/`Thread.Sleep` in src or tests. |
| No unseeded randomness / wall-clock reads | PASS | No `datetime.now`/`random.*` in src or tests. The module is a pure transform with no clock or RNG (per spec T2 classification). Hypothesis property tests are seedable by the framework. |

Determinism verdict: **PASS**.

## 9. Evidence Location Compliance

Diff scan for files written under `artifacts/baselines/`, `artifacts/qa/`,
`artifacts/evidence/`, or `artifacts/coverage/`: **none** found in the branch
diff. All feature evidence is under the canonical
`docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/` path.

`validate_evidence_locations.py` is not present in the repository, so the
script-based scan is `UNVERIFIED (script absent)`; the manual diff scan is PASS.
No `EVIDENCE_LOCATION_OVERRIDE_REJECTED` events occurred (this agent wrote its
artifacts to the canonical feature folder).

## 10. modified-workflow-needs-green-run

The branch diff modifies no path matching `.github/workflows/**`,
`scripts/benchmarks/**`, or `.github/actions/**`. The rule does not fire. No
green-run evidence is required.

## Summary of Verdicts

| Area | Verdict |
|---|---|
| Confidentiality (no real data; artifacts untracked) | PASS |
| Formatting (Black) | PASS |
| Linting (Ruff) | PASS |
| Type check (Pyright strict) | PASS |
| Tests (Pytest, 77 passed) | PASS |
| Coverage (Python, 100% line/branch) | PASS |
| File-size limit (500 lines) | **FAIL** (`tests/test_normalize_le.py` = 532) |
| Suppression authorization | PASS |
| Determinism / no temp files | PASS |
| Evidence location | PASS (script absent: UNVERIFIED-by-script) |
| modified-workflow-needs-green-run | N/A (rule not triggered) |

Overall policy-audit verdict: **PARTIAL** — one FAIL-level finding
(`tests/test_normalize_le.py` exceeds the 500-line limit). All other policy gates
pass. Remediation is required for the file-size violation.

## Appendix A — Assumptions

- The authoritative merge-base is `03eb801` (`git merge-base` + PR-context
  agreement), not the caller-supplied `2d86e83`; scope is identical under either.
- `MCP_TEMPLATE_RESOLUTION_UNAVAILABLE`: artifacts authored from canonical
  headings because MCP template tools and repo templates are absent.
- `validate_evidence_locations.py` absent: evidence-location compliance verified
  by manual diff scan.

## Appendix B — Command Reference

```
git merge-base main HEAD
git diff --name-status 03eb801de63e5f39e18c59e8d96706eafde3857c..636c493f6dca28b7a83a1f7069e1dba881ec6e4a
git ls-files artifacts/
git check-ignore artifacts/
git grep -n -i -E "acme|globex|initech" 636c493 -- src/ tests/
git grep -h -o -E 'customer="[^"]*"' 636c493 -- tests/
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing --cov-report=lcov:artifacts/python/lcov.info
wc -l src/*.py tests/*.py
```
