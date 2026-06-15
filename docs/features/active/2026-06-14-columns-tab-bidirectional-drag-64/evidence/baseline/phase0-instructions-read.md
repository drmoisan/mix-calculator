---
Timestamp: 2026-06-15T00-05
Policy Order:
  1. CLAUDE.md — not present at repo root (no file found)
  2. .claude/rules/general-code-change.md
  3. .claude/rules/general-unit-test.md
  4. .claude/rules/python.md
  5. .claude/rules/python-suppressions.md
---

# Phase 0 — Policy Read Evidence

## Files Read

1. `CLAUDE.md` — not present at repo root; rule auto-loaded via `.claude/rules/` frontmatter path scoping.
2. `.claude/rules/general-code-change.md` — Cross-language code change policy. Confirms: simplicity-first design, 500-line file limit, mandatory 7-stage toolchain loop (format → lint → type-check → arch → unit → contract → integration), restart from step 1 if any stage fails or changes files.
3. `.claude/rules/general-unit-test.md` — Cross-language unit test policy. Confirms: line coverage >= 85%, branch coverage >= 75%, no temp files in tests, AAA structure required.
4. `.claude/rules/python.md` — Python-specific policy. Confirms: Black → Ruff → Pyright → Pytest toolchain, full type hints, PEP 8 naming, inject collaborators via constructors.
5. `.claude/rules/python-suppressions.md` — Suppression authorization policy. Confirms: all `# noqa` and `# type: ignore` must match pre-authorized patterns or have explicit approval; `# type: ignore[arg-type]` on fake event objects is an existing pattern in the test file.

## Key Constraints Noted

- File size limit: 500 lines max for `_columns_tab_drag.py` (currently 441 lines), `_schema_builder_drag_tabs.py` (currently 308 lines).
- MIME design: `text/plain` = source column name; `application/x-canonical-origin` = originating canonical row name.
- `ColumnsTabWidget.dropEvent` receives drops that land outside any `ColumnDropRow` (pool area).
- `dragEnterEvent` on `ColumnsTabWidget` must require BOTH `hasText()` AND `hasFormat(_CANONICAL_ORIGIN_MIME)`.
- Test approach: fake event objects with `# type: ignore[arg-type]`, patch `QDrag` in module namespace.
