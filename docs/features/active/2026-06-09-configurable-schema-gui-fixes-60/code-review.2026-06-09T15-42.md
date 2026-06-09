# Code Review: configurable-schema-gui-fixes (Issue #60)

**Review Date:** 2026-06-09
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-06-09-configurable-schema-gui-fixes-60/`
**Base Branch:** `main` (merge-base 1d27514)
**Head Branch:** `fix/configurable-schema-gui-fixes` (head 4856661)
**Review Type:** Initial review

---

## Executive Summary

This branch bundles three configurable-schema GUI defects into one PR per the user's decision. Defect 1 adds an "Edit Schema" button and `edit_schema_requested` signal to `SourceInputWidget`, with construction/gating extracted to `_source_input_button_wiring.py` and composition-root wiring in `wire_edit_schema_buttons`. Defect 2 adds a bundled `default_sku_lu.schema.json` and flips `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` from `None` to `"default_sku_lu"`. Defect 3 widens schema discovery (`_HEADER_PREVIEW_ROWS` 1→5) and adds a `_best_header_row` selector so a sheet whose real header is on a later row (AOP1 index 2) auto-matches, with a first-row fallback that preserves LE/SKU_LU (row 0) behavior. The diff is moderate (7 production files plus 5 test files; ~700 production LOC added/changed). The reviewer inspected the full diff, re-ran the Python toolchain (Black/Ruff/Pyright/Pytest all clean, 1023 tests pass), and verified the production call sites for both the Edit-Schema wiring and the SKU_LU registry surfacing.

**What changed:**
The change is additive and localized. Discovery gains a bounded multi-row header selection with a documented strict-`>` tie-break (earliest equal-score row wins) and a `result.schema is None` skip so only schema-binding rows can win. The Edit path reuses the existing `open_schema_builder` wiring and then seeds via `getattr(presenter, "load_existing", None)`, guarding placeholder/empty selection at both the widget level (disabled button) and the wiring level (short-circuit). The new schema JSON mirrors the sibling `default_le`/`default_aop` shape.

**Top 3 risks:**
1. Discovery now calls `service.find_best_match` once per preview row (up to 5) on each tab activation; cost is bounded and acceptable for a user interaction, but it is a small increase over the prior single-row call.
2. The `_best_header_row` selector is independent of the import-time header detection (`_aop_schema_import.py` re-detects from the full file). The two header rows remain independently computed by design; a future divergence between discovery and import header logic would not be caught here.
3. The Edit path tolerates a presenter lacking `load_existing` (getattr guard) — intentional for test stubs, but it means a production wiring regression that dropped `load_existing` would silently skip seeding rather than fail loudly.

**PR readiness recommendation:** **Go** — The change is clean, well-tested, toolchain-clean, and the production call sites are verified; no blocking or major findings.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/gui/_schema_discovery_wiring.py` | `_open_edit` (lines 235-238) | Edit seeding uses `getattr(presenter, "load_existing", None)` and silently skips when absent. | Acceptable as-is for test-stub tolerance; optionally log a debug when seeding is skipped in production. | A dropped production `load_existing` would skip seeding without an error; low risk because the production presenter always exposes it. | Inspected `_schema_discovery_wiring.py:235-238`; `test_edit_with_stub_presenter_lacking_load_existing_does_not_crash` covers the guard. |
| Info | `src/gui/presenters/source_selection_presenter.py` | `_best_header_row` (lines 85-93) | Scores every preview row (cap 5) per discovery via `find_best_match`. | None required; bounded cost on a user interaction. | Slight increase over prior single-row matching; spec explicitly accepts the bound. | Inspected presenter lines 54-99; spec.md performance section. |
| Info | `src/gui/_schema_provider_factory.py` | line 176 | `_render_key_pattern` no-parts branch (`return None`) remains uncovered. | None; pre-existing line, not part of this change. | Not new code; SKU_LU key always has one part. | Coverage term-missing output line 176. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The header-row selection is a single, documented helper with an explicit fallback and a strict-`>` tie-break that preserves the prior row-0 behavior; the regression risk (LE/SKU_LU) is directly guarded by dedicated tests.
- Construction/gating extraction into `_source_input_button_wiring.py` keeps `source_input_widget.py` at 498 lines (under the 500 cap) while grouping reusable Qt-control helpers.
- The Edit wiring reuses the existing `open_schema_builder` path rather than duplicating dialog/presenter construction, and threads injectable factories for deterministic testing.
- The new schema JSON exactly mirrors the canonical SKU_LU columns and the sibling schema shape; it parses through the production registry, not only in a fixture.

#### Typing and API notes

- New public surface: `edit_schema_requested` signal, `edit_schema_btn` property, `wire_edit_schema_buttons`, and the `_source_input_button_wiring` helpers, all fully annotated. `SourceInputControls` is a frozen dataclass. No new `Any`. Pyright reports 0 errors.

#### Error handling and logging

- Reader errors stay narrowed to `ValueError` surfaced via the view; other exceptions propagate. The provider factory degrades to a blank spec on `(KeyError, ValueError, FileNotFoundError)` at the GUI open boundary (acceptable boundary behavior, not a silent swallow of internal logic). Discovery uses `logging` at info/error levels.

---

## Test Quality Audit

The new tests are deterministic, isolated, and behavioral. Header-row tests use a `_PerRowSchemaService` that binds a schema only for a marker-carrying row, which lets assertions prove which preview row was selected (the single-result fake could not). Edit-wiring tests drive `MainWindow` with recording dialog/presenter factories under offscreen Qt. Coverage on the changed modules is 98% line; repo-wide 99.09% line / 94.05% branch with no regression versus baseline.

### Reviewed test and QA artifacts

- `tests/gui/test_source_selection_presenter_header_row.py` — AC-7/AC-8/AC-9 header-row behavior, fallback, tie-break, blank-row no-crash. Deterministic in-memory previews.
- `tests/gui/test_edit_schema_wiring.py` — AC-2 seed via `load_existing`, AC-3 placeholder short-circuit, AC-9 no-schema seam across all three tabs, getattr tolerance.
- `tests/gui/test_source_input_widget.py` — Edit button presence and real-vs-placeholder gating.
- `tests/test_default_schemas.py` — `default_sku_lu` parse, canonical columns, Country alias, key, dedup/derived/fill/drop.
- `tests/gui/test_schema_provider_factory.py` — `sku_lu` → `default_sku_lu` mapping.
- `evidence/qa-gates/final-qc-pytest-coverage.2026-06-09T14-05.md` — executor coverage delta; reproduced by reviewer (`artifacts/python/lcov.info`).

### Quality assessment prompts

- **Determinism:** No wall-clock, randomness, network, or temp files; fakes only.
- **Isolation:** One behavior per test; fresh fixtures per test.
- **Speed:** Full suite ~32.8s on reviewer re-run.
- **Diagnostics:** Behavioral assertions on view/reader/service call records give clear failure localization.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Schema JSON uses synthetic/canonical names only; no secrets in diff. |
| No unsafe subprocess or command construction | N/A | No subprocess in the changed code. |
| Input validation at boundaries | ✅ PASS | Discovery guards blank path/sheet and empty preview; Edit guards placeholder/empty selection at widget and wiring layers. |
| Error handling remains explicit | ✅ PASS | Reader `ValueError` surfaced; other exceptions propagate; provider factory degrades only at the GUI open boundary. |
| Configuration / path handling is safe | ✅ PASS | New schema discovered via the existing registry bundled-dir mechanism; no new path construction from user input. |

---

## Research Log

No external research required. All verification was against the repository diff, the production registry/composition-root call sites, and the feature-folder evidence.

---

## Verdict

The implementation is ready for normal PR flow. The three defects are addressed with localized, additive changes that preserve existing LE/AOP/SKU_LU behavior; the Edit-Schema wiring is invoked from the composition root (`app.py:424` → `wire_schema_discovery_and_gating` → `wire_edit_schema_buttons`) and `default_sku_lu` surfaces in the live registry, both verified beyond unit assertions. The toolchain is clean and coverage thresholds are met with no regression. Only Info-level observations were recorded; there are no Blocker or Major findings. Recommendation: **Go**.
