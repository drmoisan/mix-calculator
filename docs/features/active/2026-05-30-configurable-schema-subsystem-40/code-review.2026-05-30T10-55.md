# Code Review: configurable-schema-subsystem (Epic #40)

**Review Date:** 2026-05-30
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-05-30-configurable-schema-subsystem-40`
**Feature Folder Selection Rule:** Epic folder whose suffix `-40` matches the branch name `epic/configurable-schema-subsystem-40`; audit artifacts consolidated at the epic root per the caller brief.
**Base Branch:** `main` (merge-base `d14d4e9`)
**Head Branch:** `epic/configurable-schema-subsystem-40` (`04dba2a`)
**Review Type:** Initial review

---

## Executive Summary

The branch implements the configurable-schema epic across four child features. Feature A (#41) adds the typed, frozen-dataclass schema model, a JSON serialization adapter, a settings-resolved shared registry with an injectable file-I/O boundary, and the bundled default AOP/LE schemas. Feature B (#42) adds a non-raising column probe and a deterministic best-match scorer with a typed mismatch report, reusing the existing resolver's fuzzy logic. Feature C (#43) adds the schema-driven `SchemaLoader` (resolve/key/fill/coerce/dedup/derived/output) and a sandboxed `asteval` formula engine validated by stdlib `ast` before evaluation, with ratio recompute via `safe_div`. Feature D (#44) adds the PySide6 schema-builder dialog, manual column-matching dialog, runtime formula entry, a `SchemaService` seam, and import-flow discovery, wired into the existing GUI with additive, behavior-preserving edits.

**What changed:** About 14,600 added lines across 124 files; 50 new `src` modules, 27 new/changed test modules, one new typed stub (`typings/asteval/__init__.pyi`), additive edits to four existing GUI modules, and `pyproject.toml`/`quality-tiers.yml` updates. The pre-existing loaders, transforms, CLI, and Feature A/B/C source remain unmodified (verified by the protected-files diff scans in each child evidence folder and confirmed independently).

**Top 3 risks:**
1. Formula-engine sandbox is the primary security surface. The defense is sound (ast-level rejection of imports/attribute access/subscript/comprehension/lambda/assignment/non-whitelisted calls, then a constrained symtable with `minimal=True`, `use_numpy=False`, `no_print=True`), but it depends on the whitelist staying exhaustive; mutation testing for the T1 modules is deferred to the pre-merge/nightly pipeline and not yet evidenced.
2. Nine unauthorized `# noqa: E402` suppressions on shared-fixture imports (procedural, not a code defect).
3. One modified test file exceeds the 500-line ceiling (`tests/gui/fakes/fake_views.py`, 508 lines).

**PR readiness recommendation:** **Conditional Go** — implementation quality is strong and the toolchain is clean; the two procedural findings (E402 authorization, test-file size) should be resolved before merge.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Minor | `tests/test_schema_loader_core.py`, `tests/test_schema_loader_derived.py`, `tests/test_schema_loader_integration.py`, `tests/test_schema_loader_parity_aop.py`, `tests/test_schema_loader_parity_le.py`, `tests/gui/integration/test_behavioral_schema_import.py` | fixture-import lines (e.g. `:34-35`) | 9 `# noqa: E402` suppressions silence module-level-import-not-at-top after a deliberate `sys.path.insert`. E402 is not pre-authorized in `python-suppressions.md` and has no recorded explicit approval. | Move shared in-memory fixtures into a real package importable without `sys.path` manipulation (e.g. a `tests/fixtures/` package or a `conftest.py` fixture), OR record explicit user approval for E402 in tests, OR add a pre-authorized E402 pattern with a required comment format. | Suppression authorization is a procedural gate (pattern-match OR explicit approval); the code is locally safe but unauthorized. | `grep -rn 'noqa: E402' tests/`; `python-suppressions.md` pre-authorized list. |
| Minor | `tests/gui/fakes/fake_views.py` | whole file | File is 508 lines, exceeding the 500-line ceiling that applies to test code per `general-code-change.md`. | Split the fake-view classes into per-protocol modules (e.g. `fake_schema_builder_view.py`, `fake_column_matching_view.py`) under `tests/gui/fakes/`. | The 500-line ceiling explicitly covers test code; only documentation/markdown and throwaway scripts are exempt. | `wc -l tests/gui/fakes/fake_views.py` -> 508 (was 218 at base `d14d4e9`). |
| Info | `quality-tiers.yml` / T1 modules | `src/schema_formula.py`, `src/schema_loader.py` | T1 mutation score (>= 75%) is not evidenced in this branch. | Confirm mutation results in the pre-merge/nightly pipeline; not required for the per-commit feature-review loop. | `quality-tiers.md` runs mutation in pre-merge/nightly, not per-commit. | `quality-tiers.md` gate matrix. |
| Info | `src/gui/pipeline_service.py` | `import_with_schema` (line ~318) | Local `from src.schema_loader import SchemaLoader` inside the method (deliberate, to keep the module import surface unchanged for callers that never use the schema path and to avoid an import cycle). | None — documented and justified in the docstring/comment. | Acceptable pattern; noted for transparency. | Diff inspection of `pipeline_service.py`. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The formula engine separates validation from evaluation cleanly: `FormulaEvaluator.validate` parses in `eval` mode and walks the AST to reject a fixed forbidden-node set and any non-whitelisted callee before evaluation, so a rejected construct can never reach `asteval`. The symtable handed to the interpreter contains only the whitelisted callables, the row's column values keyed by deterministic identifier aliases, and a `col` accessor — a tight allowlist.
- The `asteval` boundary is typed with a narrow local stub (`typings/asteval/__init__.pyi`) declaring only the constructor params, `symtable`, `error`, and `__call__` the adapter uses, with no `Any` and no `# type: ignore`. This satisfies AC7 of #43 and matches the repo's established typed-adapter pattern for unstubbed libraries.
- `safe_div` is polymorphic over scalars and pandas Series, which lets the loader recompute ratio columns element-wise from summed dollars/volume while preserving dtype parity with the protected loaders.
- The 500-line ceiling drove disciplined module splits (`_schema_formula_helpers`, `_schema_loader_helpers`, `_schema_matching_helpers`, `_schema_builder_tabs`, `_schema_builder_state`), each re-exporting through its public module — production files all stay under 500.
- Feature B reimplements the resolver's fuzzy-selection logic locally rather than importing the resolver's private `_best_fuzzy_index`, avoiding a `reportPrivateUsage` strict-mode violation while leaving the protected resolver byte-for-byte unchanged; resolver-parity tests assert identical bindings.

#### Typing and API notes

- New public API: `SchemaServiceProtocol`, `ColumnMatchingViewProtocol`, `SchemaBuilderViewProtocol`, `PipelineServiceProtocol.import_with_schema`, the `schema_*` modules, and `FormulaEvaluator`/`SchemaLoader`. Protocols are used for the GUI seams; frozen dataclasses model schema data with `__post_init__` invariants. Pyright strict passes with zero errors.

#### Error handling and logging

- `FormulaError` is the single engine-level exception with descriptive messages naming the offending construct/column. `asteval` accumulates errors rather than raising; the adapter inspects `interpreter.error` and surfaces the first as `FormulaError`. `pipeline_service.import_with_schema` logs via `logger.info` and propagates `ValueError`/`FormulaError`. No broad `except` introduced.

---

## Test Quality Audit

The verification evidence in each child feature's `evidence/qa-gates/` folder records green Black/Ruff/Pyright/Pytest runs with coverage. This review independently re-ran the full toolchain on the working tree at head and confirmed: Black PASS, Ruff PASS, Pyright strict 0 errors, Pytest 717 passed, repo-wide coverage 99.12% line / 96.46% branch.

### Reviewed test and QA artifacts

- `artifacts/python/lcov.info` (2026-05-30T09:46) — per-file coverage; all feature files >= 85% line / >= 75% branch; T1 loader/formula at 100%.
- `docs/features/active/2026-05-30-configurable-etl-core-43/evidence/qa-gates/final-pytest-coverage.2026-05-30T09-20.md` — Feature C green pytest+coverage.
- `docs/features/active/2026-05-30-gui-schema-builder-44/evidence/qa-gates/final-pyright.2026-05-30T08-40.md` — Feature D pyright strict green.
- `docs/features/active/2026-05-30-schema-matching-and-discovery-42/evidence/regression-testing/protected-files-diff.2026-05-30T07-59.md` — protected loaders/transforms unchanged.
- `tests/test_schema_loader_parity_le.py` / `_aop.py` — exact-parity assertions vs `normalize`/`load_aop` (AC1/AC2 of #43).

### Quality assessment prompts

- **Determinism:** No `time.sleep`/threads/`datetime.now()` in added tests; Hypothesis property tests for scoring determinism and formula rejection. Schema aliases built deterministically from column order.
- **Isolation:** Each test targets one behavior; registry tested via injectable in-memory file store; presenters tested without `QApplication`.
- **Speed:** 717 tests in 18.08s.
- **Diagnostics:** Assertions check exception types and message content; `assert_frame_equal` gives precise parity diffs.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No credentials/keys in the diff; `asteval` is a public PyPI package. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess use introduced. |
| Input validation at boundaries | ✅ PASS | Formula expressions validated with `ast` before evaluation; schema `__post_init__` enforces structural invariants; JSON adapter raises descriptive errors on malformed/unknown keys. |
| Error handling remains explicit | ✅ PASS | `FormulaError`/`ValueError` with messages; no silent swallowing. |
| Configuration / path handling is safe | ✅ PASS | Registry directory resolved via settings/env-override seam, tested without disk; default disk-backed service built from `os.environ`/`sys.platform`/`Path.home()`. |
| Formula sandbox rejects unsafe constructs | ✅ PASS | `_FORBIDDEN_NODES` rejects import/attribute/subscript/comprehension/lambda/assignment/starred; non-whitelisted calls rejected; symtable constrained; `use_numpy=False`, `minimal=True`, `no_print=True`. Hypothesis unsafe-expression corpus covers rejection. |

---

## Research Log

No external research was required. The review relied on diff inspection, independent toolchain execution, the canonical PR-context artifacts, and the per-feature evidence folders.

---

## Verdict

The configurable-schema subsystem is implemented to a high standard: additive design, strict typing with a properly stubbed `asteval` boundary, a defense-in-depth formula sandbox, exact-parity tests against the protected loaders, and coverage well above policy thresholds with a clean four-stage toolchain. The change is ready for normal PR flow after two minor, procedural follow-ups: authorize or eliminate the nine `# noqa: E402` suppressions, and split `tests/gui/fakes/fake_views.py` below the 500-line ceiling. There are no Blocker or Major findings and no code-correctness, security, or coverage defects. This verdict is consistent with the Findings Table and the Conditional Go recommendation above.
