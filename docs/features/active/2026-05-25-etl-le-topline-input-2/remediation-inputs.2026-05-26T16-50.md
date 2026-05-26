# Remediation Inputs — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Generated: 2026-05-26T16-50
- Source audits:
  - `docs/features/active/2026-05-25-etl-le-topline-input-2/policy-audit.2026-05-26T16-50.md`
  - `docs/features/active/2026-05-25-etl-le-topline-input-2/code-review.2026-05-26T16-50.md`
  - `docs/features/active/2026-05-25-etl-le-topline-input-2/feature-audit.2026-05-26T16-50.md`
- Base/head: `03eb801de63e5f39e18c59e8d96706eafde3857c..636c493f6dca28b7a83a1f7069e1dba881ec6e4a`

## Trigger

Remediation is triggered by one FAIL-level finding in the policy audit (Section 6,
File-Size Limit) and the corresponding Blocking finding in the code review: the
test module `tests/test_normalize_le.py` is 532 lines, exceeding the repository
500-line hard limit, which applies to test code with no exception.

All other gates pass: Black, Ruff, Pyright (strict, 0 errors), Pytest (77 passed),
coverage 100% line / 100% branch repo-wide and per file, zero suppressions,
confidentiality clean (no real data; confidential `artifacts/` untracked), no temp
files, deterministic. The defect fix is correct and acceptance-criteria complete.
This remediation is solely about restoring the file-size invariant on the one test
module; the prior re-audit's suppression-authorization findings are already
resolved (zero suppressions remain).

## Findings Requiring Remediation

### RF-1 (Blocking) — `tests/test_normalize_le.py` exceeds the 500-line limit

- File: `tests/test_normalize_le.py` (532 lines)
- Why a finding: `.claude/rules/general-code-change.md` File Size Limit — "No
  production code, test code, or reusable script file may exceed 500 lines." The
  addition of the four blank-total tests (the defect-fix coverage) pushed the
  module from a previously-passing size to 532 lines, 32 over the limit. Test
  files are explicitly in scope for the limit.
- Expected resolved state: the file is split so no resulting file exceeds 500
  lines, with no loss of test coverage or assertions. Suggested split along the
  module's existing section banners — for example, move the `load_source` /
  blank-total-fill test group (or the `normalize` aggregation group) into a new
  sibling module such as `tests/test_normalize_le_transform.py`, importing the
  shared helpers from `tests/le_fixtures.py`. Keep each test's Arrange-Act-Assert
  body and assertions unchanged.
- Verification:
  - `wc -l tests/test_normalize_le.py` and any new sibling each report <= 500.
  - `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing`
    still reports 77 passed (or more, if a test is split into multiple files; the
    collected count must not drop) with coverage unchanged at 100% line / 100%
    branch.

## Do Not Do (Constraints)

- Do not delete, weaken, or merge tests to reduce line count; relocate them
  intact. The collected-test count must not decrease and no assertion may be
  removed.
- Do not reduce coverage; it must remain 100% line / 100% branch on `src/`.
- Do not modify any `src/` transform behavior, the column-resolution threshold
  (0.85), KEY resolution semantics, the blank-total fill (`fillna`-only), or the
  per-row Qn validation; all behavior is correct and acceptance-criteria complete.
- Do not introduce any `# noqa`/`# type: ignore`/`# pyright: ignore` directive;
  the branch currently has zero and must stay at zero.
- Do not introduce temp files or real stdin into tests; keep the in-memory
  `io.BytesIO` and `sqlite3.connect(":memory:")` fixtures and the injected
  `is_tty`/`prompt` seams.
- Do not let any resulting file exceed 500 lines, including `tests/le_fixtures.py`
  (343) if helpers are added to it.
- Do not edit policy documents under `.claude/rules/`.
- Do not narrow the audit scope or skip a toolchain stage.
- After the change, re-run the full toolchain loop (format -> lint -> type-check ->
  test+coverage) until all stages pass in a single clean pass, and store evidence
  under the canonical
  `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/`.

## Optional Observation (not required for this PR)

- The previously-noted absence of a repo-root `quality-tiers.yml` (prior
  remediation RF-4) remains pre-existing infrastructure, absent at the merge-base.
  It does not change any coverage verdict (thresholds are uniform across tiers) and
  is out of scope for this remediation.

## Verification Commands (full re-run)

```
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing
wc -l tests/*.py src/*.py
grep -rn "noqa\|type: ignore\|pyright: ignore" src/ tests/
```

Acceptance for closing this remediation: every file in `src/` and `tests/` is
<= 500 lines; all four toolchain stages pass clean; the collected-test count is
>= 77 with no removed assertions; coverage remains 100% line / 100% branch with no
regression on changed lines; zero suppressions remain.

## Handoff

- Plan target file:
  `docs/features/active/2026-05-25-etl-le-topline-input-2/remediation-plan.2026-05-26T16-50.md`
- Delegate to `atomic_planner` with `${spec}` = this file (authoritative) and
  `${file}` = the plan target above. Require a deterministic, atomic plan with
  phases and `[P#-T#]` task IDs, each task carrying its own acceptance check and
  verification command.
