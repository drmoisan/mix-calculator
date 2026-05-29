# Code Review: mix-pipeline-gui (Issue #19) — Final Post-Remediation Review

**Review Date:** 2026-05-28
**Reviewer:** feature-review agent (Claude Opus 4.7 1M)
**Feature Folder:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
**Feature Folder Selection Rule:** Matched the issue number (19) in the branch name `feature/mix-pipeline-gui-19`.
**Base Branch:** `main` (resolved merge-base `7836c24ed350ebe654b924373335aa606c1fa215`)
**Head Branch:** `feature/mix-pipeline-gui-19` @ `e68ea3d` + uncommitted working-tree edits to `src/gui/app.py`, `src/gui/exporters/excel_exporter.py`, plus new `tests/gui/test_app_wiring.py`.
**Review Type:** Final post-remediation review.
**Prior Reviews Superseded:**
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/code-review.2026-05-27T21-00.md`
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/code-review.2026-05-28T12-17.md`

---

## Executive Summary

The three findings raised in `code-review.2026-05-28T12-17.md` are RESOLVED on the working-tree state:

1. **Production button-to-presenter wiring (MINOR -> resolved).** `src/gui/app.py` now exposes a typed seam `wire_control_signals` (lines 161-263) plus three default-chooser/runner functions backing `QFileDialog` and `dialog.exec()`. `build_application` calls the helper at lines 323-331. All six `MainWindow` control signals (`import_one_requested`, `import_all_requested`, `run_requested`, `save_requested`, `open_db_requested`, `export_requested`) are connected to presenter handlers in the production composition root. 19 new `qtbot`-driven tests in `tests/gui/test_app_wiring.py` lock the wiring in.

2. **`# noqa: N802` on a TYPE_CHECKING Protocol method (MINOR -> resolved).** `src/gui/exporters/excel_exporter.py` dropped the `_PandasExcelWriters` Protocol that required a PascalCase `ExcelWriter` method and replaced it with `_ExcelWriterFactory = Callable[..., _ExcelWriter]` (lines 67-71). The `cast` at line 132 now targets the callable alias. The suppression is gone; the only remaining mention of the string is in an explanatory comment at line 69 describing why the refactor avoids it.

3. **Stale `artifacts/pr_context.*` (INFO -> resolved).** Both files were regenerated against the live refs (`base: main @ 7836c24`, `head: e68ea3d`). Reviewer verified by `head -20 artifacts/pr_context.summary.txt`.

A spurious `# type: ignore[method-assign]` introduced in the wiring tests during initial remediation was eliminated by replacing the instance-method monkey-patch with a typed `_AutoCheckAllExportPresenter` subclass (`tests/gui/test_app_wiring.py` lines 54-107). The subclass preserves the `ExportPresenter` type contract and keeps Pyright strict-clean without any suppression.

**Live toolchain on the working tree (this review):**

- `poetry run black --check .` -> "92 files would be left unchanged."
- `poetry run ruff check .` -> "All checks passed!"
- `poetry run pyright` -> "0 errors, 0 warnings, 0 informations".
- `QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term` -> "333 passed in 18.38s"; TOTAL 1793/1793 line (100%) and 262/262 branch (100%).

**What changed since the prior review (substantive):**

- `src/gui/app.py` grew from 197 to 404 lines: added `wire_control_signals`, `default_save_chooser`, `default_open_chooser`, `default_export_runner`, and extended `__all__`. `build_application` now calls the wiring helper.
- `src/gui/exporters/excel_exporter.py` net change: -3/+5 lines (the Protocol replacement plus an explanatory comment). The suppression is removed.
- `tests/gui/test_app_wiring.py` (new) 561 lines, 19 tests, all `qtbot`-driven.
- `artifacts/pr_context.summary.txt` and `artifacts/pr_context.appendix.txt` regenerated.

**Top 3 risks (post-remediation):**

1. **`tests/gui/test_app_wiring.py` exceeds the 500-line file-size limit** (MINOR — new finding). At 561 lines the file is 61 over the policy cap. The cap applies to production code, test code, and reusable script files; markdown fixtures are exempt but Python test files are not. Maintainability — not a correctness gap. See Findings table.

2. **Property test density on three T2 modules** (INFO — persisting). `pipeline_service.py`, `exporters/registry.py`, `exporters/base.py` carry no `hypothesis` property tests. These T2 modules contain mostly orchestration over impure I/O; the executor placed property tests on the three T2 presenters where pure-function-like content concentrates. Branch coverage is 100% on every line. Non-blocking.

3. **`PipelineWorker.run` broad-catch** (INFO — persisting). Documented worker thread failure boundary; emits `error(str)` to the UI thread. Within policy guidance. Non-blocking.

**PR readiness recommendation:** **Go / Merge** — with an optional follow-up to split `tests/gui/test_app_wiring.py` along its natural seam (signal-routing tests vs default chooser/runner tests). The split is mechanical and would not change behavior or coverage.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | `tests/gui/test_app_wiring.py` | whole file | 561 lines exceeds the 500-line policy limit. The file collects 19 tests for signal routing plus default-chooser/runner verification, plus the `_AutoCheckAllExportPresenter` test seam and the `_build_wired` helper. | Split into two files along the natural seam: `tests/gui/test_app_wiring.py` (signal routing + live-state spec, eight to nine tests, estimated ~400 lines) and `tests/gui/test_app_default_choosers.py` (six default chooser/runner tests plus their stubs, estimated ~200 lines). Move `_AutoCheckAllExportPresenter` and `_build_wired` to a shared module if both files need them, otherwise inline. | Policy `general-code-change.md` caps test code at 500 lines. The current file is well-organized but still over the cap. The split is mechanical and risk-free. | `wc -l tests/gui/test_app_wiring.py` -> 561. |
| Info | `tests/gui/test_pipeline_service.py`, `tests/gui/test_exporter_registry.py`, `src/gui/exporters/base.py` | n/a | These T2 modules do not carry `hypothesis` property tests. The general-unit-test policy reads ">= 1 per pure function" for T1/T2. Persistent from prior reviews. | Optionally add one property test per module (for example a `register/get/available_formats` round-trip on `ExporterRegistry`) to bring the suite to strict conformance. | Modules contain mostly orchestration over impure I/O / registry mutation; branch coverage is 100% on every line. | Grep over `tests/gui/**` for `from hypothesis|@given` returns only the three presenter tests. |
| Info | `src/gui/workers/pipeline_worker.py` | lines 96-101 | The broad `except Exception` is documented as the worker's failure boundary (emits `error(str)` to the UI thread and logs). | None — matches the policy guidance that broad catches are acceptable at "well-defined boundaries with context logging." | Documented as the worker boundary; the policy permits broad catches at such boundaries when re-emitted with context. | Unchanged from prior review. |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit (post-remediation)

#### What changed in the remediation

- `src/gui/app.py`:
  - Added `wire_control_signals(window, pipeline_presenter, export_presenter, export_dialog, *, save_path_chooser, open_path_chooser, export_dialog_runner)` (lines 161-263). The helper defines six closures, one per `MainWindow` control signal, each routing through the appropriate presenter. The Save and Open handlers consult the injected chooser; the Export handler consults the injected runner and selects between derived (post-run) and imported (pre-run) tables before driving `export_presenter.set_available_tables` + `export_presenter.on_export`.
  - Added three default chooser/runner helpers — `default_save_chooser`, `default_open_chooser`, `default_export_runner` — each thinly wrapping a `QFileDialog` static method or `dialog.exec()` + `QFileDialog.getSaveFileName`.
  - `build_application` now calls `wire_control_signals` with the production defaults.
  - `__all__` extended.
- `src/gui/exporters/excel_exporter.py`:
  - Removed the `_PandasExcelWriters` Protocol (which carried the `def ExcelWriter(...) -> _ExcelWriter` member and the `# noqa: N802` suppression).
  - Introduced `_ExcelWriterFactory = Callable[..., _ExcelWriter]` under `TYPE_CHECKING`.
  - `cast` at line 132 now targets the callable alias (no PascalCase method involved).
- `tests/gui/test_app_wiring.py`: new — 19 tests, 561 lines.

#### What still reads well

- The wiring helper preserves the passive-view discipline: presenters carry no Qt import; the closures bind presenters to signals at the composition seam. The default choosers are the only place `QFileDialog` static methods are called in the new code; injection seams keep tests Qt-dialog-free.
- File-size discipline holds for every production file: largest production file `src/gui/app.py` at 404 lines (up from 197), well under 500. Largest test file `tests/gui/test_app_wiring.py` at 561 — over the limit (see Findings #1).
- Loose third-party types (openpyxl, pytest-qt signal blockers) remain contained behind `TYPE_CHECKING` Protocol views plus `typing.cast`. The `_ExcelWriterFactory` Callable alias is a tighter solution than the prior Protocol-with-PascalCase-member approach.

#### Typing and API notes

- All new public functions and methods carry full type hints. `wire_control_signals` uses keyword-only chooser/runner arguments typed as `Callable[[], str | None]` and `Callable[[ExportDialog], tuple[str, str] | None]`.
- Pyright strict: 0 errors, 0 warnings, 0 informations. No per-call `# type: ignore` or `# pyright: ignore` introduced anywhere.
- The `_AutoCheckAllExportPresenter` test subclass preserves the `ExportPresenter` type contract; `set_available_tables` is overridden by inheritance, not by instance-method assignment.

#### Error handling and logging

- The wiring helper introduces no new `except` blocks. Cancelled-chooser paths are early returns (no exception).
- All production modules use `logging.getLogger(__name__)`.

---

## Test Quality Audit

The 20-module GUI test suite now covers presenters, services, exporters, widgets, the worker, the integration scenario, and — new — the production composition wiring at the button-emission level.

### Reviewed test and QA artifacts

- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/baseline/baseline.2026-05-28T12-30.md` — remediation start: 314 pass, 100% line / 100% branch.
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/qa-gate.2026-05-28T12-30.md` — post-remediation: 333 pass, 100% line / 100% branch.
- This review reproduced the post-remediation toolchain run live: 333 pass, 1793/1793 line, 262/262 branch.

### Quality assessment prompts

- **Determinism:** PASS. No `time.sleep` / `QThread.sleep` / `QTest.qWait` in `tests/gui/**` (verified by grep). The wiring tests emit signals directly rather than physically clicking buttons, which is deterministic and avoids the chance of a `qtbot.mouseClick` timing window. `hypothesis` is the only RNG source.
- **Isolation:** PASS. Each wiring test exercises one signal route; the `_build_wired` helper assembles fresh fakes per test.
- **Speed:** PASS. 333 tests run in 18.38s.
- **Diagnostics:** PASS. Assertions read the recorded calls on the fake services so failure messages identify the routing mismatch directly.
- **Wiring coverage:** RESOLVED. The new test file exercises every `MainWindow.*_requested` signal -> presenter handler call chain, plus the cancellation paths and the live-state spec read. The integration test (`test_gui_integration.py`) still drives the presenter directly; the wiring tests are the missing piece that locks the production composition in.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | Grep for confidential terms (`SKU Description`, `Category`) in `src/gui/**` and `tests/gui/**`: no real confidential values. Fabricated examples only (`"SKU-001"`, `"LE-8 + 4"`, `"AOP1"`). |
| No unsafe subprocess or command construction | PASS | No `subprocess` use anywhere in `src/gui/**`. |
| Input validation at boundaries | PASS | Loader `ValueError` propagates from each `import_*` method and is routed to `view.show_error` by the presenter. `ExportPresenter` rejects empty selections before any exporter call. The wiring helper's Save/Open/Export early-returns on a cancelled chooser. |
| Error handling remains explicit | PASS | The only broad catch remains `PipelineWorker.run`, documented as the worker's failure boundary. The wiring helper adds no new `except`. |
| Configuration / path handling is safe | PASS | Paths passed as opaque strings; no path concatenation or shell interpolation. SQLite and Excel writes flow through pandas / openpyxl via typed boundary helpers; tests use `BytesIO` and `sqlite3.connect(":memory:")`. The wiring helper does not touch the filesystem. |
| Suppression discipline | PASS | Diff-scan for `+ … noqa|type: ignore|pyright: ignore` returns only the pre-existing six pre-authorized `# noqa: ARG002` patterns. No new suppressions of any kind were introduced. The `# noqa: N802` removed; no `# type: ignore` in any production or test file in the diff. |
| Benchmark baseline / CI workflow policies | N/A | No changes under `scripts/benchmarks/**` or `.github/workflows/**` in the branch diff. |

---

## Research Log

No external research was required for this final review. The architecture research artifact `artifacts/research/mix-pipeline-gui-architecture.2026-05-27T00-00.md`, the spec/user-story/plan in the feature folder, the prior audit artifacts at 12-17, and the qa-gate evidence at 12-30 were sufficient. The reviewer additionally read the remediated source files, the new test file, and the regenerated PR-context artifacts to verify the resolution.

---

## Verdict

The implementation is functionally complete at both the presenter contract level and the production composition level under the rebased base. The MVP passive-view structure, the reuse of the existing pure transforms via `PipelineService.run_pipeline`, the extensible `ExporterRegistry`, the typed-Protocol containment of openpyxl/pytest-qt loose typings, and the newly-added testable wiring seam are all sound choices. Toolchain output is clean and coverage is 100% line / 100% branch on every changed module.

The only post-remediation finding is the 561-line `test_app_wiring.py` file, which exceeds the 500-line file-size policy by 61 lines. The fix is a mechanical two-file split.

Recommendation: **Merge** — with an optional follow-up to split the new test file. Under a strict read of the file-size policy, splitting is required; under a contract-level read, the file is well-organized and the limit is a maintainability rule, not a correctness rule. Either disposition is acceptable.
