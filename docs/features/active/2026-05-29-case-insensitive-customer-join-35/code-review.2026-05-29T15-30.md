# Code Review: case-insensitive-customer-join (Issue #35)

**Review Date:** 2026-05-29
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-05-29-case-insensitive-customer-join-35/`
**Feature Folder Selection Rule:** Selected because the branch name `feature/case-insensitive-customer-join-35` and `issue.md` declare canonical issue #35; no other active feature folder matches.
**Base Branch:** `feature/app-rename-and-real-icon-33` (PR #34 HEAD; #35 stacked on it)
**Head Branch:** `feature/case-insensitive-customer-join-35` (commit `cc4a7399776890f2739a30130fd2093654ceae52`)
**Review Type:** Initial review

---

## Executive Summary

This minor-audit change makes the AOP-vs-LE Customer join in the mix-decomposition pipeline case-insensitive and whitespace-insensitive. Diagnostic work traced an `nrr_summary.Check = ERROR` outcome for two Winco SKUs to a Customer-name casing inconsistency (`Winco` vs `WINCO`) between the AOP and LE sides of the comparison; the change introduces a casefolded join key, applies whitespace stripping on display Customer values in three frame builders, and re-attaches an AOP-priority display column after the pivot.

**What changed:**
- `src/mix_lookups.py`: adds module-private `_customer_join_key(s: pd.Series[str]) -> pd.Series[str]` helper; applies `.str.strip()` to `Customer` in `build_customer_lu`, `build_aop_norm`, `build_le_norm`; pivots `build_aop_vs_le` on the casefolded key and re-attaches the display Customer via two left-merges (AOP wins; LE fills LE-only orphans). Public contract unchanged.
- `tests/test_mix_lookups_casefold.py`: 296 lines, 6+ new tests covering casefold collapse, whitespace collapse, AOP-display precedence, LE-only retention, and a Winco/WINCO end-to-end synthetic fixture.
- `tests/test_mix_lookups.py`: +5 lines for a pointer comment to the new file (no assertion changes).
- `tests/test_mix_pipeline.py`: +28 lines for `test_mix_pipeline_nrr_summary_check_ok` smoke test.

Evidence reviewed: the full `qa-gates/*.2026-05-29T13-45.md` set (Black, Ruff, Pyright, Pytest, file-size, AC verification), the regression-testing `fail-before-*.md` set, the issue and plan documents, and direct inspection of `src/mix_lookups.py`.

**Top 3 risks:**
1. The `astype(str)` cast inside `build_aop_vs_le` converts NaN Customer values to the literal string `"nan"`. The code documents this as intentional (matches the pre-change pivot's behavior), but downstream consumers should not treat `"nan"` as a sentinel; this contract is preserved, not improved.
2. When a single Customer key appears under multiple casings on the AOP side, `drop_duplicates(subset="_customer_key", keep="first")` selects an order-dependent display value. The code calls this out with a WARNING comment, but the chosen value depends on the input row order. For the canonical workbook this is benign; downstream code should not depend on a stable casing across runs if AOP input order changes.
3. `tests/test_mix_lookups.py` at 365 lines is below the 500-line cap but on a steady upward trend; future Customer-related work should consider where to land tests so neither file approaches the cap.

**PR readiness recommendation:** **Go** — All four toolchain stages pass single-loop with EXIT_CODE 0; module coverage is 100% line + 100% branch; the public contract is preserved; both noted edge-case behaviors are documented inline with WARNING comments.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/mix_lookups.py` | line 179 | `astype(str)` converts NaN Customer values to the literal string `"nan"`. | Preserve as-is. The behavior is documented in an inline `WARNING` comment and matches the pre-change pivot. No action required; flag only because downstream consumers should not treat `"nan"` as a sentinel. | Behavior preservation is explicit and intentional; no contract break. | Read `src/mix_lookups.py` lines 173-180. |
| Info | `src/mix_lookups.py` | lines 206-211 | AOP-side display casing is selected by `drop_duplicates(subset="_customer_key", keep="first")`, so multi-casing AOP inputs select an order-dependent value. | Preserve as-is for this scope. The behavior is documented in an inline `WARNING` comment. If a future requirement needs a deterministic casing rule (e.g., the first lexicographic casing or the most-frequent casing), implement it in a follow-up. | Edge case explicitly called out; not in scope for issue #35. | Read `src/mix_lookups.py` lines 206-219. |
| Info | `tests/test_mix_lookups.py` | full file | File is 365 lines; combined with the new `tests/test_mix_lookups_casefold.py` (296 lines), the split keeps both under the 500-line cap. | Preserve the split. Future Customer-related tests should target `test_mix_lookups_casefold.py` or a third sibling rather than re-expanding the original. | Tracks the policy `[issue2 file-size watch]` memory: tests near this module trend toward the cap. | `evidence/qa-gates/final-file-size.2026-05-29T13-45.md`. |
| Nit | `src/mix_lookups.py` | line 79 (helper signature) | `_customer_join_key` is module-private; the docstring is Google-style and accurate. | No change. | Confirms naming and documentation conformance for the new helper. | Read `src/mix_lookups.py` lines 62-78. |

No Blockers or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- The new helper `_customer_join_key` is a single-purpose, fully typed (`pd.Series[str] -> pd.Series[str]`) pure function with a Google-style docstring that explicitly notes input casing is not preserved on the return value and the caller is responsible for re-attaching the display column. This is the smallest reasonable seam for the change.
- The re-attach pattern via two left-merges followed by a `fillna(...)` for LE-only orphans is straightforward to read and to test. The dropped helper columns (`_customer_key`, `_customer_le`) keep the public contract intact.
- The `for scenario in ("AOP", "LE"):` block defensively materializes both columns when one scenario is empty, avoiding `KeyError` on the subsequent `wide["AOP"].fillna(0)`. The comment "Ensure both scenario columns exist and are zero-filled before the diff" captures intent succinctly.
- The choice of `casefold()` over `lower()` is documented in `issue.md` Design Notes (Turkish I, German ß) and is the standard pandas idiom for case-insensitive comparison.

#### Typing and API notes

- The helper signature is precise: `pd.Series[str] -> pd.Series[str]`. Pyright passes with EXIT_CODE 0 across the full repo.
- The four touched public functions retain their existing `pd.DataFrame -> pd.DataFrame` signatures. The output column layout is unchanged (`{Customer, SKU #, Attribute, AOP, LE, Diff, Classification}` for `build_aop_vs_le`; same for the three normalization helpers).
- No new `Any`, `cast`, `# type: ignore`, or `# noqa` is introduced. Verified by diff inspection and by `final-ruff.2026-05-29T13-45.md` / `final-pyright.2026-05-29T13-45.md`.

#### Error handling and logging

- No new exception paths are added. The pure-pandas transform raises whatever pandas itself raises on malformed input. This is consistent with the existing module style (no try/except).
- No print or logging added. The module remains logging-free as a pure transform; orchestration logging lives in `src.mix_pipeline`.

---

## Test Quality Audit

The change is exercised by 10 new tests plus the unchanged preexisting suite. The full pytest run (507 tests) completes EXIT_CODE 0 in a single loop. New tests are deterministic, in-memory, and follow Arrange-Act-Assert.

### Reviewed test and QA artifacts

- `tests/test_mix_lookups_casefold.py` — 296 lines, 6+ new tests covering three-casing collapse, leading/trailing whitespace collapse, AOP-display win, LE-only retention, five-casing collapse, and a Winco/WINCO Off-Invoice + Non-Trade synthetic fixture.
- `tests/test_mix_lookups.py` — preserved assertions; +5 lines for a pointer comment.
- `tests/test_mix_pipeline.py` — adds `test_mix_pipeline_nrr_summary_check_ok` smoke test against an in-memory fixture, replacing the canonical-workbook test that requires an artifact not present in the worktree (decision recorded in `phase4-e2e-decision.2026-05-29T13-35.md`).
- `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/final-pytest.2026-05-29T13-45.md` — 507 pass; 100% line + 100% branch on `src/mix_lookups.py`.
- `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/qa-gates/ac-verification.2026-05-29T13-45.md` — all 10 ACs PASS with evidence cross-links.
- `docs/features/active/2026-05-29-case-insensitive-customer-join-35/evidence/regression-testing/fail-before-*.md` — confirms each new positive test failed before the implementation, demonstrating it exercises the changed behavior rather than a degenerate baseline.

### Quality assessment prompts

- **Determinism:** No clock, RNG, network, filesystem, or wall-clock waits used. Inputs are literal DataFrame constructions.
- **Isolation:** Each test name encodes one behavior; failure messages from `pd.testing.assert_frame_equal` will identify the offending DataFrame.
- **Speed:** Final pytest of 507 tests is reported by the qa-gates artifact as a single-loop pass; no slow tests flagged.
- **Diagnostics:** Fail-before artifacts contain assertion output, confirming readable failure modes (pandas frame diff).

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | PASS | Only DataFrame column names and string literals (`"AOP"`, `"LE"`, `"Cases"`, attribute names) appear. Verified by direct read of `src/mix_lookups.py`. |
| No unsafe subprocess or command construction | PASS | No subprocess use in the change. |
| Input validation at boundaries | PASS | Module is pure-transform; inputs are typed pandas frames. `astype(str)` is applied before casefold to defend against mixed-type Customer columns (documented as preserving the pre-change behavior). |
| Error handling remains explicit | PASS | No new try/except; pandas exceptions propagate. |
| Configuration / path handling is safe | N/A | No paths or configuration handled in this module. |

---

## Research Log

No external research was required. All findings are grounded in repo policy files (`.claude/rules/*.md`), the issue and plan documents in the active feature folder, and direct inspection of `src/mix_lookups.py`.

---

## Verdict

The change implements its scoped objective cleanly: a casefolded join key, whitespace-stripped display Customer values, and an AOP-priority display re-attach. The public contract is preserved, all four toolchain stages pass single-loop, and module coverage is 100% line + 100% branch. The two `Info`-level findings (NaN-to-`"nan"` cast and order-dependent AOP-display selection) are documented inline with `WARNING` comments and are intentional behavior-preservation choices rather than defects.

**Ready for normal PR flow.** No follow-ups required for this scope. The branch is stacked on PR #34 and should be sequenced behind it per the issue's stated branching strategy.
