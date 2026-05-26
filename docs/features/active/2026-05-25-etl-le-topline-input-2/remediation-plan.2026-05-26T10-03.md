# Remediation Plan — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Created: 2026-05-26T10-03
- Work Mode: full-feature
- Authoritative spec (remediation inputs):
  `docs/features/active/2026-05-25-etl-le-topline-input-2/remediation-inputs.2026-05-26T10-03.md`
- Base/head: `2d86e836f89f43df011ed7528ac8decbd82cd761..dc39c977cb023130409a94c369688f2dcda343c3`

> Status: DRAFT — handoff target for `atomic_planner`. The phases and `[P#-T#]` task IDs
> below are a deterministic starting structure derived from the remediation inputs.
> `atomic_planner` is the authoritative author of the final atomic plan and must refine
> task decomposition, acceptance checks, and ordering before execution. Do not execute
> from this draft without the planner pass.

## Scope

Resolve the suppression-authorization gap recorded in
`policy-audit.2026-05-26T10-03.md` Section 3 for four suppressions:
- `tests/le_fixtures.py:85` — `# noqa: S608`
- `src/normalize_le.py:168` — `# pyright: ignore[reportUnknownMemberType]`
- `src/normalize_le.py:354` — `# pyright: ignore[reportUnknownMemberType]`
- `tests/le_fixtures.py:89` — `# pyright: ignore[reportUnknownMemberType]`

No transform behavior, threshold, or KEY semantics change. The optional housekeeping
observation (RF-4, `quality-tiers.yml`) is out of the required scope and may be deferred.

## Phase P0 — Baseline and decision

- [ ] [P0-T1] Capture a pre-change toolchain baseline (black/ruff/pyright/pytest+coverage)
  and store it under `evidence/remediation-baseline/<timestamp>/`. Acceptance: four
  baseline artifacts exist with `Command`/`EXIT_CODE` schema fields.
- [ ] [P0-T2] Decide the resolution path per finding from the three options in the
  remediation inputs (record explicit approval, add a pre-authorized pattern, or refactor
  to remove). Acceptance: the chosen option for RF-1, RF-2, RF-3 is recorded in an
  evidence note with rationale.

## Phase P1 — Resolve RF-1 (`# noqa: S608` in tests)

- [ ] [P1-T1] Apply the chosen resolution for `tests/le_fixtures.py:85` (approval record,
  policy pattern addition with the existing comment confirmed to match, or refactor
  `read_table` to eliminate S608 and remove the `# noqa`). Acceptance:
  `ruff check .` exits 0 and the suppression is either authorized or absent
  (`grep -rn "noqa: S608" src/ tests/` matches only authorized/zero occurrences).

## Phase P2 — Resolve RF-2 / RF-3 (`# pyright: ignore[reportUnknownMemberType]`)

- [ ] [P2-T1] Apply the chosen resolution for `src/normalize_le.py:168` and `:354`
  (approval record, policy pattern addition, or typed-adapter refactor that removes the
  directive). Acceptance: `pyright` exits 0; directives authorized or absent in `src/`.
- [ ] [P2-T2] Apply the chosen resolution for `tests/le_fixtures.py:89` (same option set,
  applied to `read_table`). Acceptance: `pyright` exits 0; directive authorized or absent
  in `tests/`.

## Phase P3 — Verify and record

- [ ] [P3-T1] Run the full toolchain loop until all four stages pass in a single clean
  pass:
  ```
  env -u VIRTUAL_ENV poetry run black --check .
  env -u VIRTUAL_ENV poetry run ruff check .
  env -u VIRTUAL_ENV poetry run pyright
  env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
  ```
  Acceptance: all EXIT 0; coverage remains >= 85% line / >= 75% branch (currently
  100%/100%) with no regression on changed lines; no production/test file exceeds 500
  lines.
- [ ] [P3-T2] Confirm every remaining suppression in `src/`/`tests/` matches a
  pre-authorized pattern or has recorded explicit approval:
  `grep -rn "noqa\|type: ignore\|pyright: ignore" src/ tests/`. Acceptance: each match is
  authorized; the resolution path is documented.
- [ ] [P3-T3] Store final QA-gate evidence under
  `evidence/qa-gates/<timestamp>/` with `Command`/`EXIT_CODE` fields and a 1-20 line
  output summary. Acceptance: evidence artifacts exist at the canonical path.

## Constraints (from remediation inputs)

- No test/assertion/coverage weakening; no broadened type surface; no file-level
  suppressions.
- No transform-behavior, threshold (0.85), or KEY-semantics changes.
- No temp files or real stdin in tests; preserve injected `is_tty`/`prompt` seams.
- Policy-document edits only if the chosen path is "add a pre-authorized pattern," and
  only with the required comment-format/contextual-requirement specification.
- All evidence under the canonical
  `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/` scheme.
