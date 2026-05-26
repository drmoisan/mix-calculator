# Remediation Inputs — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Generated: 2026-05-26T10-03
- Source audits:
  - `docs/features/active/2026-05-25-etl-le-topline-input-2/policy-audit.2026-05-26T10-03.md`
  - `docs/features/active/2026-05-25-etl-le-topline-input-2/code-review.2026-05-26T10-03.md`
  - `docs/features/active/2026-05-25-etl-le-topline-input-2/feature-audit.2026-05-26T10-03.md`
- Base/head: `2d86e836f89f43df011ed7528ac8decbd82cd761..dc39c977cb023130409a94c369688f2dcda343c3`

## Trigger

Remediation is triggered by one meaningful PARTIAL finding in the policy audit
(Section 3, Python code change policy): four suppressions in the branch are locally safe
and narrowly scoped but are not authorized — none matches a pre-authorized pattern in
`.claude/rules/python-suppressions.md`, and there is no recorded explicit user approval.
The caller's review brief for this re-audit expressly requires that any
`# noqa`/`# type: ignore`/`# pyright: ignore` be authorized.

There are no toolchain failures, no coverage shortfalls, no unmet acceptance criteria,
and no code-correctness defects. This remediation is solely about resolving the
suppression-authorization gap (and an optional housekeeping observation).

## Findings Requiring Remediation

### RF-1 (Major) — Unauthorized `# noqa: S608` in test fixtures

- File: `tests/le_fixtures.py:85`
- Current: `query = f'SELECT * FROM "{table_name}"'  # noqa: S608 - trusted test table name`
- Why a finding: Ruff selects the `S` (flake8-bandit) ruleset and the only per-file
  ignore is `tests/** = ["S101"]` (`pyproject.toml:45-58`), so S608 is actively enforced
  in tests. S608 is not a pre-authorized `# noqa` pattern (the test-only authorized
  patterns are S108/S105 for paths/passwords), and there is no recorded explicit approval.
- Expected resolved state: one of the following, with the chosen path documented:
  1. Record explicit user approval for this specific S608 suppression, OR
  2. Add a new pre-authorized test-only pattern to `.claude/rules/python-suppressions.md`
     covering "S608 — table identifier interpolated from a trusted test constant" with a
     required comment format, then confirm the existing comment matches it, OR
  3. Refactor `read_table` so S608 does not fire (for example, validate/whitelist
     `table_name` against a known set, or read via a parameterized helper) and remove the
     `# noqa`.
- Verification: `env -u VIRTUAL_ENV poetry run ruff check .` exits 0 with the suppression
  either authorized (options 1/2) or removed (option 3); if option 3, confirm no new
  S608 occurrence remains via `grep -rn "noqa: S608" tests/ src/`.

### RF-2 (Major) — Unauthorized `# pyright: ignore[reportUnknownMemberType]` at source pandas boundaries

- Files: `src/normalize_le.py:168` (`pd.read_excel`), `src/normalize_le.py:354`
  (`df.to_sql`)
- Why a finding: the only pre-authorized `type: ignore` pattern is `import-untyped`;
  `# pyright: ignore` for `reportUnknownMemberType` is not listed, and there is no
  recorded explicit approval. The caller's brief enumerates `# pyright: ignore` as
  in-scope for authorization.
- Expected resolved state: one of:
  1. Record explicit user approval for the `reportUnknownMemberType`-at-pandas-boundary
     directives, OR
  2. Add a pre-authorized pattern to `.claude/rules/python-suppressions.md` for
     "reportUnknownMemberType at an unstubbed pandas/connection boundary" with a required
     comment format, then confirm the directives match it, OR
  3. Wrap each unstubbed call in a small typed adapter that returns the explicitly typed
     value so the directive becomes unnecessary, then remove it.
- Verification: `env -u VIRTUAL_ENV poetry run pyright` exits 0 (0 errors/0 warnings) with
  the directives either authorized (1/2) or removed (3); confirm with
  `grep -rn "pyright: ignore" src/`.

### RF-3 (Major) — Unauthorized `# pyright: ignore[reportUnknownMemberType]` in test fixtures

- File: `tests/le_fixtures.py:89` (`pd.read_sql`)
- Why a finding: same authorization gap as RF-2.
- Expected resolved state: same option set as RF-2, applied to the `read_table` helper.
- Verification: `env -u VIRTUAL_ENV poetry run pyright` exits 0; confirm with
  `grep -rn "pyright: ignore" tests/`.

### RF-4 (Observation, optional) — Missing repo-root `quality-tiers.yml`

- File: repository root (absent)
- Why noted: `.claude/rules/quality-tiers.md` states every project must be classified in
  `quality-tiers.yml`. The file is absent repo-wide and was absent at the merge-base, so
  this is pre-existing infrastructure, not introduced by this feature. It does not change
  any coverage verdict (thresholds are uniform across tiers).
- Expected resolved state (if addressed): add a repo-root `quality-tiers.yml` entry
  classifying the `normalize_le`/`le_columns`/`le_key` module(s) as T2 per spec.md.
- Verification: file exists with the module classified; not a blocker for this PR.

## Do Not Do (Constraints)

- Do not weaken or remove tests, assertions, or coverage to make a stage pass.
- Do not broaden the type surface (no `Any`, no `# type: ignore[...]` widening, no
  file-level `# pyright: ignore` or `# ruff: noqa`).
- Do not edit policy documents under `.claude/rules/` except deliberately and only if the
  chosen resolution for RF-1/RF-2/RF-3 is "add a pre-authorized pattern" — and only with
  the required comment-format and contextual-requirement specification; do not edit them
  to silence unrelated rules.
- Do not modify `src/normalize_le.py` transform behavior, the column-resolution threshold
  (0.85), or the KEY resolution semantics; behavior is correct and acceptance-criteria
  complete.
- Do not introduce temp files or real stdin into tests; keep the in-memory `io.BytesIO`
  and `sqlite3.connect(":memory:")` fixtures and the injected `is_tty`/`prompt` seams.
- Do not exceed the 500-line file limit on any production or test file.
- Do not narrow the audit scope or skip a toolchain stage.
- After any change, re-run the full toolchain loop (format -> lint -> type-check ->
  test+coverage) until all stages pass in a single clean pass, and store evidence under
  the canonical `docs/features/active/2026-05-25-etl-le-topline-input-2/evidence/<kind>/`.

## Verification Commands (full re-run)

```
env -u VIRTUAL_ENV poetry run black --check .
env -u VIRTUAL_ENV poetry run ruff check .
env -u VIRTUAL_ENV poetry run pyright
env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing
grep -rn "noqa\|type: ignore\|pyright: ignore" src/ tests/
```

Acceptance for closing this remediation: every remaining suppression in `src/` and
`tests/` either matches a pre-authorized pattern in `.claude/rules/python-suppressions.md`
(with the required comment format) or has recorded explicit user approval; all four
toolchain stages pass clean; coverage remains >= 85% line / >= 75% branch (currently
100%/100%) with no regression on changed lines.

## Handoff

- Plan target file: `docs/features/active/2026-05-25-etl-le-topline-input-2/remediation-plan.2026-05-26T10-03.md`
- Delegate to `atomic_planner` with `${spec}` = this file (authoritative) and `${file}` =
  the plan target above. Require a deterministic, atomic plan with phases and `[P#-T#]`
  task IDs, each task carrying its own acceptance check and verification command.
