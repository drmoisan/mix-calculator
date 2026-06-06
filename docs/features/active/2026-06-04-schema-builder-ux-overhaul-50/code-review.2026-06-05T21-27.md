# Code Review: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 1 EXIT Reaudit

- **Timestamp:** 2026-06-05T21-27
- **Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `7b8994c` | **Merge-base:** `5e659f2`
- **Scope:** full branch diff `main...HEAD` (114 files; Python + JSON)
- **Verdict:** PARTIAL — 1 blocking finding (file-size cap), 1 non-blocking finding. Code quality of the wiring is sound.

## Executive Summary

The remediation cycle correctly closes the defect class that produced the prior FAIL: every new seam (drag-drop Columns/Key tabs, derived-formula dialog, `BuildSpecProvider`, `new_from_template`, `on_partial_match`) is now invoked from a production call site reachable from `build_application` or the opened `SchemaBuilderDialog`, not merely from isolated unit tests. The wiring is well-factored: a single shared `open_schema_builder` path backs both the menu action and the per-tab buttons, `DragTabBinder` centralizes column/key view routing through tab presenters, and `open_new_from_template_builder` is reused by both the explicit affordance (R5) and the partial-match hand-off (R6). The four Phase-5 helper extractions are cohesive, documented, and keep all production files under the 500-line cap.

Two issues remain. One is blocking: a test file modified this cycle (`tests/gui/test_schema_builder_presenter.py`) grew to 506 lines, exceeding the repository's 500-line cap — the same file-size class of defect the cycle was supposed to remove (N1). One is non-blocking: two new `typing.Protocol` contract modules are imported only under `TYPE_CHECKING` and therefore report 0% coverage; their behavior is fully exercised through the concrete widgets and presenters.

Toolchain is green (Black, Ruff, Pyright 0 errors, 932 pytest pass), masking scan is clean, and no suppressions were added.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|----------|------|----------|---------|----------------|-----------|----------|
| Blocking | tests/gui/test_schema_builder_presenter.py | L1-506 (whole file) | Test file is 506 lines, over the 500-line cap; grew from 229 (main) to 506 this cycle. The cycle's own P7-T8 evidence omits this file. | Split into two focused modules (e.g., presenter-state/edit-load tests vs. seeding/new-from-template tests), preserving every test; re-run toolchain. | `general-code-change.md` File Size Limit applies to test code; recurrence of the N1 defect class the cycle targeted. | `awk END NR` = 506; `git show main:...` = 229; `evidence/qa-gates/final-file-sizes.md` does not list this file. |
| Non-blocking | src/gui/_columns_tab_protocol.py; src/gui/_key_tab_protocol.py | columns L19-111; key L17-75 | 0% line coverage; modules imported only under `TYPE_CHECKING`, so the class/decorator/`def` lines never execute at runtime (the `...` bodies are coverage-excluded). | Add `# pragma: no cover` to the contract bodies, or import the protocol at runtime where it is structurally used, so the coverage figure reflects the type-only nature. | Uniform 85% line / 75% branch thresholds target executable code; these are non-executable structural contracts whose behavior is covered by `_columns_tab_drag.py` (95%), `_columns_tab_presenter.py` (93%), `_key_tab_presenter.py` (100%). | pytest --cov rows show 0% for both; grep shows imports only inside `if TYPE_CHECKING:` (`_columns_tab_presenter.py:34`, `_key_tab_presenter.py:31`). |
| Info | src/gui/widgets/_schema_builder_tabs.py | build_derived_tab L238-261 | The Derived tab retains the `name\|expression` plain-text editor alongside the new "New derived column" button; the editor is the persisted surface and the dialog appends to it. | None required — intentional per Decision 7 (the dialog augments rather than replaces the editor). | Confirms R3 did not orphan the editor; derived columns surface on Columns via `set_derived` → `DragTabBinder.set_derived`. | `schema_builder_dialog.py:338-355`. |
| Info | src/gui/_schema_open_helpers.py | install_new_derived_handler L83-107 | Handler installation guards on `isinstance(presenter, SchemaBuilderPresenter)` and `callable(getattr(...))` so recording test stubs skip wiring. | None — guards are documented and the production path is exercised by the integrated test. | Defensive guards add branch count (minor branch-coverage dip) but keep the open path stub-compatible. | `coverage-comparison.md` notes the guard branches; `test_live_derived_button_adds_column_to_columns_tab` covers the real path. |

## Scope-Change Adjudication: Phase-5 Helper Extractions

The executor extracted four modules during Phase 5 to keep `app.py` and `_schema_wiring.py` under the cap. Adjudication:

- `src/gui/widgets/_schema_builder_drag_tabs.py` (303 lines, 96% cov) — `DragTabBinder`; single cohesive responsibility (route column/key view setters through tab presenters). Approved.
- `src/gui/_schema_provider_factory.py` (205 lines, 95% cov) — production `BuildSpecProvider`. Approved.
- `src/gui/_schema_open_helpers.py` (160 lines, 93% cov) — open-path helpers. Approved.
- `src/gui/_source_signal_wiring.py` (116 lines, 100% cov) — source-signal wiring. Approved.

All four are ≤ 500 lines, documented, and exercised by integrated tests. No new defect or untested executable behavior was introduced by the extractions. `app.py` (490) and `_schema_wiring.py` (417) both remain under the cap after the extractions.

## Toolchain (live at HEAD 7b8994c)

- Black: `220 files would be left unchanged` (EXIT 0)
- Ruff: `All checks passed!` (EXIT 0)
- Pyright: `0 errors, 0 warnings, 0 informations` (EXIT 0)
- Pytest: `932 passed` in 22.46s (EXIT 0); 98.7% line / 94.0% branch
- Masking scan: clean
- Suppressions added: none
