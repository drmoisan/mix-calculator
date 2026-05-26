# Remediation Plan — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Created: 2026-05-26T16-50
- Work Mode: full-feature
- Authoritative spec (remediation inputs):
  `docs/features/active/2026-05-25-etl-le-topline-input-2/remediation-inputs.2026-05-26T16-50.md`
- Base/head: `03eb801de63e5f39e18c59e8d96706eafde3857c..636c493f6dca28b7a83a1f7069e1dba881ec6e4a`

> Status: DRAFT — handoff target for `atomic_planner`. The phases and `[P#-T#]`
> task IDs below are a deterministic starting structure derived from the
> remediation inputs. `atomic_planner` is the authoritative author of the final
> atomic plan and must refine task decomposition, acceptance checks, and ordering
> before execution. Do not execute from this draft without the planner pass.

## Scope

Restore the 500-line file-size invariant on `tests/test_normalize_le.py` (currently
532 lines) recorded in `policy-audit.2026-05-26T16-50.md` Section 6 and
`code-review.2026-05-26T16-50.md` (Blocking). No `src/` behavior, threshold, KEY
semantics, blank-total fill, or per-row Qn validation changes. No coverage or
assertion loss. Zero suppressions must remain zero.

## Phase P0 — Baseline

- [P0-T1] Capture the current toolchain + line-count baseline (Black/Ruff/Pyright
  exit 0; Pytest 77 passed; coverage 100/100; `wc -l tests/test_normalize_le.py`
  = 532) into
  `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/remediation-baseline/2026-05-26T16-50/baseline.md`.
  Acceptance: baseline file records each command and exit code.

## Phase P1 — Split the oversized test module

- [P1-T1] Choose a cohesive test group to relocate (suggested: the `load_source` /
  blank-total-fill group or the `normalize` aggregation group) such that both the
  remaining `tests/test_normalize_le.py` and the new sibling are each <= 500 lines.
  Acceptance: the chosen group is identified by its section banner and line range.
- [P1-T2] Create `tests/test_normalize_le_transform.py` (name at planner's
  discretion), move the chosen tests intact (unchanged Arrange-Act-Assert bodies
  and assertions), and import shared helpers from `tests/le_fixtures.py`. Do not
  add suppressions. Acceptance: `env -u VIRTUAL_ENV poetry run pyright` exits 0;
  no `noqa`/`type: ignore`/`pyright: ignore` introduced.
- [P1-T3] Verify both files are <= 500 lines. Acceptance: `wc -l` on every file in
  `tests/` and `src/` reports <= 500.

## Phase P2 — Full toolchain re-verification

- [P2-T1] Run the full loop until clean in a single pass:
  `env -u VIRTUAL_ENV poetry run black --check .`,
  `... ruff check .`, `... pyright`,
  `... pytest --cov=src --cov-branch --cov-report=term-missing`.
  Acceptance: all four exit 0; collected-test count >= 77; coverage 100% line /
  100% branch with no regression on changed lines.
- [P2-T2] Store final QA evidence under
  `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/qa-gates/2026-05-26T16-50/`.
  Acceptance: evidence files record each command and exit code at the canonical
  path.

## Constraints (from remediation inputs — do not violate)

- Relocate tests intact; no deletion, weakening, or merging; collected count must
  not drop; no assertion removed.
- No `src/` behavior/threshold/KEY/fill/validation change.
- Zero suppressions before and after.
- No temp files or real stdin; keep in-memory fixtures and injected seams.
- No file may exceed 500 lines after the change.
- No edits to `.claude/rules/`. No scope narrowing; no skipped stage.
