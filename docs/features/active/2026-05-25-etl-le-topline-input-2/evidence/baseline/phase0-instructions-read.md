# Phase 0 — Policy Read Evidence

Timestamp: 2026-05-25T20-42

Policy Order:
1. CLAUDE.md (not present at repo root; standing instructions auto-load via path-scoped frontmatter in `.claude/rules/`)
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/quality-tiers.md`
5. `.claude/rules/python.md`
6. `.claude/rules/python-suppressions.md`
7. `.claude/rules/self-explanatory-code-commenting.md`
8. `.claude/rules/tonality.md`

Files read (explicit list):
- `.claude/rules/general-code-change.md` — cross-language code change policy (design principles, mandatory seven-stage toolchain loop, 500-line file limit, error handling, I/O boundary isolation).
- `.claude/rules/general-unit-test.md` — unit test policy (independence/isolation/determinism, coverage >= 85% line and >= 75% branch, scenario completeness, no temp files, property-based tests for T1/T2).
- `.claude/rules/quality-tiers.md` — module rigor tiers; uniform coverage thresholds across T1–T4; T2 requires >= 1 property test per pure function.
- `.claude/rules/python.md` — Python toolchain order (Black -> Ruff -> Pyright -> Pytest), strong typing, docstrings, Pytest rules, prohibited behaviors.
- `.claude/rules/python-suppressions.md` — suppression authorization policy; escalation path; pre-authorized noqa/type-ignore patterns; S608 is not pre-authorized (requires resolution attempts or narrow justified suppression).
- `.claude/rules/self-explanatory-code-commenting.md` — mandatory docstrings for classes/functions, intent comments for loops/branches, no numbered notes.
- `.claude/rules/tonality.md` — professional tone; no humor, hyperbole, or decorative metaphor.

Notes:
- CLAUDE.md is absent at repo root; its role is fulfilled by the auto-loaded `.claude/rules/` policy files listed above. This is recorded for audit completeness, not a blocker.
- Module tier for `src/normalize_le.py`: T2 (Core). T2 obligations include >= 1 property test per pure function (`coerce_sku`, `rebuild_key`, `compute_ytg`, `normalize`, `validate_tieouts`).
