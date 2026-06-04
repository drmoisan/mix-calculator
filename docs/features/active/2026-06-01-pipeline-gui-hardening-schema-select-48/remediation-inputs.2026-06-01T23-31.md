# Remediation Inputs — Schema dropdown does not surface bundled default schemas (Issue #48 / PR #49)

**Cycle entry timestamp:** 2026-06-01T23-31
**Feature folder:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
**Branch:** `feature/pipeline-gui-hardening-schema-select-48`
**Head at entry:** `c526e4f`
**Base:** `main`
**Trigger:** Functional defect reported on the open #48 PR (PR #49, unmerged). The per-tab schema dropdown lists no schemas when the application is launched via `poetry run`. The two bundled default schemas (`default_aop`, `default_le`) are never offered for selection, and the auto-select-on-match path cannot match them either.

This is a remediation cycle on the open feature #48. The defect falls within #48's stated objective (WS2: "a dropdown per source tab that auto-selects a matching schema on tab activation, shows a `<Choose Schema>` placeholder when none matches"). Folding the fix into PR #49 before merge is preferred over a new issue.

---

## Confirmed Root Cause

The defect has three coupled production gaps. All three were confirmed by reading the current source and by a runtime check from `poetry run`.

### Gap 1 — Bundled defaults are never listed

`SchemaRegistry.list_schemas()` ([src/schema_registry.py:212](../../../../src/schema_registry.py#L212)) enumerates only the per-user registry directory resolved by `resolve_registry_dir` ([src/schema_settings.py:43](../../../../src/schema_settings.py#L43)). On Windows that directory is `%APPDATA%/mix-calculator/schemas`; on a fresh profile it does not yet exist and is empty. The two bundled defaults shipped in [src/schemas/](../../../../src/schemas/) are reachable only through `SchemaRegistry.load_bundled_default(name)` ([src/schema_registry.py:269](../../../../src/schema_registry.py#L269)), which is **never called in production** and whose results are never merged into the listing.

### Gap 2 — The dropdown is never populated in production

`SourceInputWidget.set_schema_list(names)` ([src/gui/widgets/source_input_widget.py:300](../../../../src/gui/widgets/source_input_widget.py#L300)) and the corresponding `SourceSelectionViewProtocol.set_schema_list` ([src/gui/protocols.py:128](../../../../src/gui/protocols.py#L128)) exist and are unit-tested, but `set_schema_list` has **zero production callers**. Nothing wires `service.list_schema_names()` into the per-tab combos at startup or on tab activation. Only the auto-select path (`set_selected_schema` driven by `discover_schema`) is wired ([src/gui/_schema_wiring.py:146](../../../../src/gui/_schema_wiring.py#L146)).

### Gap 3 — Matching cannot see the bundled defaults

`find_best_match_in_registry` ([src/schema_matching.py:430](../../../../src/schema_matching.py#L430)) builds its candidate list from `registry.list_schemas()` only. Because Gap 1 leaves that list empty on a fresh profile, `discover_schema` always returns `action="resolve"` and the auto-select path (AC-11) never fires for the bundled defaults. The placeholder-only behavior the user observes is the resolve branch firing for every source.

### Net effect

On a fresh profile, the only schemas shipped with the product (`default_aop`, `default_le`) are invisible to both manual dropdown selection and automatic matching. The feature-audit for #48 marked AC-11/AC-12 PASS because those criteria only describe auto-select and the placeholder; neither criterion required the dropdown to be **populated** with the available schemas, so this gap was not caught.

---

## Runtime Evidence (from `poetry run`)

A fresh-profile simulation (empty registry directory, no `MIX_CALCULATOR_SCHEMA_DIR` override) produced:

```
LIST=[]                 # SchemaService.list_schema_names() -> empty; dropdown source is empty
AOP=default_aop         # load_bundled_default('default_aop') succeeds
LE=default_le           # load_bundled_default('default_le') succeeds
```

The bundled files exist and parse; they are simply never surfaced. Files present: `src/schemas/default_aop.schema.json` (47 lines), `src/schemas/default_le.schema.json` (71 lines), added in commit `602b886`.

---

## Acceptance Criteria for This Remediation

These are added as remediation ACs for cycle entry 2026-06-01T23-31. The implementer must check them off in `spec.md` (extending the AC list) per the acceptance-criteria-tracking skill.

- **R-AC-1:** On a profile with an empty user registry directory and no `MIX_CALCULATOR_SCHEMA_DIR` override, the set of selectable schema names exposed to the GUI includes both `default_aop` and `default_le`.
- **R-AC-2:** A user-saved schema whose name collides with a bundled default name takes precedence over the bundled default of the same name (user override wins; no duplicate name appears in the list).
- **R-AC-3:** Each source tab's schema dropdown is populated at application startup (and/or on tab activation) with the available schema names from the schema service; `set_schema_list` has at least one production caller and the populated names include the bundled defaults per R-AC-1.
- **R-AC-4:** `discover_schema` / `find_best_match` consider the bundled defaults as candidates, so a source whose headers match a bundled default yields `action="proceed"` and auto-selects that schema (restores AC-11 for the shipped defaults).
- **R-AC-5:** Loading a selected schema by name (`SchemaService.load_schema` / the import-with-schema path) succeeds for a bundled-default name even when no user-saved file of that name exists.
- **R-AC-6:** The change is additive: the existing known-file loaders (`import_le`/`import_aop`/`import_skulu`) and the existing user-registry persistence behavior are unchanged. Existing AC-1..AC-15 remain PASS.

---

## Design Direction (non-binding; the planner owns the final design)

The repeated symptom across all three gaps is that "available schemas" is computed from the user registry directory alone. The recommended direction is to make the bundled defaults first-class participants in listing, loading, and matching through a single seam, rather than copying/seeding files onto disk at launch:

- Prefer extending `SchemaRegistry` (or the `SchemaService`) so that `list_schemas()`/`list_schema_names()`, `load()`/`load_schema()`, and the registry-backed matching all consider the union of bundled defaults and user-saved schemas, with user-saved entries overriding bundled entries of the same name. This makes `find_best_match_in_registry` see the bundled defaults automatically.
- Avoid a first-run "copy bundled files into `%APPDATA%`" approach unless the planner finds a strong reason; it adds launch-time disk side effects and a divergence risk if bundled defaults change between releases.
- Wire dropdown population (`set_schema_list(service.list_schema_names())`) into the composition root / source-selection presenter so each tab's combo is filled at startup and/or on tab activation, alongside the existing auto-select wiring.

---

## Constraints

- **Toolchain (Python):** Black -> Ruff -> Pyright -> Pytest must pass in a single clean pass (`.claude/rules/python.md`).
- **Coverage:** >= 85% line, >= 75% branch; no regression on changed lines (`.claude/rules/quality-tiers.md`).
- **File-size cap:** no production/test/script file may exceed 500 lines. Note `src/gui/app.py` was reported at 499/500 during #48; do not grow it in place — extract if wiring must live near the composition root. The new modules added in #48 (`_run_wiring.py`, `_key_mismatch_seam.py`, `_key_mismatch_dialog.py`) are precedent for small wiring modules.
- **Tests:** unit tests for the listing/loading/matching union and override behavior; GUI tests (offscreen, `QT_QPA_PLATFORM=offscreen`) for dropdown population wiring. No temp files, no real network/disk in unit tests; the registry's injectable `SchemaFileStore` already supports an in-memory fake for bundled+user fixtures.
- **No confidential figures:** no real workbook values in any committed artifact (AC-15 still applies).
- **Additive only:** do not alter the known-file loader defaults or existing user-registry semantics beyond surfacing bundled defaults.

---

## Out of Scope

- Re-opening WS1/WS3/WS4/WS5 behavior (already PASS in the #48 feature-audit).
- Any change to the bundled schema JSON content itself.
- Packaging/Nuitka changes (WS1b) — unless the planner determines bundled-default resolution differs under a packaged build, in which case that is a new finding and a new cycle per the scope-change rule.

---

## Delegation Plan For This Cycle

1. `atomic-planner` authors `remediation-plan.2026-06-01T23-31.md` against this inputs file and the `atomic-plan-contract`.
2. `atomic-executor` runs preflight; revise loop with `atomic-planner` until `PREFLIGHT: ALL CLEAR`.
3. `atomic-executor` executes the approved plan task-by-task (workers invoked only by the executor).
4. `feature-review` produces `code-review`, `feature-audit`, and `policy-audit` at cycle exit.
5. Orchestrator computes `blocking_count`; exit when `blocking_count == 0`, else open cycle N+1.
