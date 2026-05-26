# Policy Compliance Audit — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature
- Generated: 2026-05-26T14-32
- Re-audit context: post-remediation re-review of the four suppression findings
  raised in `policy-audit.2026-05-26T10-03.md` / `remediation-inputs.2026-05-26T10-03.md`.
- Base branch (resolved): `main`
- Merge-base SHA: `2d86e836f89f43df011ed7528ac8decbd82cd761`
- Head SHA: `c97da58a18869584004664590180a7d5a757f3ca`
- Audit range: `2d86e836f89f43df011ed7528ac8decbd82cd761..c97da58a18869584004664590180a7d5a757f3ca`
- Primary evidence: `artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`
- MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: the review-artifact MCP template tools
  (`resolve_policy_audit_template_asset`) and a repo-side template fallback are both
  absent in this environment; artifact built from the canonical headings per the
  fail-closed guidance in `feature-review-workflow`.

## 1. Scope and Method

The audit scope is the full feature branch diff against the resolved base `main` at
the merge-base above. Scope is feature-vs-base, not any plan/task subset. Changed code
files (determined from the branch diff, not from any caller-supplied list):

| File | Status | +/- |
|---|---|---|
| `src/normalize_le.py` | added | +476 |
| `src/le_columns.py` | added | +204 |
| `src/le_key.py` | added | +262 |
| `src/pandas_io.py` | added | +169 |
| `tests/test_normalize_le.py` | added | +435 |
| `tests/test_normalize_le_io.py` | added | +362 |
| `tests/test_le_columns.py` | added | +168 |
| `tests/test_le_key.py` | added | +209 |
| `tests/le_fixtures.py` | added | +315 |
| `pyproject.toml` | modified | +7 |
| `poetry.lock` | modified | +318/-1 |

Only Python source/test files plus Poetry config changed. No TypeScript, PowerShell, or
C# files are present in the branch diff. No paths under `.github/workflows/**`,
`scripts/benchmarks/**`, or `.github/actions/**` changed.

## 2. Rejected Scope Narrowing

None. The caller brief explicitly instructed "Determine the full diff scope yourself
from the branch diff vs `main`; do not narrow scope," which is consistent with the
scope invariant. No narrowing instruction was issued. The audit proceeds against the
full feature-vs-base diff.

## 3. Python Code Change Policy

| Check | Verdict | Evidence |
|---|---|---|
| Formatting (Black) | PASS | `env -u VIRTUAL_ENV poetry run black --check .` -> exit 0; "12 files would be left unchanged." |
| Linting (Ruff) | PASS | `env -u VIRTUAL_ENV poetry run ruff check .` -> exit 0; "All checks passed!" |
| Type checking (Pyright) | PASS | `env -u VIRTUAL_ENV poetry run pyright` -> exit 0; "0 errors, 0 warnings, 0 informations" |
| Unit + integration tests | PASS | `pytest` -> 72 passed, exit 0 |
| Suppression authorization | PASS | `grep -rn "noqa\|type: ignore\|pyright: ignore\|ruff: noqa" src/ tests/` returns no matches. Zero suppressions present. |
| File-size limit (<=500 lines) | PASS | Max is `src/normalize_le.py` at 476 lines (see Section 6). |
| Typing strictness (no `Any`, no widening) | PASS | New adapter `src/pandas_io.py` isolates the unstubbed pandas boundary behind a typed `Protocol` view via `typing.cast`; no `Any`, no `# type: ignore`/`# pyright: ignore`. Aligns with `python.md` "isolate it by wrapping untyped libraries behind small typed adapters." |
| Dependencies | PASS | `pandas`, `openpyxl` runtime deps and `hypothesis` dev dep added per spec; introduced in prior review, unchanged this revision. |
| I/O boundaries isolated | PASS | I/O confined to `load_source`/`write_sqlite` in `normalize_le.py`, routed through the typed `src/pandas_io.py` boundary; pure transforms (`coerce_sku`, `rebuild_key`, `resolve_columns`, `normalize`, `compute_ytg`, `validate_tieouts`) carry no I/O. |

### 3.1 Suppression-authorization re-verification (prior PARTIAL)

The prior re-audit (`policy-audit.2026-05-26T10-03.md`) returned PARTIAL on four
unauthorized suppressions:

- `tests/le_fixtures.py` — `# noqa: S608` (RF-1)
- `src/normalize_le.py` — two `# pyright: ignore[reportUnknownMemberType]` at
  `pd.read_excel` and `df.to_sql` (RF-2)
- `tests/le_fixtures.py` — `# pyright: ignore[reportUnknownMemberType]` at
  `pd.read_sql` (RF-3)

All four were resolved by Option 3 (refactor to remove the directive):

- A new typed boundary module `src/pandas_io.py` wraps `pd.read_excel` (`read_excel_sheet`),
  `pd.read_sql` (`read_table`), and `DataFrame.to_sql` (`write_table`). Each accesses the
  relevant member through a `Protocol` view (`_PandasReaders` / `_FrameWriter`) using
  `typing.cast`, so the previously-unknown member types are contained and Pyright strict
  reports the members as fully known. `typing.cast` is a runtime no-op.
- `src/normalize_le.py` now calls `read_excel_sheet(...)` and `write_table(...)` instead
  of the direct pandas calls that previously needed `# pyright: ignore`.
- The test `read_table` helper in `tests/le_fixtures.py` delegates to
  `src.pandas_io.read_table`.
- The S608 finding is removed because `read_table` assembles the query from a module
  constant clause (`_SELECT_ALL_FROM = "SELECT * FROM "`) concatenated with a quoted,
  escaped identifier rather than an f-string literal beginning with the SQL verb adjacent
  to interpolation. Ruff `S608` no longer fires.

Verification: `grep -rn "noqa\|type: ignore\|pyright: ignore\|ruff: noqa" src/ tests/`
returns no matches; Pyright exits 0 with 0 errors/0 warnings; Ruff exits 0. The
suppression-authorization gap that drove the prior PARTIAL is closed. Verdict: PASS.

## 4. Unit Test Policy

| Check | Verdict | Evidence |
|---|---|---|
| Tests present and passing | PASS | 72 tests pass across `test_le_columns`, `test_le_key`, `test_normalize_le`, `test_normalize_le_io` (plus pre-existing `test_calculator`). |
| No temp files in tests | PASS | All Excel fixtures use `io.BytesIO`; all SQLite round-trips use `sqlite3.connect(":memory:")`. `grep` for `tempfile`/`NamedTemporaryFile`/`mkstemp`/`tmp_path`/`tmpdir` returns no matches in `tests/` or `src/`. |
| No external dependencies | PASS | No network/DB/external process; SQLite is in-memory; Excel reads from `BytesIO`. |
| Determinism | PASS | Pure transform module; no `datetime`/`time`/`random` in production code under test. Interactive `--key-mismatch prompt` path uses injected `is_tty`/`prompt` seams (`src/le_key.py:130-131,197-198`); no real stdin. Module is T2 per spec; no Clock/seeded-RNG required. |
| Property-based tests (T2: >=1 per pure function) | PASS | Plan verification notes record hypothesis property tests for `coerce_sku`, `rebuild_key`, `compute_ytg`, `normalize`, `validate_tieouts`. |
| Coverage tooling excludes test files | PASS | Coverage report lists only `src/` modules; `tests/` excluded. |

## 5. Coverage Verification (Python — mandatory; has changed files)

Coverage artifact: `artifacts/python/lcov.info` (present; refreshed by this re-audit run).
Thresholds (uniform per `quality-tiers.md`): line >= 85%, branch >= 75%; new files
require the same; no regression on changed lines.

Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
--cov-report=lcov:artifacts/python/lcov.info` (exit 0).

| File | Tier | Line cov | Branch cov | Verdict |
|---|---|---|---|---|
| `src/normalize_le.py` (new) | new | 100% | 100% | PASS |
| `src/le_columns.py` (new) | new | 100% | 100% | PASS |
| `src/le_key.py` (new) | new | 100% | 100% | PASS |
| `src/pandas_io.py` (new) | new | 100% | (no branches) 100% | PASS |
| Repo-wide (Python) | — | 100% (244/244 stmts) | 100% (78/78 branches) | PASS |

The new boundary module `src/pandas_io.py` (15 statements) is fully covered. No coverage
regression on changed lines. Coverage verdict for Python: **PASS**.

## 6. File Size Limit (<=500 lines)

| File | Lines | Verdict |
|---|---|---|
| `src/normalize_le.py` | 476 | PASS |
| `src/le_key.py` | 262 | PASS |
| `src/le_columns.py` | 204 | PASS |
| `src/pandas_io.py` | 169 | PASS |
| `tests/test_normalize_le.py` | 435 | PASS |
| `tests/test_normalize_le_io.py` | 362 | PASS |
| `tests/le_fixtures.py` | 315 | PASS |
| `tests/test_le_key.py` | 209 | PASS |
| `tests/test_le_columns.py` | 168 | PASS |

All production and test files are under 500 lines, including the new `src/pandas_io.py`.

## 7. Workflow / Benchmark Change Policy (modified-workflow-needs-green-run)

NOT TRIGGERED. No paths under `.github/workflows/**`, `scripts/benchmarks/**`, or
`.github/actions/**` are present in the branch diff. The benchmark-baseline-provenance
and ci-workflows rules do not apply to this diff.

## 8. Evidence Location Compliance

`git diff --name-only <range>` scan for files under `artifacts/baselines/`,
`artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/`: no matches. All
feature evidence is under the canonical
`docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/` path.

The repo-side helper `validate_evidence_locations.py` is not present in this repository;
the PreToolUse hook `.claude/hooks/enforce-evidence-locations.ps1` exists. The diff-scan
result is the authoritative check here and reports zero violations. No
EVIDENCE_LOCATION_OVERRIDE_REJECTED events occurred during this review.

## 9. Tier Classification (observation)

RF-4 from the prior remediation (absent repo-root `quality-tiers.yml`) was an optional
housekeeping observation, pre-existing at the merge-base and not introduced by this
feature. It does not change any coverage verdict (thresholds are uniform across tiers).
Observation only; not a blocking finding for this PR.

## 10. Overall Verdict

PASS. All toolchain stages pass clean in a single pass. The four suppression findings
that drove the prior PARTIAL are resolved (zero suppressions in `src/` and `tests/`),
the typed-adapter approach holds Pyright strict at 0 errors without weakening typing,
all files are under the 500-line limit, no-temp-files/determinism hold, coverage is
100% line / 100% branch including the new boundary module, and no runtime behavior or
API regressed. No blocking or PARTIAL findings remain.

## Appendix A — Assumptions

- The PR-context summary records the resolved base as `origin/main @ 2f8c1d9...`, while
  the caller supplied merge-base `2d86e83...`. The merge-base SHA is the authoritative
  baseline for the diff range and is used throughout; both refer to base branch `main`.
- MCP template tools unavailable; canonical headings used (see header).

## Appendix B — Command Reference

```
git diff --stat 2d86e836f89f43df011ed7528ac8decbd82cd761..c97da58a18869584004664590180a7d5a757f3ca
git diff --name-status <range> -- src/ tests/ pyproject.toml poetry.lock
grep -rn "noqa\|type: ignore\|pyright: ignore\|ruff: noqa" src/ tests/
wc -l src/*.py tests/*.py
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing --cov-report=lcov:artifacts/python/lcov.info
grep -rn "BytesIO\|:memory:\|tempfile\|NamedTemporaryFile\|mkstemp\|tmp_path\|tmpdir" tests/ src/
```
