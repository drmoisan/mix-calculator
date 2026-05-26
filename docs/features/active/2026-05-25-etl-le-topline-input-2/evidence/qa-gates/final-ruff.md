# Final QA — Ruff

Timestamp: 2026-05-25T21-02
Command: `poetry run ruff check .` (run as `env -u VIRTUAL_ENV poetry run ruff check .` per VIRTUAL_ENV quirk)
EXIT_CODE: 0
Output Summary: All checks passed. 0 errors.

Suppressions present (all conform to `.claude/rules/python-suppressions.md` and the plan's S608 handling clause):
- `src/normalize_le.py`: two narrow `# pyright: ignore[reportUnknownMemberType]` on the `pd.read_excel` and `pd.to_sql` boundary calls. Justified inline: pandas-stubs overloads reference unstubbed openpyxl/connection types, so the member resolves as partially unknown under Pyright strict; results are explicitly typed and the ignores are scoped to the single boundary call lines.
- `tests/le_fixtures.py`: one `# noqa: S608 - trusted test table name` on the read-back `SELECT` (table name is a trusted in-test literal), and one narrow `# pyright: ignore[reportUnknownMemberType]` on `pd.read_sql` (same unstubbed-connection rationale as production).

These are Pyright-strict third-party-stub-completeness diagnostics at untyped-library boundaries, not S608 SQL-injection suppressions on the production `to_sql` path. The production `to_sql` table name originates from the trusted `--table-name` CLI argument; pandas quotes the identifier and no `# noqa: S608` was required on that path (Ruff did not flag it).
