---
name: pyright-ignore-authorization-scope
description: Whether `# pyright: ignore` counts as a governed suppression depends on the caller's brief, not just python-suppressions.md
metadata:
  type: feedback
---

For issue #2 (etl-le-topline-input) the feature branch carries `# pyright: ignore[reportUnknownMemberType]`
directives at pandas/unstubbed-connection boundaries and a `# noqa: S608` in test fixtures.
The repo rule `.claude/rules/python-suppressions.md` literally names only `# noqa` and
`# type: ignore`, so a strict reading (taken by the prior review `policy-audit.2026-05-25T21-11.md`)
treats `# pyright: ignore` as out of scope and passes the suppressions.

**Rule:** When the caller's review brief explicitly enumerates `# pyright: ignore` (or any
mechanism) as in-scope for authorization, apply that expanded standard and evaluate those
directives against the pre-authorized-pattern-OR-explicit-approval gate — even if the repo
rule file's text alone is narrower. None of the four issue #2 suppressions match a
pre-authorized pattern (authorized `type: ignore` is only `import-untyped`; authorized
test-only `noqa` is S108/S105, not S608), so the correct verdict is PARTIAL + remediation,
not PASS.

**Why:** The 2026-05-26 re-audit caller brief said "any `# noqa`/`# type: ignore`/
`# pyright: ignore` must be authorized." The suppressions were each locally safe and
narrowly scoped (so not a code defect), but the authorization gate is procedural: pattern
match or recorded approval. Reporting PASS would have ignored the caller's stated standard.

**How to apply:** Treat suppression findings as PARTIAL/procedural (not Blocking and not a
code-correctness defect) when the code is safe but unauthorized. Route to remediation with
three resolution options: record explicit approval, add a pre-authorized pattern with the
required comment format, or refactor to remove the directive. See
[[mcp-template-tools-unavailable]] and [[poetry-virtualenv-quirk]] for the other recurring
issue #2 review constraints.

**Resolution (2026-05-26 re-audit at head c97da58):** all four suppressions were
eliminated via Option 3 (refactor). A new typed boundary module `src/pandas_io.py` wraps
`pd.read_excel`/`pd.read_sql`/`df.to_sql` behind a `typing.Protocol` view accessed with
`typing.cast` (runtime no-op), so Pyright strict reports the members as fully known with
zero directives; the S608 `# noqa` was removed by assembling the read query from a constant
`SELECT * FROM ` clause plus a quoted/escaped identifier. Grep now finds zero
`# noqa`/`# type: ignore`/`# pyright: ignore` in `src/` and `tests/`; the re-audit verdict
is PASS with no remediation. The `cast`-to-`Protocol` adapter pattern is the validated way
to clear `reportUnknownMemberType` at the pandas/openpyxl boundary in this repo without
weakening typing.
