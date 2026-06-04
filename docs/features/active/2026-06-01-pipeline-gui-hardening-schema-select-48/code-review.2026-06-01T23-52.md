# Code Review: Surface bundled default schemas (Issue #48 / PR #49, remediation cycle exit)

**Review Date:** 2026-06-01
**Cycle exit timestamp:** 2026-06-01T23-52
**Feature Folder:** `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48`
**Base Branch:** `main` (merge base `1df33019b31bbeb73fb96bc0490ffb3cc4bba288`)
**Head Branch:** `feature/pipeline-gui-hardening-schema-select-48` (working tree, uncommitted remediation edits on top of `c526e4f`)
**Work Mode:** `full-feature`
**Review Type:** Remediation-cycle exit re-review (bundled-default-schema fix)

---

## Scope

This review covers the working-tree remediation changes implementing the bundled-default-schema
fix. The full branch diff against `main` was inspected; the remediation-specific production changes
are:

- `src/schema_registry.py` (MODIFIED) — `list_schemas` now returns the deduplicated union of
  user-saved and bundled-default names; new private helper `_list_bundled_names`; `load` falls back
  to the bundled-defaults directory when no user-saved file exists.
- `src/gui/_schema_list_wiring.py` (NEW, 62 lines) — composition-root helper
  `populate_schema_lists` that calls `view.set_schema_list(service.list_schema_names())` per view.
- `src/gui/app.py` (MODIFIED) — one import plus one call site invoking `populate_schema_lists` in
  `build_application`.
- Tests (MODIFIED/NEW): `tests/test_schema_registry.py`, `tests/test_schema_matching_registry.py`,
  `tests/gui/test_schema_service.py`, `tests/gui/test_app_wiring_schema_list.py` (NEW).

The original #48 production scope (WS1a/WS1b/WS3/WS4/WS5/WS2 widget work) was reviewed and approved
in `code-review.2026-06-01T15-30.md`; this cycle re-confirms no regression to that work and reviews
only the remediation delta in depth.

---

## Executive Summary

The remediation delta is correct, additive, and policy-compliant. All four Python toolchain stages
were independently reproduced by the reviewer and pass in a single clean pass (Black, Ruff, Pyright,
Pytest with coverage). No Blocking, High, Medium, or change-requiring Low findings were identified.
No suppressions were added. The original #48 work shows no regression. Verdict: Approved.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|----------|------|----------|---------|----------------|-----------|----------|
| Info | src/schema_registry.py | `list_schemas` / `_list_bundled_names` | Union computed via `set(user_names) \| set(self._list_bundled_names())` then `sorted`. Deterministic ordering and single-source-of-truth dedup. Store-backed, no direct `pathlib` I/O. | None. | Matches the single-seam design direction in the remediation plan; keeps the I/O boundary inside the injected store. | `git diff src/schema_registry.py`; `tests/test_schema_registry.py::test_list_schemas_includes_bundled_when_user_dir_empty` |
| Info | src/schema_registry.py | `load` | Resolution order is user-path-first then bundled-path fallback then explicit `SchemaRegistryError`; the error message now names both directories. Fails fast and explicitly per `general-code-change.md`. | None. | User-override precedence is preserved; the error path is specific, not swallowed. | `tests/test_schema_registry.py::test_load_colliding_name_returns_user_saved_schema`, `::test_load_unknown_name_raises_when_in_neither_location` |
| Info | src/gui/_schema_list_wiring.py | whole module | Module docstring, Google-style function docstring, `__all__`, `TYPE_CHECKING`-guarded imports (Qt-free at runtime), single intent comment per block. Separation of concerns held: view population only, no domain/matching logic. | None. | Conforms to `self-explanatory-code-commenting.md` and `python.md` small-cohesive-module guidance; follows the `_run_wiring.py` precedent. | `src/gui/_schema_list_wiring.py` lines 1-62 |
| Info | src/gui/app.py | `build_application` call site | Addition limited to one import and one call; no inline population logic, preserving the 500-line cap headroom. File is at exactly 500 lines (at the cap, not over). | None. | Honors the spec's hard cap constraint and the plan's extract-not-inline directive. | `wc -l src/gui/app.py` = 500; `awk 'END{print NR}'` = 500 |
| Info | tests (all four files) | new R-AC tests | All new tests use the in-memory `InMemoryFileStore` / fakes; no temp files, no real disk, no network. AAA structure; descriptive names; one behavior per test. | None. | Conforms to `general-unit-test.md` (independence, isolation, determinism) and the no-temp-file prohibition. | `tests/test_schema_registry.py:213-327`, `tests/gui/test_schema_service.py:131-157`, `tests/gui/test_app_wiring_schema_list.py:56-87` |

No Blocking, High, or Medium findings. No Low findings requiring change.

---

## Best-Practice Assessment

- **Simplicity / single seam:** The fix resolves all three documented gaps (listing, matching,
  load-by-name) at one source — the union-aware registry — rather than seeding files to disk at
  launch. No launch-time disk side effects were added. This is the simplest correct design.
- **Reusability:** Matching (`find_best_match_in_registry`) and the service
  (`list_schema_names`/`load_schema`) already delegate to the registry, so no duplicate union logic
  was introduced at those layers; they inherit the fix.
- **Extensibility / SoC:** Dropdown population lives in its own wiring module; pure registry logic
  is separate from Qt glue and from the composition root.
- **Error handling:** `load` fails fast with a specific `SchemaRegistryError` naming both lookup
  locations; no broad handlers, no swallowed errors, no `print`.
- **Typing:** Pyright clean (0 errors / 0 warnings). No `Any`, no new suppressions.
- **Docstrings/comments:** Updated `list_schemas`/`load` docstrings describe the union and
  precedence semantics; loops carry intent comments; no numbered notes.
- **Tonality:** Production docstrings and comments are factual and measured.

## Suppressions

No `# noqa`, `# type: ignore`, or `# pyright: ignore` added in the production or test diff
(scanned). No suppression authorization question arises this cycle.

## Toolchain (reviewer-reproduced, independent)

| Stage | Command | Result |
|---|---|---|
| Format | `env -u VIRTUAL_ENV poetry run black --check .` | EXIT 0; 187 files unchanged |
| Lint | `env -u VIRTUAL_ENV poetry run ruff check .` | EXIT 0; all checks passed |
| Type | `env -u VIRTUAL_ENV poetry run pyright` | EXIT 0; 0 errors, 0 warnings, 0 informations |
| Test | `QT_QPA_PLATFORM=offscreen env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing` | EXIT 0; 811 passed; line 99%, branch ~97% total |

## Verdict

**Approved.** No remediation-required findings. The remediation delta is correct, additive, and
policy-compliant; the original #48 work shows no regression (AC-supporting suites re-run green).
