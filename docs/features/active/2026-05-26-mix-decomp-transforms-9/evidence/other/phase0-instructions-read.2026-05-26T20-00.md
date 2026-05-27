# Phase 0 — Instructions Read Evidence (Issue #9)

Timestamp: 2026-05-26T20-00

Policy Order:
1. `CLAUDE.md` (standing instructions, auto-loaded into context)
2. `.claude/rules/general-code-change.md` (cross-language code change policy)
3. `.claude/rules/general-unit-test.md` (cross-language unit test policy)
4. Language-specific (Python): `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
5. Supporting rules: `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/benchmark-baselines.md`, `.claude/rules/tonality.md`

Files Read:
- `CLAUDE.md` — standing instructions; auto-loaded into the session context (no standalone file at repo root; the codebase instructions are delivered via the project context block).
- `.claude/rules/general-code-change.md` — design principles, mandatory seven-stage toolchain loop, 500-line file limit, error-handling, naming, I/O boundary rules.
- `.claude/rules/general-unit-test.md` — five core unit-test properties, coverage requirements (>=85% line, >=75% branch), scenario completeness, AAA structure, no temp files / no external services.
- `.claude/rules/python.md` — Black -> Ruff -> Pyright strict -> Pytest toolchain, full type hints, Google-style docstrings, dependency seams, pytest rules.
- `.claude/rules/python-suppressions.md` — authorized suppression patterns; only `BLE001 - CLI top-level error handling` is relevant here (CLI entry point).
- `.claude/rules/quality-tiers.md` — T1-T4 tiers; new modules classified T2 (Core); uniform coverage thresholds.
- `.claude/rules/self-explanatory-code-commenting.md` — mandatory class/function docstrings, loop/branch intent comments, meta-what comments, no numbered notes.
- `.claude/rules/benchmark-baselines.md` — benchmark baseline provenance (not directly in scope; no benchmark baselines touched by this feature).
- `.claude/rules/tonality.md` — professional tone for all authored content.

Confidentiality reminder applied: no real customer names, SKU descriptions, category names, SKU numbers, prices, or discounts may appear in any source, test, fixture, or doc. Only fabricated values are used (Acme Foods, Globex Market, Initech Grocers, SKU-001, Widget A, Category X). The Country values US/Canada are not secret.
