# Phase 0 — Instructions Read (Issue #20)

Timestamp: 2026-05-27T22-07

Policy Order: The repository auto-loads policy via path-scoped frontmatter in `.claude/rules/`. The documented precedence order (per `policy-compliance-order`) is:
1. `CLAUDE.md` (standing instructions)
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. Language-specific rules (Python): `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`

Files read (in required order):
- `CLAUDE.md` — NOT PRESENT in this repository (no file at repo root or anywhere under the tree; verified via glob `**/CLAUDE.md`). Standing instructions are delivered through the auto-loaded `.claude/rules/` files below, which are loaded into the agent context. No separate `CLAUDE.md` exists to read; its role is fulfilled by the path-scoped rules.
- `.claude/rules/general-code-change.md` — read (cross-language code change policy: design principles, mandatory seven-stage toolchain loop, 500-line file limit, I/O boundary isolation).
- `.claude/rules/general-unit-test.md` — read (cross-language unit test policy: five test properties, coverage >= 85% line / >= 75% branch, scenario completeness, determinism).
- `.claude/rules/python.md` — read (Black -> Ruff -> Pyright -> Pytest toolchain order; restart on any failure/file change; coverage thresholds; pytest rules).
- `.claude/rules/python-suppressions.md` — read (suppression authorization policy; pre-authorized noqa/type-ignore patterns; escalation path).
- `.claude/rules/quality-tiers.md` — read (T1–T4 tier matrix; uniform coverage thresholds across tiers).
- `.claude/rules/self-explanatory-code-commenting.md` — read (mandatory docstrings for classes/functions/private helpers; loop/branch intent comments; no numbered notes).
- `.claude/rules/tonality.md` — read (professional tone; no humor/hyperbole; evidence-first wording).

Output Summary: All policy files in the required order were read. `CLAUDE.md` does not exist as a discrete file in this repository; its standing-instruction role is served by the auto-loaded `.claude/rules/` files, all seven of which exist and were read. No policy files under `.claude/rules/` or `.github/instructions/` will be modified during execution.
