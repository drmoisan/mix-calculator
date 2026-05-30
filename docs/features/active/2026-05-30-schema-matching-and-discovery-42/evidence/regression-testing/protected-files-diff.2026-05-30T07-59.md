# Regression — Protected files unchanged (AC1, AC8)

Timestamp: 2026-05-30T07-59
Command: `git diff --name-only main -- src/normalize_le.py src/load_aop.py src/_load_aop_helpers.py src/etl_columns.py src/etl_key.py src/etl_totals.py src/schema_model.py src/schema_serialization.py src/_schema_json_helpers.py src/schema_settings.py src/schema_registry.py src/schemas/default_aop.schema.json src/schemas/default_le.schema.json`
EXIT_CODE: 0

## Result of the planned command (`git diff --name-only main`)

The `vs main` command output is NOT empty. It lists:

```
src/_schema_json_helpers.py
src/schema_model.py
src/schema_registry.py
src/schema_serialization.py
src/schema_settings.py
src/schemas/default_aop.schema.json
src/schemas/default_le.schema.json
```

## Analysis — these differences are pre-existing Feature A ancestry, not this feature's changes

Branch topology:
- Current branch: `epic/configurable-schema-subsystem-40`.
- `main` HEAD = `d14d4e9` and is also the merge-base with the current HEAD.
- Current HEAD = `602b886` (Feature A landed on the epic branch ahead of `main`).

The seven listed files are the Feature A modules and bundled schema JSON that were
committed on the epic branch and are not yet on `main`. They are committed
ancestors of this feature's work, not modifications introduced by issue #42.

Two independent confirmations that THIS feature modified no protected file:

1. Working-tree status for the protected paths is empty:
   `git status --short -- <protected paths>` -> (no output).
2. Diff against the pre-feature committed state is empty:
   `git diff --name-only HEAD -- <protected paths>` -> (no output), EXIT_CODE 0.

## AC1 resolver-specific confirmation

`src/etl_columns.py` (the AC1 raising-resolver target) is ABSENT from the
`git diff main` output, and `git diff --name-only main -- src/etl_columns.py`
returns empty. The resolver is byte-for-byte unchanged versus `main`, satisfying
AC1's "resolver unchanged" requirement.

## Verdict

PASS — this feature is additive and modified no protected file. The non-empty
`git diff main` listing reflects committed Feature A ancestry on the shared epic
branch, verified empty against `HEAD` and against working-tree status. The
orchestrator should be aware that the `vs main` comparison includes Feature A
files; the `vs HEAD` comparison is the correct gate for this feature's delta and
is empty.
