# Remediation Inputs — schema-builder-ux-overhaul (Issue #50) — Cycle 2 Entry

- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main`; Head: `7b8994c`
- Source artifacts:
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/policy-audit.2026-06-05T21-27.md`
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/code-review.2026-06-05T21-27.md`
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/feature-audit.2026-06-05T21-27.md`
- Timestamp: 2026-06-05T21-27
- Consolidated blocking_count: 1

## Status of Cycle 1 Remediation

R1–R6 are CLOSED. Each seam (drag-drop Columns/Key tabs, derived-formula dialog,
`BuildSpecProvider`, `new_from_template`, `on_partial_match`) now has a production
call site reachable from `build_application` or the opened `SchemaBuilderDialog`,
proven by a dialog-level / composition-root integration test (not an isolated unit
test). N2 (dead `# noqa: N802`) and N3 (spec Decision 1 / AC 14 reconciliation) are
CLOSED. N1's intent (no test file over 500 lines) is regressed — see B1.

## Remediation-Required Findings (blocking)

### B1 — `tests/gui/test_schema_builder_presenter.py` exceeds the 500-line cap
- Policy: `general-code-change.md` File Size Limit (applies to test code).
- File: `tests/gui/test_schema_builder_presenter.py` (506 lines; was 229 on `main`,
  grew to 506 this cycle).
- The cycle's own P7-T8 evidence
  (`evidence/qa-gates/final-file-sizes.md`) omits this file, so the violation
  slipped through remediation QA.
- Required: split into focused modules (for example presenter-state / edit-load
  tests vs. seeding / new-from-template tests), preserving every existing test; do
  not delete or weaken assertions. Verify all resulting test files are <= 500 lines
  and re-run the full toolchain.

## Non-Blocking Findings (address opportunistically)

### N4 — Protocol-only modules report 0% coverage
- Files: `src/gui/_columns_tab_protocol.py`, `src/gui/_key_tab_protocol.py`.
- Both are pure `typing.Protocol` contracts imported only inside `TYPE_CHECKING`
  blocks; the only counted lines are non-executable signatures (the `...` bodies
  are coverage-excluded). Behavior is covered by the concrete widgets/presenters
  (`_columns_tab_drag.py` 95%, `_columns_tab_presenter.py` 93%,
  `_key_tab_presenter.py` 100%).
- Suggested: add `# pragma: no cover` to the contract bodies (or import the
  protocol at runtime where structurally used) so the per-file figure reflects the
  type-only nature. No behavioral gap; not blocking.

## Verification on Re-Review

After B1 is fixed, confirm every changed/new `.py` file (production and test) is
<= 500 lines, the full toolchain stays green (Black / Ruff / Pyright / Pytest),
coverage thresholds hold with no regression on changed lines, and no test was
deleted or weakened by the split.
