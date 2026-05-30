---
name: e402-fixture-import-unauthorized
description: `# noqa: E402` on test-fixture imports placed after a sys.path.insert is NOT pre-authorized in python-suppressions.md — gate it as PARTIAL/procedural
metadata:
  type: feedback
---

When a test file does `sys.path.insert(0, str(Path(__file__).resolve().parent))`
then `import aop_fixtures  # noqa: E402` (to reach shared in-memory fixture
modules), the `# noqa: E402` is locally safe but is NOT one of the pre-authorized
patterns in `.claude/rules/python-suppressions.md` (which lists S603, ARG002,
B008, TCH002/3, S310, S314, BLE001, S301, S108/S105 and `type: ignore[import-untyped]`
only). There is no recorded explicit user approval for E402.

**Rule:** Treat unauthorized E402 fixture-import suppressions the same way as the
issue #2 `# pyright: ignore` finding — PARTIAL/procedural, NOT Blocking and NOT a
code defect, routed to remediation with three resolution options: (1) refactor so
the fixtures import without sys.path manipulation (move to `tests/fixtures/` package
or a conftest fixture), removing E402 entirely — preferred; (2) record explicit
user approval; (3) add an E402 pre-authorized pattern to the policy file (policy
edit requires user authorization — the reviewer does not edit policy files).

**Why:** Verified 2026-05-30 on the epic #40 (configurable-schema-subsystem) review
at head 04dba2a — 9 such E402 directives across 6 test files. By contrast S108
(`# noqa: S108 - test fixture path`) and ARG002 (`# noqa: ARG002 - match X API`) in
the same branch matched pre-authorized patterns verbatim and passed. The repo's
ruff per-file-ignores only sets `tests/**/* = ["S101"]`, so E402 is not blanket-allowed
for tests either.

**How to apply:** grep the diff for `noqa:` and classify each code against the
pre-authorized list. S101 is blanket-allowed in tests via pyproject per-file-ignores;
S108/S105/ARG002 are pattern-authorized; E402 is NOT. See [[pyright-ignore-authorization-scope]]
for the same procedural-gate reasoning and [[policy-audit-required-structure]] for
the artifact structure.

**Epic #40 outcome (cycle 1, head 0ddfc53, verified 2026-05-30):** the preferred
refactor (option 1) was applied — fixtures moved to top-of-file package imports
(`from tests import aop_fixtures` / `from tests.le_fixtures import ...`), all 9 E402
directives and all fixture-only `sys.path.insert` lines removed, no policy edit, no
new suppression (ruff per-file-ignores still only `tests/**/* = ["S101"]`). Re-audit
verdict FULLY COMPLIANT. The gating rule above still stands for future diffs; this
note just records that the epic #40 instance is closed.
