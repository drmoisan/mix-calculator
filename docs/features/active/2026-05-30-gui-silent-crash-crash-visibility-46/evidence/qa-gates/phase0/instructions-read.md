# Phase 0 — Instructions Read (Cycle 2)

Timestamp: 2026-05-31T03-25

Policy Order:
1. `.claude/rules/general-code-change.md`
2. `.claude/rules/general-unit-test.md`
3. `.claude/rules/python.md`
4. `.claude/rules/python-suppressions.md`
5. `.claude/rules/quality-tiers.md`
6. `.claude/rules/self-explanatory-code-commenting.md`
7. `.claude/rules/tonality.md`
8. `.claude/rules/benchmark-baselines.md`
9. `.claude/rules/ci-workflows.md`

Files read (in the order above):
- `.claude/rules/general-code-change.md`
- `.claude/rules/general-unit-test.md`
- `.claude/rules/python.md`
- `.claude/rules/python-suppressions.md`
- `.claude/rules/quality-tiers.md`
- `.claude/rules/self-explanatory-code-commenting.md`
- `.claude/rules/tonality.md`
- `.claude/rules/benchmark-baselines.md`
- `.claude/rules/ci-workflows.md`

Output Summary: All nine policy files read in the order above. Hard constraints carried into cycle-2 execution: no new dependency; no new `# noqa` / `# type: ignore` / `# pyright: ignore`; 500-line file cap on both production and test code; no runtime temp files in tests; mandatory four-stage Python toolchain loop (black -> ruff -> pyright -> pytest with coverage); coverage thresholds line >= 85%, branch >= 75% uniform across T1-T4; preserve `vars(crash_handler)[...]` private-symbol access and in-memory `BytesIO` sink technique in relocated R4 closure tests.
