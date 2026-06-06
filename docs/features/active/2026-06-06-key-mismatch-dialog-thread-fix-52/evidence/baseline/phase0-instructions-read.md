# Phase 0 — Policy Reads (P0-T1)

Timestamp: 2026-06-06T11-40

Policy Order:
The repository's standing-instructions layer (the `policy-compliance-order`
"CLAUDE.md / always-loaded" layer) is auto-loaded by the harness and is NOT an
openable file on disk; it is recorded here rather than read from a `CLAUDE.md`
file. The remaining policy files were read on disk in the precedence order
defined by `.claude/skills/policy-compliance-order`.

Files read (in order):
1. (harness-auto-loaded standing instructions — not a file on disk)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/python.md
5. .claude/rules/python-suppressions.md
6. .claude/rules/self-explanatory-code-commenting.md
7. .claude/rules/quality-tiers.md

Output Summary: All six on-disk policy files plus the harness standing-instructions
layer accounted for. Key constraints noted: 500-line file cap; Black -> Ruff ->
Pyright -> Pytest toolchain loop restarting on any change; coverage >= 85% line /
>= 75% branch uniform across tiers; suppressions only per pre-authorized patterns;
mandatory class/function docstrings and intent comments on loops/branches.
