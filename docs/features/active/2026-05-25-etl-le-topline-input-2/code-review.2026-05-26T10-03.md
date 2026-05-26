# Code Review — etl-le-topline-input (#2)

- Feature: 2026-05-25-etl-le-topline-input-2
- Issue: #2
- Base branch (resolved): `main`
- Range: `2d86e836f89f43df011ed7528ac8decbd82cd761..dc39c977cb023130409a94c369688f2dcda343c3`
- Review timestamp: 2026-05-26T10-03
- Reviewer: feature-review agent

> MCP_TEMPLATE_RESOLUTION_UNAVAILABLE: The MCP `code-review-template` asset and the
> orchestration-artifact validator are not available in this environment, and no repo
> template file exists. Per fail-closed guidance this artifact uses the canonical
> `## Executive Summary` + `## Findings Table` structure with the required findings-table
> header.

## Executive Summary

This re-audit covers the position-independent extraction and KEY-mismatch handling added
since the prior review. The code is well-structured: column resolution and KEY logic were
extracted into dedicated, single-purpose modules (`src/le_columns.py`,
`src/le_key.py`), keeping the host (`src/normalize_le.py`) under the 500-line limit and
improving separation of concerns. Pure logic (resolution, KEY decision) is cleanly
separated from I/O (`load_source`, `write_sqlite`) and CLI glue. Typing is complete and
Pyright-strict-clean; docstrings and intent comments meet the commenting policy.

Determinism is handled correctly for the new interactive path: `decide_key_action` is a
pure decision seam taking `is_tty: bool` and an injected `prompt` callable, and
`resolve_key`/`load_source` accept injectable `is_tty`/`prompt` collaborators. Tests drive
every KEY branch with scripted lambdas and assert no-prompt paths with a prompt that
raises, so no real stdin is touched. The fuzzy threshold (0.85) is exercised both
positively (a one-character typo binds) and negatively (an unrelated column is not
force-bound), which addresses the documented mis-mapping risk.

One review item is recorded: four suppressions (one `# noqa: S608`, three
`# pyright: ignore[reportUnknownMemberType]`) are locally safe but lack a pre-authorized
pattern match or recorded explicit approval under `.claude/rules/python-suppressions.md`
and the caller's review standard. This is an authorization-process item, not a
correctness defect; it is the driver of the PARTIAL policy verdict and is routed to
remediation. No blocker-severity correctness defects were found.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Major | tests/le_fixtures.py | line 85 | `# noqa: S608 - trusted test table name` suppresses an actively-enforced Ruff rule (only `S101` is per-file-ignored for tests) but S608 is not a pre-authorized `# noqa` pattern and has no recorded explicit approval. | Obtain explicit approval and record it, OR add an authorized "S608 — interpolated table name from trusted test constant" test-only pattern to `.claude/rules/python-suppressions.md`, OR parameterize the identifier so S608 does not fire. Do not silently keep the suppression. | The suppression policy requires a pre-authorized pattern OR explicit approval for every `# noqa`; the test-only authorized patterns (S108/S105) do not cover S608. The code is safe (fixed test literal), so this is procedural, not a bug. | `.claude/rules/python-suppressions.md:11-22, 91-96`; `pyproject.toml:45-58` (S selected, only S101 ignored for tests); `tests/le_fixtures.py:85` |
| Major | src/normalize_le.py | lines 168, 354 | Two `# pyright: ignore[reportUnknownMemberType]` directives at the `pd.read_excel` and `df.to_sql` boundaries are not a pre-authorized suppression pattern (only `# type: ignore[import-untyped]` is authorized) and have no recorded explicit approval. | Obtain and record explicit approval, OR add an authorized "reportUnknownMemberType at a pandas/unstubbed-connection boundary" pattern to the suppression policy, OR wrap the unstubbed call in a small typed adapter so the directive is unnecessary. | Authorization is required for `# pyright: ignore` per the caller's stated review standard. Each directive is single-line, narrowly scoped, and justified by an accurate comment, so the code is sound; the gap is authorization. | `.claude/rules/python-suppressions.md:99-107`; `src/normalize_le.py:164-170, 350-356` |
| Major | tests/le_fixtures.py | line 89 | `# pyright: ignore[reportUnknownMemberType]` at the `pd.read_sql` boundary; same authorization gap as the source-side directives. | Same as the source-side directives (approval, add an authorized pattern, or typed adapter). | Same rationale as above. | `tests/le_fixtures.py:86-92` |
| Info | src/le_columns.py | lines 92-130 | The fuzzy matcher resolves ties to the earliest candidate via a strict `>` on the ratio and prefers normalized-equality first, which is deterministic and matches the documented spec. | No change. Recorded as a positive determinism observation. | Deterministic tie-breaking avoids order-dependent mis-mapping; the negative test confirms the 0.85 floor is respected. | `src/le_columns.py:113-130`; `tests/test_le_columns.py:119-128` (`test_resolve_columns_unrelated_column_not_force_bound`) |
| Info | src/le_key.py | lines 127-189 | `decide_key_action` is a pure decision seam with injected `is_tty`/`prompt`; the non-interactive prompt path raises with the exact `--key-mismatch trust|overwrite` remedy rather than blocking. | No change. Recorded as a positive determinism/non-blocking observation. | Satisfies the "prompt must never block automation" constraint and the determinism rule that interactivity be injected, not real stdin. | `src/le_key.py:167-189`; `tests/test_le_key.py:53-57, 180-189` |
| Info | src/normalize_le.py | lines 43-56 | Re-exporting the column/KEY helpers via `__all__` keeps the host file under 500 lines while preserving a single import surface for callers and tests. | No change. | Aligns with the file-size limit and the small-cohesive-module guidance; the split is the reason all files are within the limit. | `src/normalize_le.py:39-56`; `wc -l` (host 483 lines) |
| Info | tests/le_fixtures.py | lines 95-129 | `PersistentConnection` neutralizes `close` so an in-memory SQLite round-trip survives `write_sqlite`'s `finally: con.close()`, avoiding any temp file. | No change. Recorded as a positive no-temp-files observation. | Satisfies the strict no-temp-files-in-tests rule while still exercising the real `to_sql`/`read_sql` path. | `tests/le_fixtures.py:95-129`; `tests/test_normalize_le_io.py:140-173` |

### Typed-Python review note

Pyright runs in `strict` mode (`pyproject.toml:87-88`) and reports 0 errors / 0 warnings
/ 0 informations on the full `src` + `tests` tree. All public functions in the three
changed source modules carry complete parameter and return annotations, including
`pd.Series[float]` and `pd.DataFrame` returns at the transform boundaries. The only typing
escape hatches are the three `reportUnknownMemberType` directives noted above, each scoped
to a single unstubbed-library call and accompanied by an explicit `pd.DataFrame` /
`pd.Series` result annotation so no `Unknown` type leaks into downstream code. No `Any`
usage and no broadened type surface were found.
