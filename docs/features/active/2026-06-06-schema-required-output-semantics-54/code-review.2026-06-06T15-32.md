# Code Review: schema-required-output-semantics (#54)

**Review Date:** 2026-06-06
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-06-06-schema-required-output-semantics-54`
**Base Branch:** `7bfa57c` (rebased #50 HEAD immediately before #54 work; isolates the #54 delta from already-reviewed #50 work)
**Head Branch:** `feature/schema-builder-ux-overhaul-50` @ `55261bf` (rides in PR #51)
**Review Type:** Initial review (isolated #54 delta)

---

## Executive Summary

The #54 change introduces an explicit `in_output: bool = True` field on `ColumnSpec` and switches the schema loader's output determination from `drop_columns` by-name exclusion to `in_output` inclusion (plus `KEY` and derived columns, in schema order). `required` keeps its source-presence meaning, so `resolve_columns`/`resolve_and_rename` are unchanged. The LE discriminator `YTD/YTG` becomes `required:false, in_output:false` with `drop_columns: []`; the AOP schema gains explicit `in_output:true` on every column (AOP `YTG` stays `required:false, in_output:true`). The #50 schema-builder column-row tuple migrates from a 4-tuple to a 5-tuple end-to-end. No `SCHEMA_FORMAT_VERSION` bump.

**What changed:**
The design is the locked research option (a): additive, parity-preserving, separating source-presence (`required`) from output-membership (`in_output`). I verified the core correctness claims by inspecting `_output_column_order`, the `none`-mode emit branch, `_by_name_optional_columns`, and `_object_to_column`, and by independently running the toolchain. The discriminator is now correctly classified as a by-name-optional column (because `required=false`), so it is located by name without raising on absence, carried through `resolve_and_rename` and `collapse_by_key`, and excluded from output only at emit by `in_output=false`. The 4-tuple->5-tuple migration is complete and type-correct at every site I checked: state, presenter (`_spec_to_row`, `_state_from_schema`, dtype comprehension), columns-tab presenter (4 unpack sites + the row reassignment that now carries `in_output`), drag-tabs binder, dialog, the view protocol, and both fakes/fixtures. Pyright reports 0 errors, which independently confirms no missed unpack site.

**Top 3 risks:**
1. Low: the `none`-mode emit now keeps any frame column not declared in the schema "by default" (only declared `in_output=false` columns are excluded). For AOP, all output columns are declared, so behavior is unchanged and the AOP parity test passes; this is a deliberate, documented choice rather than a defect.
2. Low: `drop_columns` remains in the JSON shape and serialization but is no longer consulted for output. A future author could set it expecting an effect; this is documented in the spec as intentional backward-compatibility retention.
3. Low: the provider-factory split keys on `column.required`, so any future schema that marks an output column `required:false` would land in the optional specs — correct for `YTG`/`YTD/YTG` today and consistent with the loader, but worth keeping in mind for the builder UX.

**PR readiness recommendation:** **Go** — The #54 delta is correct, parity-preserving, fully migrated, and toolchain-clean. No follow-up required.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/_schema_loader_helpers.py` | `emit_output_columns` none-mode (~451-461) | The `none` path excludes only declared `in_output=false` columns; undeclared frame columns are kept by default. | No change needed; keep the inline comment that documents this. | Preserves AOP's un-reordered validated frame and matches `load_aop`; AOP parity test confirms byte-identity. | AOP parity (4 tests) pass; inspected diff. |
| Info | `src/schema_model.py` / `src/schema_serialization.py` | `drop_columns` field | `drop_columns` retained in shape but unused for output. | Leave as-is (documented compatibility decision). | Intentional per spec Non-Goals; no code consults it for output (verified by grep). | `git grep drop_columns` shows only docstrings, the field definition, and serialization read/write. |
| Nit | `src/gui/presenters/schema_builder_presenter.py` | dtype comprehension (~343-347) | The 5-tuple unpack uses a parenthesized continuation for line length. | None. | Stylistic only; Black-clean. | Black check clean. |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The output-determination switch is minimal and readable: `_output_column_order` reduces to `[c.canonical_name for c in schema.columns if c.in_output]`, and the derived-insertion loop dropped its `drop` membership test cleanly.
- The discriminator handling required no new control flow. Because `_by_name_optional_columns` already iterated `if not column.required`, marking `YTD/YTG` as `required:false` automatically routed it through the by-name-optional resolution path (located by name, no fuzzy, tolerant of absence) and through `collapse_by_key` as the dedup discriminator. Exclusion happens only at emit. This is the correct, generalizing design and matches the spec's dedup-discriminator requirement.
- The `ColumnSpec` docstring gained a dedicated "Required vs. in_output" section that states the three genuinely-different cases (`KEY`, LE `YTD/YTG`, AOP `YTG`), satisfying the self-explanatory-commenting rule with intent rather than narration.
- Serialization is correctly additive: emit writes `in_output`, parse reads it with `optional_bool(..., default=True)`, and `in_output` was added to `_COLUMN_KEYS` so `reject_unknown_keys` still accepts it. Legacy JSON without the key parses as `True`. No version bump, consistent with the additive-with-safe-default rationale.

#### Typing and API notes

- `ColumnSpec.in_output: bool = True` is a defaulted dataclass field placed after `required` and before `aliases`. Because `ColumnSpec` is constructed by keyword everywhere I inspected (loader tests, serialization, `assemble_schema`), the positional insertion is safe.
- The 4-tuple->5-tuple migration updated every annotation to `tuple[str, str, bool, bool, tuple[str, ...]]` in the state field, the view protocol `set_columns`/`get_columns`, the dialog, the drag-tabs binder, and both fakes. Pyright 0 errors confirms no annotation was missed.
- `assemble_schema` forwards `in_output=in_output` into `ColumnSpec(...)`, and `_spec_to_row`/`_state_from_schema` carry the flag in both directions, so schema -> state -> schema round-trips preserve `in_output` (verified by `test_assemble_schema_*` and presenter tests).

#### Error handling and logging

- No new exception handling or logging was introduced. Existing serialization validation (`reject_unknown_keys`, `optional_bool`) is reused. No broad catches, no `print`, no suppressions (git-diff scan confirms).

---

## Test Quality Audit

The change is backed by targeted behavioral tests plus the protected parity tests. I independently ran the #54-relevant subset (54 tests, 1.64s, all pass) and the full suite (966 pass, ~23s).

### Reviewed test and QA artifacts

- `tests/test_schema_loader_derived.py` — new `_membership_schema`/`_membership_frame` fixtures parametrize the discriminator's `in_output` to prove inclusion, exclusion, and "used-for-dedup-yet-excluded" (collapsed two rows, summed `Amt` to 15.0, discriminator absent). Strong behavioral coverage of AC-2 and AC-5.
- `tests/test_schema_serialization.py` — `test_absent_in_output_defaults_to_true` uses an inline legacy-JSON string (no temp file) to prove the additive default; `test_in_output_false_round_trips` proves round-trip preservation; the property test `_draw_column` now draws `in_output` independently of `required`, exercising all four combinations. Covers AC-6.
- `tests/gui/test_schema_builder_assemble.py` (new) — proves `assemble_schema` forwards both True and False `in_output` and that `required` is forwarded independently. Covers AC-7.
- `tests/gui/test_schema_provider_factory.py::test_real_bundled_le_ytd_ytg_is_in_optional_specs` — loads the real bundled LE schema and asserts `YTD/YTG` lands in optional (not required) specs. Covers AC-7 provider-factory split.
- `tests/test_default_schemas.py::test_le_drops_ytd_ytg_source_column` — updated to assert `drop_columns == ()`, `required is False`, `in_output is False`. Covers AC-1.
- `tests/test_schema_loader_parity_le.py` (5) and `tests/test_schema_loader_parity_aop.py` (4) — the top invariant; both pass unchanged, confirming byte-identical output to the protected loaders.
- `evidence/qa-gates/final-coverage-delta.md` — documents 99.07% line / 94.15% branch with per-module breakdown; matches my independent re-run exactly.

### Quality assessment prompts

- **Determinism:** No wall-clock, RNG outside the seeded Hypothesis config, sleeps, or network. In-memory DataFrames and inline JSON strings.
- **Isolation:** Each test targets one behavior; the parametrized discriminator fixture keeps inclusion/exclusion cases distinct.
- **Speed:** 54 targeted tests in 1.64s; full suite ~23s.
- **Diagnostics:** Behavioral assertions on column presence and summed measures give clear failure signals.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff adds a boolean field and JSON flags; no secrets. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess code in the diff. |
| Input validation at boundaries | ✅ PASS | Serialization retains `reject_unknown_keys`/`optional_bool`; absent `in_output` defaults safely. |
| Error handling remains explicit | ✅ PASS | No broad handlers added; existing fail-fast behavior preserved. |
| Configuration / path handling is safe | ✅ PASS | Bundled-schema JSON edits are flag-only; the provider-factory test reads a packaged read-only resource. |
| Parity with protected loaders preserved | ✅ PASS | LE (5) + AOP (4) parity tests pass; protected loaders unmodified (not in diff). |

---

## Research Log

No external research required. All findings derive from diff inspection, the feature folder spec/plan/issue, the project policy rules, and an independent local toolchain run.

---

## Verdict

The #54 delta is correct and complete. The `in_output` inclusion model is implemented cleanly in `_output_column_order` and the `none`-mode emit branch; the discriminator is carried through dedup and excluded only at emit; serialization is additive with a safe default and no version bump; and the builder 4-tuple->5-tuple migration is type-correct at every site (Pyright 0 errors). Parity with the protected loaders holds byte-for-byte. There are no Blocker or Major findings; the three recorded findings are Info/Nit and require no action. The change is ready for normal PR flow within PR #51.
