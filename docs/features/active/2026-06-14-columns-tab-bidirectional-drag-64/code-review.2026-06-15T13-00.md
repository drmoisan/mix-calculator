# Code Review: Columns Tab Bidirectional Drag (#64)

**Review Date:** 2026-06-15
**Reviewer:** Feature Review Agent (Claude Sonnet 4.6)
**Feature Folder:** `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/`
**Base Branch:** `main`
**Head Branch:** `fix/columns-tab-bidirectional-drag` (`50919cd`)
**Review Type:** Initial review

---

## Executive Summary

This change adds bidirectional drag capability to the Columns tab widget layer. Three production files change and one test file expands by 182 lines. The implementation is narrow in scope: `ColumnDropRow` gains a `mouseMoveEvent` drag-source path and a `_current_source` state variable; `ColumnsTabWidget` gains `dragEnterEvent`/`dropEvent` for pool-area unassign drops, `setAcceptDrops(True)`, a `_on_release` callback, and a `clear_row` delegator; `DragTabBinder` gains one binding line. No presenter logic changed, consistent with the issue's stated constraint that the gap is purely in the widget layer.

The implementation is clean. All toolchain stages pass. The 499-line count for `_columns_tab_drag.py` sits exactly one line below the 500-line cap, which required careful scoping. Four targeted widget-seam tests cover the positive, negative, guard-clause, and MIME-discrimination paths. The MIME design — carrying both `text/plain` (source column name) and `application/x-canonical-origin` (origin row name) — cleanly distinguishes re-assign drags from pool-token drags.

**What changed:** `_columns_tab_drag.py` gains ~58 net lines of widget event-handler code. `_schema_builder_drag_tabs.py` gains one binding line. The test file gains four tests (182 lines including inline stubs and AAA comments).

**Top 3 risks:**
1. The 499-line count for `_columns_tab_drag.py` leaves no headroom. A subsequent minor addition to that file will breach the 500-line cap and require extraction.
2. `ColumnsTabWidget.dragEnterEvent` accepts any drag carrying both `text/plain` and `CANONICAL_ORIGIN_MIME`. If another widget inadvertently sets both keys on a drag, it could trigger an unintended `clear_row` call. The current codebase has no such widgets, but this is a latent coupling risk.
3. The `type: ignore[misc, assignment]` QDrag monkey-patch pattern in tests is brittle against Pyright version upgrades or Qt stub changes. This is a pre-existing pattern in the test file, not new.

**PR readiness recommendation:** **Go** — all quality gates pass and no blocking or major findings are present.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/widgets/_columns_tab_drag.py` | Line 499 | File is at 499 lines, one below the 500-line cap. | Track this constraint actively; any future addition to the file should trigger extraction of a cohesive group into a helper module. | The issue notes `_columns_tab_drag.py` was at 441 lines pre-change; post-change it is at 499. The cap is 500. | `wc -l` output: 499 lines. |
| Info | `tests/gui/test_columns_tab_widgets.py` | Lines 151, 229, 281 | `type: ignore[misc, assignment]` on QDrag monkey-patch is used in 3 of the 4 new tests and 1 pre-existing test. | No action required; this is an established pattern for headless Qt drag testing in this file. | The suppression is in test code, targets a known Pyright limitation with module-attribute assignment, and is consistent with pre-existing usage. | `qa-pyright.md`: 0 errors; pre-existing `test_source_token_starts_drag_on_left_button_move` uses the same pattern. |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The dual-MIME key design (`text/plain` for source name, `application/x-canonical-origin` for origin canonical) is clean and self-documenting. It allows `ColumnDropRow.dropEvent` to remain unchanged while `ColumnsTabWidget.dragEnterEvent` discriminates by checking for the presence of the secondary key.
- `ColumnDropRow.mouseMoveEvent` has a precise guard clause: it returns immediately when `_current_source is None` or the left button is not held. This prevents accidental drag initiation on unassigned rows and on non-drag mouse interactions.
- The `_on_release` callback follows the same injection pattern as the existing `_on_assign` callback, keeping the widget layer consistently passive.
- `CANONICAL_ORIGIN_MIME` is exported in `__all__` and is public, allowing tests to reference the constant rather than string-literal the MIME type. This removes a maintenance hazard.
- The `clear_row` method on `ColumnsTabWidget` wraps `_on_release` with the same delegation pattern as `assign_column` wraps `_on_assign`, keeping the seam contract uniform.
- The single added line in `_schema_builder_drag_tabs.py` (`columns_widget.clear_row = self._columns_presenter.clear_row`) follows the existing wiring convention exactly, minimizing cognitive load for future readers of `DragTabBinder.__init__`.

#### Typing and API notes

- All new public methods are fully annotated: `mouseMoveEvent(self, e: QMouseEvent) -> None`, `clear_row(self, target_canonical: str) -> None`, `dragEnterEvent(self, e: QDragEnterEvent) -> None`, `dropEvent(self, e: QDropEvent) -> None`.
- `_current_source: str | None = None` is typed precisely; `_on_release: Callable[[str], None]` is typed via the existing `TYPE_CHECKING` import of `Callable`. Both are consistent with existing patterns in the file.
- `CANONICAL_ORIGIN_MIME` is typed as `str` by inference (module-level string literal). No `Any` introduced.
- Pyright reports 0 errors. The `QByteArray.toStdString()` call required for decoding the MIME data byte payload is noted in `qa-pyright.md` as a Pyright-compatible form over `bytes(ba).decode()`.

#### Error handling and logging

- No new exception-raising paths were introduced. The guard clause in `mouseMoveEvent` uses early return, which is the correct Qt widget pattern for conditional drag initiation.
- `ColumnsTabWidget.dropEvent` does not guard against a missing `CANONICAL_ORIGIN_MIME` key after accepting the drop, but `dragEnterEvent` ensures only drags carrying both keys are accepted, so `dropEvent` can safely assume the key is present.
- No print statements introduced.

---

## Test Quality Audit

The four new tests are well-structured, targeted, and follow the AAA pattern with inline comments. The QDrag stub avoids real drag loops in the headless Qt environment. Event stubs provide the minimum interface required (`mimeData()` and `acceptProposedAction()`), keeping tests focused.

### Reviewed test and QA artifacts

- `tests/gui/test_columns_tab_widgets.py` (lines 192-372) — Four new tests: drag-source positive path, drag-source guard-clause negative path, pool-drop positive path, pool-drag-enter rejection path. All pass.
- `evidence/qa-gates/qa-pytest.md` — 1041 passed, 0 failed; all 4 new tests named and confirmed passing.
- `evidence/qa-gates/qa-coverage-comparison.md` — Baseline vs post-change delta: 0% line, 0% branch. Changed module at 94% line coverage.
- `evidence/qa-gates/ac-verification.md` — AC-1 through AC-4 all verified with evidence citations.

### Quality assessment prompts

- **Determinism:** Tests use fixed MIME payloads, synthetic column names, and deterministic stubs. No wall-clock reads or external I/O.
- **Isolation:** Each test constructs its own `ColumnDropRow` or `ColumnsTabWidget` instance. No shared widget state.
- **Speed:** Qt headless tests; no evidence of timing issues noted. 1041-test run completes without warning.
- **Diagnostics:** List-accumulator assertions (`assert calls == [("col_revenue", "Revenue")]`) produce clear Pytest diff output on failure. MIME key assertions check both text and byte payload values directly.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | Inspected `_columns_tab_drag.py`, `_schema_builder_drag_tabs.py`, `test_columns_tab_widgets.py`. Only synthetic column names and MIME type strings. |
| No unsafe subprocess or command construction | PASS | No subprocess calls in changed files. |
| Input validation at boundaries | PASS | `dragEnterEvent` in `ColumnsTabWidget` validates that both MIME keys are present before accepting. `mouseMoveEvent` in `ColumnDropRow` guards against `None` source. |
| Error handling remains explicit | PASS | Guard clauses use early return. No broad exception catches introduced. |
| Configuration / path handling is safe | PASS | No filesystem paths in changed code. MIME type string is a hardcoded constant. |

---

## Research Log

No external research was required. All implementation decisions are documented in `issue.md` and `plan.2026-06-14T22-02.md` in the feature folder.

---

## Verdict

This change is ready for normal PR flow. The implementation is minimal, consistent with existing widget layer patterns, and passes all four toolchain stages clean. The 499-line count for `_columns_tab_drag.py` is a near-cap note that warrants active tracking, but it does not block merge. No blocking or major findings were identified. All four new tests pass and cover the intended behavior and guard paths.
