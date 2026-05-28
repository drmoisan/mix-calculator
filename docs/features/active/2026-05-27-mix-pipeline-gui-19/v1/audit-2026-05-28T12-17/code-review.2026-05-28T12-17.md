# Code Review: mix-pipeline-gui (Issue #19) — Post-Rebase Re-review

**Review Date:** 2026-05-28
**Reviewer:** feature-review agent (Claude Opus 4.7 1M)
**Feature Folder:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/`
**Feature Folder Selection Rule:** Matched the issue number (19) in the branch name `feature/mix-pipeline-gui-19`.
**Base Branch:** `main` (resolved merge-base `7836c24ed350ebe654b924373335aa606c1fa215`)
**Head Branch:** `feature/mix-pipeline-gui-19` @ `e68ea3d`
**Review Type:** Re-review following rebase onto current `main` (post-#15 / #18 / #20 / #23).
**Prior Review Superseded:** `docs/features/active/2026-05-27-mix-pipeline-gui-19/code-review.2026-05-27T21-00.md`

---

## Executive Summary

This re-review covers the same 24 production modules and 19 test modules added under `src/gui/**` and `tests/gui/**`, now rebased onto `7836c24` (which includes the NRR summary work from #15, the bottoms-up rollups from #18, and the customer/category mix tie-out fix from #20 / PR #23). The GUI's pipeline-service surface aligns cleanly with the post-rebase mix-pipeline shape: `PipelineService.run_pipeline` calls the same eight transform/builder functions in the same order as the post-rebase `mix_pipeline.main` (lines 197-204 on `7836c24`), then `run_transforms` — whose new outputs (bottoms-up SKU/category/customer tables and the NRR summary) are passed through opaquely as part of the `**derived` spread. No stale imports were introduced by the rebase, and no behavioral assumption in the GUI is invalidated by the bottoms-up tie-out fix (the GUI never inspects rollup values; it persists and exports them as opaque DataFrames).

The caller-reported post-rebase toolchain run was clean (Black/Ruff/Pyright: 0; Pytest: 314 pass / 0 fail; coverage 100% line / 100% branch). The reviewer independently verified import-cleanness (`from src.gui.pipeline_service import PipelineService, ImportSpec` succeeds against the rebased base) and the file-size discipline (largest production file 389 lines; largest test 424 lines).

**What changed since the prior review (substantive):**
- Base reference moved from `703de51…` to `7836c24` (the rebase). The branch diff against the new base is identical in shape to the diff against the old base for `src/gui/**` and `tests/gui/**`; the rebase only affected pre-existing `src/mix_*` modules and corresponding tests. No GUI code or GUI test changed in the rebase.
- The PR-context artifacts (`artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`) predate the rebase and reference the pre-rebase head/base. They should be regenerated before opening a PR; the audit itself used `git diff --name-only main...HEAD` against the live refs.

**Top 3 risks (re-stated for the rebased base):**

1. **Production button-to-presenter wiring gap** (MINOR — promoted from "Top Risk 3" in the prior review to a more precise statement, but unchanged behavior). `src/gui/app.py::build_application` constructs `PipelinePresenter` and `ExportPresenter` and the three `SourceSelectionPresenter` instances; it connects only the per-input `file_selected` and `render_tab_requested` signals to the source-selection presenters (lines 109-114). The six `MainWindow` control-button signals — `import_one_requested`, `import_all_requested`, `run_requested`, `save_requested`, `open_db_requested`, `export_requested` — emit on button click but are not connected to `pipeline_presenter.on_import_one` / `on_import_all` / `on_run` / `on_save` / `on_open_db` / `export_presenter.on_export_requested` in the production composition root. Presenter behavior is fully covered by unit tests that drive the presenters directly (and the integration scenario in `test_gui_integration.py` drives the presenter, not the button). In production, the buttons are inert. The prior review described this as "the worker is not wired" — the more accurate description is that the synchronous presenter path is not wired either, so neither the sync `on_run` nor the QThread-worker path is reachable from a button press.

2. **`# noqa: N802` on a TYPE_CHECKING Protocol method** (MINOR — persisting from prior review). `src/gui/exporters/excel_exporter.py:69` still carries `# noqa: N802 - mirrors the pandas API member name`. The rebase did not add an N802 pattern to `.claude/rules/python-suppressions.md` and there is no explicit user approval recorded in the rebased history. The suppression is non-discretionary (Protocol method must match the pandas API member name) and the resolution remains documentation-only.

3. **Property test density on three T2 modules** (INFO — persisting). `pipeline_service.py`, `exporters/registry.py`, and `exporters/base.py` carry no hypothesis property tests. These T2 modules contain mostly orchestration over impure I/O; the executor placed property tests on the three T2 presenters where pure-function-like content concentrates. Branch coverage is 100% on every line. The strict reading of ">= 1 per pure function" may not apply.

**PR readiness recommendation:** **Conditional Go / Remediate** — Same as the prior review on the GUI substance, with the button-wiring observation promoted because it is the only finding that could surprise an end user. Recommended remediation, in order of decreasing urgency:

1. **Wire the six MainWindow signals in `build_application`** (or document a follow-up issue). If the worker path is the intended production runner for Run, also construct the QThread there. Mechanical change; no test changes required for current tests (they bypass MainWindow).
2. Authorize or pattern-extend the `N802` suppression in `python-suppressions.md`.
3. Regenerate the `artifacts/pr_context.*` artifacts so PR tooling sees the post-rebase refs.

The Info-level T2 property-test gap can be left as is.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | `src/gui/app.py` | `build_application`, lines 73-137 | The composition root constructs `PipelinePresenter` and `ExportPresenter` but does not connect `MainWindow.import_one_requested`, `import_all_requested`, `run_requested`, `save_requested`, `open_db_requested`, or `export_requested` signals to the corresponding presenter methods. Only per-input `file_selected` and `render_tab_requested` are wired. Pressing Run / Save / Open / Export / Import buttons in the production GUI fires a signal that has no connected slot. | Add the six signal-to-presenter `connect` calls in `build_application` (and, if the worker is the intended production runner, construct a `QThread` + `PipelineWorker` and route Run through it). Alternatively, file a follow-up issue and add a `# TODO: wire control buttons` comment in `build_application` so the gap is visible. | Presenter behavior is fully verified by direct-presenter tests; the wiring decision lives at the composition root. The acceptance criteria 4-8 read as button-press-triggers-action behaviors and would surprise a user pressing the buttons today. The fix is mechanical and small. | Read `src/gui/app.py`; greps over `src/gui/app.py` for `run_requested`, `import_one_requested`, `import_all_requested`, `save_requested`, `open_db_requested`, `export_requested`, and `on_run` returned zero matches. `test_app_composition.py` constructs `wired.pipeline_presenter` and then drives it directly, never via a button click. |
| Minor | `src/gui/exporters/excel_exporter.py` | line 69 | `# noqa: N802 - mirrors the pandas API member name` is not on the pre-authorized list in `.claude/rules/python-suppressions.md` and has no recorded user approval. The rebase did not change this. | Either request explicit user approval for this single suppression or extend `python-suppressions.md` to include "TYPE_CHECKING Protocol view mirroring a third-party API member" as an approved `N802` pattern. | Non-discretionary (Protocol method must be named `ExcelWriter` to match the pandas API), narrowly scoped, no correctness risk; the policy still requires authorization. | Inspected file; greps over `src/gui/**` for `noqa` returned only this one occurrence. |
| Info | `tests/gui/test_pipeline_service.py`, `tests/gui/test_exporter_registry.py`, `src/gui/exporters/base.py` | n/a | These T2 modules do not carry hypothesis property tests. The general-unit-test policy reads ">= 1 per pure function" for T1/T2. | Optionally add one property test per module (for example a `register/get/available_formats` round-trip) to bring the suite to strict conformance. | Modules contain mostly orchestration over impure I/O / registry mutation; branch coverage is 100% on every line. | Greps over `tests/gui/**` for `from hypothesis|@given` returned only the three presenter tests. Unchanged from prior review. |
| Info | `src/gui/workers/pipeline_worker.py` | lines 96-101 | The broad `except Exception` is documented as the worker's failure boundary (emits `error(str)` to the UI thread and logs). | None — matches the policy guidance that broad catches are acceptable at "well-defined boundaries with context logging." | Documented as the worker boundary; the policy permits broad catches at such boundaries when re-emitted with context. | Inspected file; the docstring explicitly identifies the boundary. Unchanged from prior review. |
| Info | `artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt` | file headers | The PR-context artifacts reflect pre-rebase base `b0e048f…` and head `ad8c84fa…`, not the current base `7836c24` and head `e68ea3d`. | Regenerate via the orchestrator's collect-PR-context tool before opening a PR. | Audit itself used live git refs; downstream PR-creation tooling that consumes these files would compose a stale body. | `head -30 artifacts/pr_context.summary.txt` — Base ref (resolved): `origin/main @ b0e048fe…`; Head ref (resolved): `…@ ad8c84fa…`. |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit (post-rebase)

#### Alignment with the rebased base

- `PipelineService.run_pipeline` (`src/gui/pipeline_service.py` lines 304-353) calls the same import surface as the post-rebase `mix_pipeline.main` (verified by `git show main:src/mix_pipeline.py | grep run_transforms\|build_`). The eight builders invoked in order — `pivot_le`, `pivot_aop`, `build_customer_lu`, `build_aop_norm`, `build_le_norm`, `build_aop_vs_le`, `build_mix_base`, then `run_transforms` — match the post-rebase CLI exactly.
- `run_transforms` on the rebased base now spreads the bottoms-up SKU/category/customer tables and the NRR summary into its returned dict. The GUI consumes this via `**derived` in `pipeline_service.run_pipeline` and treats the dict opaquely; no GUI code path depends on the rollup numeric values. The tie-out fix from #20 changes how `mix_rollup_2/3/4` are computed (aggregating from the unfiltered `mix_base`), but the keys are unchanged and the GUI does not introspect them.
- `DbService.save_tables` / `open_tables` over `src.pandas_io` works for any rectangular table including the new bottoms-up and NRR summary tables.
- No stale import was introduced. `from src.mix_pipeline_run import run_transforms`, `from src.mix_transforms import pivot_aop, pivot_le`, and `from src.mix_lookups import …` all resolve under the rebased base (smoke-tested by importing `PipelineService` and `ImportSpec` at module level).

#### What still reads well after the rebase

- The Model-View-Presenter passive-view split is unchanged and continues to satisfy `src/gui/protocols.py` having no Qt import; presenters in `src/gui/presenters/**` continue to import no Qt symbols at runtime.
- File-size discipline is observed under the rebased base: largest production file `pipeline_service.py` at 389 lines; largest test file `test_pipeline_service.py` at 424 lines. All files <= 500 lines.
- Loose third-party types (openpyxl, pytest-qt signal blockers) remain contained behind TYPE_CHECKING Protocol views plus `typing.cast`, keeping pyright strict at zero errors with no per-call `# type: ignore` or `# pyright: ignore`.

#### Typing and API notes

- All public functions and methods carry full type hints. `ImportSpec` is `@dataclass(frozen=True)`.
- `PipelineServiceProtocol`, `WorkbookReaderProtocol`, and `ExporterProtocol` are unchanged; their signatures continue to satisfy the spec.
- The signal declarations on `PipelineWorker` (`finished: Signal = Signal(dict)`) remain pyright-strict-clean under PySide6 6.11.

#### Error handling and logging

- Loader `ValueError` is the explicit user-facing condition: presenters catch it and route to `view.show_error`; non-`ValueError` exceptions propagate. Unchanged from prior review.
- `PipelineWorker.run` remains the only broad-catch site; it is documented as the worker's failure boundary and re-emits via `error(str)`.
- All production modules use `logging.getLogger(__name__)`.

---

## Test Quality Audit

The 19-module GUI test suite continues to cover presenters, services, exporters, widgets, the worker, and an end-to-end integration scenario. The integration test drives the `PipelinePresenter` directly (not via `MainWindow` button clicks), so it does not exercise the production button-wiring path; this is the structural reason the wiring gap in Finding #1 was not caught by the existing tests.

### Reviewed test and QA artifacts (still operative under the rebased base)

- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md` — pre-rebase final QA: 279 pass, 100% line / 100% branch. Operative for the GUI surface; caller-reported post-rebase numbers (314 pass) reproduce the verdict against the larger upstream test set.
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/coverage-delta.2026-05-27T20-59.md` — baseline-versus-post-change delta: every changed line at 100% coverage. Operative for `src/gui/**`.
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-pyright.2026-05-27T20-59.md` — strict: 0 errors, 0 warnings.
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-ruff.2026-05-27T20-59.md` — 0 errors; one pre-authorized `ARG002` pattern on test fakes.
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/evidence/qa-gates/final-black.2026-05-27T20-59.md` — 0 reformats.

### Quality assessment prompts

- **Determinism:** Unchanged from prior review; no `time.sleep` / `QThread.sleep` / `QTest.qWait` in `tests/gui/**` (verified by grep). The worker test uses `qtbot.waitSignal` (event-driven). Hypothesis is the only RNG source.
- **Isolation:** Unchanged. Each test exercises a single presenter method, widget signal/slot, or exporter call.
- **Speed:** Caller-reported 314 tests run in a single suite without flake under the rebased base.
- **Diagnostics:** Unchanged.
- **Gap surfaced by re-review:** No test exercises a `MainWindow.button.click()` -> presenter handler call chain. The presenter unit tests cover all behavior in isolation; the integration test wires the presenter directly. Closing the wiring gap should be accompanied by at least one click-driven test that asserts the presenter handler is invoked.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | Grep for confidential terms (`SKU Description`, `Category`) in `src/gui/**` and `tests/gui/**`: no real confidential values. Fabricated examples only. |
| No unsafe subprocess or command construction | PASS | No `subprocess` use anywhere in `src/gui/**`. |
| Input validation at boundaries | PASS | Loader `ValueError` propagates from each `import_*` method and is routed to `view.show_error` by the presenter. `ExportPresenter` rejects empty selections before any exporter call. |
| Error handling remains explicit | PASS | The only broad catch is `PipelineWorker.run`, documented as the worker's failure boundary. All other catches are `except ValueError`. |
| Configuration / path handling is safe | PASS | Paths passed as opaque strings; no path concatenation or shell interpolation. SQLite and Excel writes go through pandas / openpyxl through typed boundary helpers; tests use `BytesIO` and `sqlite3.connect(":memory:")`. |
| Post-rebase pipeline shape | PASS | `PipelineService.run_pipeline` import surface matches post-rebase `mix_pipeline.main` exactly; no stale imports; bottoms-up tie-out fix from #20 is transparent to the GUI (the GUI does not inspect rollup values). Verified via `git show main:src/mix_pipeline.py` and source inspection. |
| Benchmark baseline / CI workflow policies | N/A | No changes under `scripts/benchmarks/**` or `.github/workflows/**` in the branch diff; `benchmark-baselines.md` and `ci-workflows.md` do not fire. |

---

## Research Log

No external research was required for this re-review. The architecture research artifact `artifacts/research/mix-pipeline-gui-architecture.2026-05-27T00-00.md`, the spec/user-story/plan in the feature folder, and the prior audit artifacts were sufficient. The reviewer additionally read `git show main:src/mix_pipeline.py` and `git show main:src/mix_pipeline_run.py` to confirm post-rebase alignment.

---

## Verdict

The implementation remains well-designed and matches the spec at the presenter contract level under the rebased base. The MVP passive-view structure, the reuse of the existing pure transforms via `PipelineService.run_pipeline`, the extensible `ExporterRegistry`, and the typed-Protocol containment of openpyxl/pytest-qt loose typings are all sound choices. Toolchain output is clean and coverage is 100% line / 100% branch on every changed module.

The two persisting Minor findings are the `# noqa: N802` documentation issue and the more precisely-stated production button-wiring gap in `build_application`. The wiring gap is the only finding that could surprise a user pressing buttons in the launched GUI; the resolution is a small mechanical change at the composition root.

Recommendation: **Remediate** — wire the six `MainWindow` control-button signals to their presenter handlers in `build_application` before merge; resolve or pattern-extend the `N802` authorization; regenerate the `pr_context.*` artifacts. Under a contract-level read of the AC, the branch is mergeable as is with the two findings tracked as a follow-up issue.
