# Code Review: Pipeline GUI Hardening and Schema Selection (Issue #48)

**Review Date:** 2026-06-01
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
**Feature Folder Selection Rule:** Active folder whose `-48` suffix matches the issue number in the branch name `bug/gui-silent-crash-crash-visibility-46` is absent; the supplied active folder and the PR-context summary both resolve to the `-48` folder with the most material scoping-doc changes.
**Base Branch:** `main` (`1df33019b31bbeb73fb96bc0490ffb3cc4bba288`)
**Head Branch:** `feature/pipeline-gui-hardening-schema-select-48` (`c526e4f1cf988c02fcfbc2571249148327ad765e`)
**Review Type:** Initial review

---

## Executive Summary

This branch delivers six workstreams against Issue #48: routing the KEY-mismatch decision through a Qt modal instead of stdin (WS1a), a console-less packaged launch flag (WS1b), a per-source-tab import-schema dropdown (WS2), a strengthened Run gate that requires all three import keys (WS3), modal-plus-status-bar error surfacing (WS4), and a corrected `validate_aop` YTD/YTG identity for partial-year ("8+4") workbooks (WS5). The change is Python-only, spans 16 source files and ~21 test modules, and is structured around small injectable seams (a default trust resolver, a pure Run-gate predicate, a pure identity-map helper) with the Qt surface isolated in dedicated `_`-prefixed modules. The reviewer independently reproduced a clean four-stage toolchain pass and 100% line/branch coverage on every changed module.

**What changed:**
- `src/_load_aop_helpers.py`: new pure `build_per_row_checks`; `validate_aop` delegates the YTD/YTG split to it. `src/load_aop.py` reuses the same map for blank-fill.
- `src/gui/_key_mismatch_seam.py` + `_key_mismatch_dialog.py` (new): default-trust resolver, no-stdin seams, and the Qt modal; wired into `pipeline_service.py` for both the LE and AOP loaders.
- `src/gui/presenters/import_dispatch.py`: new `required_keys_present` gate; `pipeline_presenter.can_run` delegates to it.
- `src/gui/_main_window_view.py`: `show_error` now drives `QMessageBox.critical` plus a truncated status summary.
- WS2 widget/presenter/wiring additions for the schema dropdown, placeholder, and build-new-schema button.

**Top 3 risks:**
1. The WS5 fixture change rewrites well-formed YTD values for no-YTG workbooks (`_rewrite_ytd_for_full_year`). This is correct, but it adds fixture complexity; a future fixture edit could mask a real full-year identity regression if the rewrite heuristic ("YTD equals the partial-year default") is not understood. Mitigated by the negative-path tests that still assert full-year violations raise.
2. The KEY-mismatch resolver default is "trust" (keep existing). This is the documented safe default, but it means a diverging KEY is silently trusted in a non-interactive GUI default unless the composition root injects the modal-backed resolver. Verified that the production composition root injects the Qt resolver and that `no_stdin_prompt` raises if the prompt path is ever reached, so the failure mode is loud, not silent.
3. No runtime assertion that the packaged build actually opens no console window (WS1b is verified by argv inspection only, per the spec's stated testing strategy). This matches AC-4's "and/or" wording and the spec's explicit decision not to assert a runtime console window in unit tests.

**PR readiness recommendation:** **Go** — The implementation is clean, fully tested, and policy-compliant; no Blocking or Major findings were identified.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/_load_aop_helpers.py` | `build_per_row_checks` (185-219), `validate_aop` (222-294) | WS5 corrects the identity rather than relaxing it: with YTG present, YTD must equal sum(Jan..Apr) AND YTG must equal sum(May..Dec); with YTG absent, YTD must equal sum(Jan..Dec). Genuine violations still raise via `total_vs_months_violations`. | None. Matches AC-8/9/10 and the Non-Goal "do not relax validation". | Diff inspection + 3 negative-path tests in `tests/test_load_aop_helpers.py` raising `ValueError`. |
| Info | `src/load_aop.py` | 227-237 | The blank-fill total map was changed to reuse `build_per_row_checks`, removing a prior inconsistency where fill used full-year YTD while validation used a different map. This strengthens correctness within WS5 scope. | None. Net positive consistency improvement. | `git diff src/load_aop.py`; `load_aop.py` 100% covered. |
| Info | `src/gui/_key_mismatch_seam.py` | `no_stdin_prompt` (58-77) | The stdin path is made fail-loud: if the prompt seam is ever reached in a GUI session it raises `RuntimeError` rather than blocking on real stdin. | None. Good defensive design supporting AC-1/AC-3. | Diff inspection; `tests/gui/test_pipeline_service_key_seam.py` asserts the stdin path is never reached. |
| Nit | `tests/aop_fixtures.py` | `_rewrite_ytd_for_full_year` (138-180) | The full-year YTD rewrite relies on the heuristic that a row's YTD equals the partial-year Jan..Apr default to decide whether to promote it; a test that deliberately sets YTD to the partial-year sum on a full-year workbook would be silently promoted. | Consider keying the rewrite on an explicit flag rather than value equality if fixtures grow. Not required now. | Diff inspection; current tests pass and exercise both identities. |
| Info | `src/build_exe.py` | `resolve_nuitka_command` (125-148) | WS1b adds `--windows-console-mode=disable` to the deterministic argv. The pre-existing `# noqa: S603` on the unchanged `runner(...)` call matches the authorized pattern. | None. AC-4 satisfied via the build-config path. | `git diff src/build_exe.py`; `tests/test_build_exe.py`. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- **WS5 identity extraction is clean and pure.** `build_per_row_checks(columns)` is a single-branch pure function with no I/O; `validate_aop` delegates to it and keeps the empty-frame guard, the quarter checks, the duplicate-KEY warning, and `TIEOUT_TOL` unchanged. Reusing the same map in `load_aop.py`'s blank-fill removes a latent fill/validate inconsistency.
- **WS1a uses the existing loader seam correctly.** `PipelineService` forwards `key_mismatch=self._key_mismatch_resolver()`, `is_tty=never_tty`, and `prompt=no_stdin_prompt` to both `normalize_le.load_source` and `load_aop.load_aop`, so neither GUI import path can reach the built-in `input()`. The resolver default ("trust") short-circuits `reconcile_key` before the prompt path; the production resolver is the Qt modal defaulting to "Keep existing".
- **WS3 is a delegated pure predicate.** `required_keys_present(imported, derived, is_running)` requires all three keys (or a non-empty derived set for re-runs) and not running. The import-error callbacks recompute the Run button from this gate, so a partial import leaves Run disabled and `run_pipeline` is never reached with a missing key — closing the `KeyError: 'aop'` cascade.
- **WS4 surfaces both a modal and a status summary.** `MainWindowPipelineView.show_error` calls `show_dialog_error` (QMessageBox.critical with the full diagnostic) and then writes a first-line, length-bounded summary to the status bar.
- **WS2 is additive.** The schema dropdown, `<Choose Schema>` placeholder, and build-new-schema button are added to `SourceInputWidget`; discovery selects a schema only on `action="proceed"` and leaves the placeholder on `action="resolve"`. The known-file loaders (`import_le`/`import_aop`/`import_skulu`) are untouched and remain the default path; `import_with_schema` is a separate additive method.
- **Extraction-before-addition was honored.** `app.py` (was 499) and `pipeline_presenter.py` (was 490) were reduced by extracting wiring/dispatch into sibling modules before WS2/WS3 additions landed; the largest changed file is 494 lines.

#### Typing and API notes

- New public surfaces are fully typed: `build_per_row_checks(columns: Sequence[str]) -> dict[str, list[str]]`, `required_keys_present(...) -> bool`, `build_key_mismatch_resolver(...) -> Callable[[], str]`. `ImportSpec` and `SchemaDiscoveryDecision` are frozen dataclasses. Protocols (`PipelineServiceProtocol`, `ImportDispatchContext`) carry the call surface. No new `Any`; Pyright is clean. Keyword-only injection (`*, key_mismatch_resolver=...`, `*, schema_service=None`) preserves extensibility without breaking existing callers.

#### Error handling and logging

- Exception handling is specific and boundary-scoped: loaders propagate `ValueError`, presenters catch `ValueError` to route to `show_error` while letting other exceptions propagate, unknown import keys raise `KeyError`, and `no_stdin_prompt` raises `RuntimeError`. New code logs via `logging` at appropriate levels; the only `print` is the pre-existing CLI `print_summary`.

---

## Test Quality Audit

The reviewer independently ran `poetry run pytest --cov --cov-branch` (801 passed, 30.44s) and `poetry run coverage report`, confirming the changed modules at 100% line/branch. WS5 has dedicated positive, negative, and property tests; WS1a/WS3/WS4/WS2 each have unit and behavioral integration tests. No regression and no skipped/removed assertions.

### Reviewed test and QA artifacts

- `tests/test_load_aop_helpers.py` — WS5 corrected identity: YTG-present split, full-year YTD, quarter independence, a Hypothesis partition property, and three genuine-violation negatives. All values synthetic.
- `tests/gui/test_pipeline_service_key_seam.py` — Asserts the GUI import path never reaches stdin and that "Keep existing"->trust, "Rebuild"->overwrite for both AOP and LE.
- `tests/gui/test_pipeline_presenter_run_gate.py` — Partial import leaves Run disabled; all-keys-present enables it; no `KeyError`.
- `tests/gui/test_main_window_view.py` — `show_error` drives both the modal and the status summary.
- `tests/gui/test_source_input_widget.py` / `test_source_selection_presenter.py` / `integration/test_behavioral_schema_import.py` — Placeholder present, proceed selects, resolve leaves placeholder, build button opens the builder.
- `evidence/qa-gates/coverage-delta.md` / `evidence/regression-testing/ws5-validate-aop.md` — Coverage delta and WS5 regression evidence; consistent with the reviewer's independent run.

### Quality assessment prompts

- **Determinism:** Synthetic inputs, injected fakes for the resolver/service/views, in-memory `io.BytesIO` workbooks, offscreen Qt. No wall-clock/RNG/network/temp-file dependence.
- **Isolation:** Each test targets a single behavior with a clear name and docstring.
- **Speed:** 801 tests in 30.44s; no sleeps or retries.
- **Diagnostics:** `pytest.raises(..., match="YTD"|"YTG")` and aggregated `validate_aop` messages naming offending KEYs make failures self-identifying.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No credentials/keys introduced. AC-15: no confidential workbook figures — fixtures and tests use synthetic `range(1,13)`-derived values only. |
| No unsafe subprocess or command construction | ✅ PASS | `build_exe.py` builds a deterministic argv from constants; the only subprocess call is the pre-existing seam with the authorized `# noqa: S603`. No shell string interpolation. |
| Input validation at boundaries | ✅ PASS | `validate_aop` enforces per-row identities and empty-frame guard; the Run gate requires all keys; loader `ValueError` is surfaced via the view. |
| Error handling remains explicit | ✅ PASS | Specific `ValueError`/`KeyError`/`RuntimeError`; no broad `except Exception` without re-raise. |
| Configuration / path handling is safe | ✅ PASS | Nuitka icon/output paths anchored off `REPO_ROOT` (resolved absolute), not cwd-relative or user-input-derived. |

---

## Research Log

No external research was required. All evidence is from diff inspection, the reviewer's own toolchain runs, the feature-folder evidence set, and the repository policy files under `.claude/rules/`.

---

## Verdict

The change is ready for normal PR flow. The six workstreams are implemented with small, well-typed, well-documented seams; the Qt surface is isolated from the testable presenter/service logic; and the WS5 financial-validation change is corrected (not relaxed), with genuine identity violations still raising `ValueError`. The reviewer independently reproduced a clean Black/Ruff/Pyright/Pytest pass and 100% line/branch coverage on every changed module. No Blocking or Major findings were identified; the Info/Nit items are observations, not required changes. This conclusion is consistent with the Findings Table and the **Go** readiness recommendation above.
