# Policy Audit — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Work Mode: full-feature
- Base branch (resolved): `main`
- Merge-base SHA: `2d86e836f89f43df011ed7528ac8decbd82cd761`
- Head SHA: `dc39c977cb023130409a94c369688f2dcda343c3`
- Range: `2d86e836f89f43df011ed7528ac8decbd82cd761..dc39c977cb023130409a94c369688f2dcda343c3`
- Audit timestamp: 2026-05-26T10-03
- Auditor: feature-review agent
- Audit type: re-audit after a behavior change (position-independent column resolution
  + KEY-mismatch handling added since the prior 2026-05-25T21-11 review).

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: The MCP tool
> `mcp__drm-copilot__resolve_policy_audit_template_asset` (asset `template`) and the
> validator `mcp__drm-copilot__validate_orchestration_artifacts` are not available in
> this environment, and no repository policy-audit template file exists. Per the
> `policy-audit-template-usage` fail-closed guidance, this artifact is constructed
> directly with the canonical major headings. This does not affect the audit verdicts
> below, which are derived from the branch diff and from toolchain runs executed by the
> auditor.

## Executive Summary

The branch adds a single-file Python CLI plus two extracted helper modules:
`src/normalize_le.py` (the transform host and CLI), `src/le_columns.py`
(position-independent column resolution: position pass, then `difflib` fuzzy match
`>= 0.85`, halt on a missing required column, warn on extras), and `src/le_key.py`
(KEY create/trust/resolve with an injectable, non-blocking prompt seam). The new
behavior since the prior review is the position-independent extraction and the
`--key-mismatch {prompt,trust,overwrite}` resolution. Four test modules and the
dependency/doc changes accompany the code.

The only language with changed code files in the branch diff is Python. The auditor
re-ran the full Python toolchain (Black, Ruff, Pyright, Pytest with coverage). All four
stages passed in a single clean pass. Repo-wide coverage is 100% line and 100% branch;
the coverage artifact `artifacts/python/lcov.info` is present and was inspected.

Overall verdict: PARTIAL. There are no toolchain failures, no coverage shortfalls, and
no code-correctness defects. The single PARTIAL driver is suppression authorization
(Section 3): the branch carries four suppressions (one `# noqa: S608`, three
`# pyright: ignore[reportUnknownMemberType]`) that are each locally safe and
narrowly scoped but that do not match a pre-authorized pattern in
`.claude/rules/python-suppressions.md` and have no recorded explicit user approval.
The caller's review brief expressly requires that any
`# noqa`/`# type: ignore`/`# pyright: ignore` be authorized, so these are evaluated as
unauthorized-pending and routed to remediation for an authorization decision. One
non-blocking observation (absence of a repo-root `quality-tiers.yml`) is unchanged from
the prior review.

## 1. General Unit Test Policy Compliance

Verdict: PASS

- Independence/Isolation: Tests are function-scoped and use `monkeypatch` for the
  SQLite (`patch_connect`) and `load_source` (`patch_load_source`) boundaries; no shared
  mutable global state. Evidence: `tests/le_fixtures.py:113-171`.
- Determinism: No wall-clock, `sleep`, or unseeded randomness. Property tests use
  Hypothesis with bounded strategies (`tests/test_normalize_le_io.py:102-132`). The
  modules under test have no `datetime`/`time`/`random` usage. Critically, the KEY
  prompt interactivity is injected, not real stdin: `decide_key_action` takes
  `is_tty: bool` and `prompt: Callable`, and `resolve_key`/`load_source` accept
  `is_tty`/`prompt` collaborators that tests supply as lambdas
  (`tests/test_le_key.py:38-209`, `tests/le_fixtures.py:132-171`). No test reads real
  stdin. PASS.
- No temp files / no external services: Excel fixtures use `io.BytesIO`; SQLite
  round-trips use `sqlite3.connect(":memory:")` via a `PersistentConnection` whose
  `close` is neutralized. Repository-wide grep for `tempfile`, `NamedTemporary`,
  `mkstemp`, `mkdtemp`, `tmp_path`, `tmpdir` in `tests/` returned no matches. Evidence:
  `tests/le_fixtures.py:1-10, 95-129`.
- Scenario completeness: positive, negative (schema mismatch / missing required column,
  tie-out perturbation, FY mismatch, missing `--output`, diverging-KEY non-TTY prompt),
  edge (singleton key, 3+ rows, NaN-as-0, empty-output branch, reordered/typo columns,
  unrelated-column-not-bound), and property-based flows present.
- AAA structure and descriptive names: each test uses Arrange/Act/Assert comments and a
  behavior-descriptive name.
- Property-test density (T2 self-classified): property tests exist for `coerce_sku`,
  `rebuild_key`, `compute_ytg`, `normalize`, and `validate_tieouts`. Meets ">= 1 per
  pure function" for the pure transforms.

## 2. General Code Change Policy Compliance

Verdict: PASS

- Simplicity / separation of concerns: pure transforms are separated from I/O boundaries
  and CLI glue. The new modules increase separation: column resolution
  (`src/le_columns.py`, no I/O, no logging) and KEY logic (`src/le_key.py`, pure decision
  seam `decide_key_action` + frame mutation `resolve_key`) are isolated from the host.
  Evidence: module docstrings `src/le_columns.py:18-22`, `src/le_key.py:8-18`.
- Reusability/extensibility: `resolve_columns` takes a keyword-only `threshold` default;
  `resolve_key`/`load_source` take keyword-only injectable `is_tty`/`prompt` seams with
  sensible defaults. Consistent with the keyword-default API guidance.
- Fail-fast error handling: a missing required column raises `ValueError` naming the
  unmatched column(s) (`src/le_columns.py:193-197`); a non-interactive `prompt` policy
  raises with the exact remedy (`src/le_key.py:169-174`); `main` maps `ValueError` to
  exit code 1 (`src/normalize_le.py:473-475`). No broad catch-all; the single
  `except ValueError` at the CLI boundary re-emits a message and returns non-zero.
- File size limit (<= 500 lines): all changed Python files are within the limit:
  `src/normalize_le.py` 483, `src/le_key.py` 262, `src/le_columns.py` 204,
  `tests/test_normalize_le.py` 435, `tests/le_fixtures.py` 316,
  `tests/test_normalize_le_io.py` 362, `tests/test_le_key.py` 209,
  `tests/test_le_columns.py` 168. PASS (verified with `wc -l`).
- Naming: `snake_case` functions/variables, `CONSTANT_CASE` module constants
  (`DEFAULT_THRESHOLD`, `SOURCE_COLUMNS`, etc.), `PascalCase` class
  (`PersistentConnection`). PASS.
- Dependencies: no new dependency introduced by this revision; `difflib`, `logging`,
  `sqlite3`, `math` are stdlib. `pandas`/`openpyxl` (runtime) and
  `hypothesis`/`pandas-stubs` (dev) were already added and documented. PASS.
- I/O boundary isolation: Excel read (`load_source`) and SQLite write (`write_sqlite`)
  are isolated; `le_columns` and `le_key` are pure/logging-only. PASS.

## 3. Language-Specific Code Change Policy Compliance (Python)

Verdict: PARTIAL

- Strong typing: all public functions carry full parameter/return type hints; each module
  declares `from __future__ import annotations`; Pyright runs in `strict` mode and reports
  0 errors / 0 warnings / 0 informations (auditor run, Appendix B). PASS for typing.
- Docstrings and intent comments: every function/class has a Google-style docstring with
  Args/Returns/Raises/Side effects as applicable; loops and branches carry intent comments
  per `self-explanatory-code-commenting.md`. PASS.
- Logging vs print: `print` is used for the CLI tie-out summary by design (CLI tool
  output, documented in spec Definition of Done); warnings use the stdlib `logging`
  module (`src/le_key.py:251-260`, `src/normalize_le.py:189`). Acceptable.
- Suppressions: PARTIAL. The branch carries four suppressions. The authorization rule
  in `.claude/rules/python-suppressions.md` requires every suppression to either match a
  pre-authorized pattern OR carry explicit user approval. The caller's review brief
  additionally directs that any `# noqa`/`# type: ignore`/`# pyright: ignore` must be
  authorized. None of the four match a pre-authorized pattern, and no explicit approval
  is recorded:

  | # | File:Line | Suppression | Enforced by | Pre-authorized? | Local justification present? |
  |---|---|---|---|---|---|
  | S1 | `tests/le_fixtures.py:85` | `# noqa: S608 - trusted test table name` | Ruff `S` select; only `tests/** = ["S101"]` is per-file-ignored, so S608 is active in tests (`pyproject.toml:45-58`) | No. The test-only authorized patterns are S108/S105 (paths/passwords), not S608. | Yes — table name is a fixed test literal, not user input. |
  | S2 | `src/normalize_le.py:168` | `# pyright: ignore[reportUnknownMemberType]` | Pyright strict | No. The only authorized `type: ignore` pattern is `import-untyped`; `# pyright: ignore` / `reportUnknownMemberType` is not listed. | Yes — `pd.read_excel` overload vs unstubbed openpyxl; result explicitly typed `pd.DataFrame`. |
  | S3 | `src/normalize_le.py:354` | `# pyright: ignore[reportUnknownMemberType]` | Pyright strict | No (as S2). | Yes — `df.to_sql` `con` union includes unstubbed `sqlite3.Connection`. |
  | S4 | `tests/le_fixtures.py:89` | `# pyright: ignore[reportUnknownMemberType]` | Pyright strict | No (as S2). | Yes — `pd.read_sql` `con` union vs unstubbed connection; result explicitly typed. |

  Assessment: each suppression is single-line, narrowly scoped to one rule/diagnostic,
  and accompanied by a specific, accurate justification comment; none hides a
  code-correctness defect. The PARTIAL verdict is strictly procedural: the
  authorization gate (pre-authorized pattern OR recorded explicit approval) is not
  satisfied for any of the four. Resolution options are listed in the remediation inputs
  (obtain explicit approval, add S608-in-tests and a `reportUnknownMemberType`-at-pandas-
  boundary pattern to the pre-authorized list, or refactor to remove the directives).

  Note: a prior reviewer (`policy-audit.2026-05-25T21-11.md:91-101`) reasoned that
  `# pyright: ignore` is out of scope for `python-suppressions.md` (which names
  `# noqa`/`# type: ignore`). That reading is reasonable for the rule file taken alone,
  but the caller's brief for this re-audit expressly enumerates `# pyright: ignore` as
  in-scope for authorization. This audit applies the caller's stated standard.

## 4. Language-Specific Unit Test Policy Compliance (Python)

Verdict: PASS

- Pytest runner, `tests/test_<module>.py` layout (`test_le_columns.py`,
  `test_le_key.py`, `test_normalize_le.py`, `test_normalize_le_io.py`), `parametrize`
  used for the `coerce_sku` matrix and `decide_key_action` policy/answer matrices,
  `monkeypatch` for module attributes and `sqlite3.connect`.
- No network/DB/external-process/temp-file dependencies; in-memory only.
- Patch location is the import location used by the unit under test
  (`src.normalize_le.load_source`, `sqlite3.connect`). PASS.
- Prompt seam: tests assert the no-prompt paths by injecting a prompt callable that
  raises (`_unused_prompt`, `_raising_prompt`), and drive interactive paths with scripted
  reply lambdas. No real stdin is touched. PASS.
- Coverage thresholds satisfied (see Section 5).

## 5. Test Coverage Detail

Verdict: PASS

Coverage artifact (Python): `artifacts/python/lcov.info` — present and inspected
(auditor-confirmed; written by the auditor's `pytest --cov` run, file size 5817 bytes).

Auditor `pytest --cov --cov-branch` results (Appendix B):

| Scope | Line | Branch | Threshold (line>=85 / branch>=75) | Verdict |
|---|---|---|---|---|
| Repo TOTAL | 100% (228 stmts, 0 miss) | 100% (78 br, 0 part) | met | PASS |
| `src/normalize_le.py` (new) | 100% (120 stmts, 0 miss) | 100% (24 br, 0 part) | new-file >=85/>=75 met | PASS |
| `src/le_columns.py` (new) | 100% (48 stmts, 0 miss) | 100% (22 br, 0 part) | new-file >=85/>=75 met | PASS |
| `src/le_key.py` (new) | 100% (56 stmts, 0 miss) | 100% (30 br, 0 part) | new-file >=85/>=75 met | PASS |
| `src/calculator.py` (unchanged) | 100% | 100% | no regression | PASS |

- New-file thresholds (line >= 85%, branch >= 75%): met (100%/100% on all three new
  source files), including the new fuzzy-match and KEY-resolution branches.
- No regression on changed lines: the only pre-existing module (`src/calculator.py`)
  remains at 100%/100%.

Coverage verdict per language with changed files:
- Python: PASS (explicit).
- All other languages (TypeScript, PowerShell, C#): zero changed files in the branch
  diff; coverage is not applicable for those languages.

## 6. Test Execution Metrics

- Total tests: 72 passed, 0 failed, 0 skipped (auditor run).
  - `tests/test_le_columns.py`: 15 tests.
  - `tests/test_le_key.py`: 13 tests.
  - `tests/test_normalize_le.py`: 28 tests.
  - `tests/test_normalize_le_io.py`: 14 tests.
  - `tests/test_calculator.py`: 2 pre-existing tests.
- Runtime: ~8.4s (auditor run).
- Determinism: deterministic; no retries observed.

## 7. Code Quality Checks

| Stage | Command | Result | Verdict |
|---|---|---|---|
| Format | `env -u VIRTUAL_ENV poetry run black --check .` | 11 files unchanged | PASS |
| Lint | `env -u VIRTUAL_ENV poetry run ruff check .` | All checks passed | PASS |
| Type check | `env -u VIRTUAL_ENV poetry run pyright` | 0 errors, 0 warnings, 0 informations | PASS |
| Tests + coverage | `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | 72 passed; 100%/100% | PASS |

All stages completed in a single clean pass with no auto-fixes (no loop restart needed).
The Ruff result confirms the four suppressions are accepted by the linter/type checker;
the PARTIAL in Section 3 concerns the authorization process for those suppressions, not a
tool failure.

## 8. Gaps and Exceptions

- Suppression authorization (PARTIAL, routed to remediation): four suppressions lack a
  pre-authorized pattern match or recorded explicit approval. See Section 3 and the
  remediation inputs. This is a procedural authorization gap, not a code defect.
- Observation (non-blocking, unchanged from prior review): No `quality-tiers.yml` exists
  at the repository root. `.claude/rules/quality-tiers.md` states every project must be
  classified there. The module self-classifies as T2 (spec.md Implementation Strategy);
  the classification file is absent repo-wide and was absent at the merge-base baseline,
  so this is a pre-existing repository-infrastructure gap. It does not change any coverage
  verdict because thresholds are uniform across tiers. Recommend adding a repo-root
  `quality-tiers.yml` as housekeeping.
- Exception: MCP template-resolution and orchestration-artifact validators are
  unavailable in this environment (see header note); artifacts were built with the
  canonical headings and validated structurally by the auditor.

## 9. Summary of Changes

Core logic (Python):
- `src/normalize_le.py` (+483) — transform host + CLI; re-exports `resolve_columns`,
  `normalize_name`, `coerce_sku`, `rebuild_key`, `decide_key_action`, `resolve_key`.
- `src/le_columns.py` (+204, new) — position-independent column resolution.
- `src/le_key.py` (+262, new) — KEY create/trust/resolve with injectable prompt seam.
- `tests/test_normalize_le.py` (+435), `tests/test_normalize_le_io.py` (+362),
  `tests/le_fixtures.py` (+316), `tests/test_le_key.py` (+209),
  `tests/test_le_columns.py` (+168).

Configuration / docs:
- `pyproject.toml`, `poetry.lock` — pandas/openpyxl runtime, hypothesis/pandas-stubs dev,
  `normalize-le` script entry (unchanged by this revision relative to the prior review).
- `README.md` — usage section.
- `docs/features/.../*` (spec, user-story, issue, plan, promoted note, prior review
  artifacts, evidence) — docs.

No `.github/workflows/**`, `scripts/benchmarks/**`, or `.github/actions/**` paths
changed; the `modified-workflow-needs-green-run` rule does not fire.

## Rejected Scope Narrowing

None. The caller prompt set the full feature-vs-base scope, explicitly instructed
"Determine the full diff scope yourself from the branch diff vs `main`; do not narrow
scope," and did not attempt to narrow to a plan, task, phase, file subset, or to mark any
language out of scope. The audit was performed against the full branch diff
`2d86e836..dc39c977`.

## Evidence Location Compliance

The branch diff was scanned (`git diff --name-only <range>`) for files written under
`artifacts/baselines/`, `artifacts/baseline/`, `artifacts/qa/`, `artifacts/qa-gates/`,
`artifacts/evidence/`, `artifacts/coverage/`, `artifacts/regression-testing/`, or
`artifacts/post-change/`. None were found. All feature evidence is written to the
canonical `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/`
scheme (`evidence/baseline/`, `evidence/qa-gates/`). The only `artifacts/` path written
is `artifacts/python/lcov.info`, which is the language coverage artifact path mandated by
the feature-review-workflow SKILL coverage table, not an evidence artifact; it is not a
violation.

- Validator note: `validate_evidence_locations.py` is not present in this repository (a
  filesystem search returned no match), so the script-based scan could not be run. The
  PreToolUse hook `.claude/hooks/enforce-evidence-locations.ps1` is referenced by policy.
  The manual diff scan above is the substitute evidence; it found no FAIL-level
  evidence-location violations.

## 10. Compliance Verdict

Overall: PARTIAL

- General unit test policy: PASS
- General code change policy: PASS
- Python code change policy: PARTIAL (suppression authorization)
- Python unit test policy: PASS
- Coverage (Python, only changed language): PASS
- Workflow green-run rule: not applicable (no matching paths changed)
- Blocking findings: 0
- Remediation-required findings: 1 (suppression authorization — 4 suppressions)
- Non-blocking observations: 1 (missing repo-root `quality-tiers.yml`)

Remediation: triggered. See `remediation-inputs.2026-05-26T10-03.md`.

## Appendix A: Test Inventory

`tests/test_le_columns.py` (15):
- `normalize_name`: parametrized case/space/punctuation matrix (6 cases).
- `resolve_columns`: exact-by-position, reordered-by-name, trailing-space variant,
  fuzzy typo at >= 0.85, missing-required halt naming the column, extra-column returned,
  unrelated-column-not-force-bound (negative threshold test).
- `load_source`-level: reordered columns resolve to canonical; extra column logged as
  warning and run continues.

`tests/test_le_key.py` (13):
- `decide_key_action`: direct trust/overwrite returns policy; non-TTY prompt raises with
  guidance; TTY prompt returns user choice; retry-until-valid; unknown policy raises.
- `resolve_key`: absent -> created from pattern; present-matching -> trusted;
  present-diverging trust -> keeps existing + warns; overwrite -> replaces + warns;
  prompt non-TTY -> raises; prompt TTY -> honors choice.

`tests/test_normalize_le.py` (28):
- `coerce_sku` branch matrix and integer property; `rebuild_key`; `compute_ytg`;
  `normalize` (singleton, 2-row pair, 3+ rows NaN-as-0, column order / no YTD-YTG,
  first-appearance order, Super Category/PPG quirk, non-numeric SKU preserved, property).

`tests/test_normalize_le_io.py` (14):
- `validate_tieouts`: pass, row-count mismatch, column-total perturbation, FY mismatch,
  property round-trip.
- `write_sqlite`: round-trip columns/rows, replace-if-exists no duplication.
- `main`: end-to-end success, missing `--output` non-zero, unmatched required column
  non-zero, diverging-KEY prompt non-TTY non-zero, diverging-KEY overwrite succeeds,
  custom sheet/table name.
- `print_summary`: empty-output branch omits row samples.

`tests/test_calculator.py`: 2 pre-existing tests (unchanged).

## Appendix B: Toolchain Commands Reference

All commands run from repo root with the VIRTUAL_ENV quirk prefix
(`env -u VIRTUAL_ENV poetry run ...`) per the project's Poetry virtual-env note.

```
env -u VIRTUAL_ENV poetry run black --check .
# -> All done. 11 files would be left unchanged. (EXIT 0)

env -u VIRTUAL_ENV poetry run ruff check .
# -> All checks passed! (EXIT 0)

env -u VIRTUAL_ENV poetry run pyright
# -> 0 errors, 0 warnings, 0 informations (EXIT 0)

env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
# -> 72 passed in ~8.4s (EXIT 0)
# -> src/le_columns.py   100% line (48 stmts),  100% branch (22 br)
# -> src/le_key.py       100% line (56 stmts),  100% branch (30 br)
# -> src/normalize_le.py 100% line (120 stmts), 100% branch (24 br)
# -> TOTAL               100% line (228 stmts), 100% branch (78 br)
# -> Coverage LCOV written to artifacts/python/lcov.info

# Supporting scans
wc -l src/le_columns.py src/le_key.py src/normalize_le.py tests/*.py
#   -> max file 483 lines (all <= 500)
grep -rn "noqa|type: ignore|pyright: ignore" src/ tests/
#   -> 4 suppressions (1 noqa S608, 3 pyright reportUnknownMemberType)
grep -rn "tempfile|tmp_path|tmpdir|sys.stdin|input(" tests/
#   -> none (no temp files, no real stdin)
```
