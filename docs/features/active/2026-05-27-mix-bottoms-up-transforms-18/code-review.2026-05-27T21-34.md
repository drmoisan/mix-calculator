# Code Review: mix-bottoms-up-transforms (Issue #18)

**Review Date:** 2026-05-27
**Reviewer:** feature-review agent (Claude)
**Feature Folder:** `docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/`
**Feature Folder Selection Rule:** Active folder whose suffix (`-18`) matches the issue number and whose scoping docs (spec.md, user-story.md) are the material changes in the diff.
**Base Branch:** `main` (resolved `origin/main` @ `703de5170c37dadb8189eecc01398730d5c50e8d`)
**Head Branch:** `mix-calculator-wt-2026-05-27-20-32` @ `5ad987cd0df42df534c79248e99042ec8fe33b80`
**Review Type:** Initial review

---

## Executive Summary

The branch adds a pure-transform stage that builds three BottomsUp mix tables
(`mix_2_sku_bottomsup`, `mix_3_category_bottomsup`, `mix_4_customer_bottomsup`) and
wires them into `run_transforms`. The implementation is split across
`src/mix_bottomsup.py` (the three builders plus private assembly helpers) and
`src/_mix_bottomsup_helpers.py` (the shared contribution arithmetic and the
`classify_from_lbs` zero-test), keeping each module well under the 500-line limit.
The reviewed scope is Python only: six `.py` files, plus README, quality-tiers, and
feature docs. The diff is additive — `src/mix_pipeline.py` and `src/pandas_io.py`
are unchanged, so the new tables propagate through the existing return-dict /
persistence path.

Evidence reviewed: full branch diff via the PR-context appendix, the source and
test files, the executor QA-gate evidence, the regenerated `artifacts/python/lcov.info`,
and a reviewer re-run of Black/Ruff/Pyright/Pytest against the changed files. The
implementation quality is high: the arithmetic is faithfully factored, the
divide-by-zero and unmatched-merge guards match the documented Excel behavior, and
the formulas are covered by tie-out, branch-activation, and property tests at 100%
line/branch coverage.

**What changed:**
Three new builder functions and two shared helpers; three new call sites and three
new return-dict entries in `src/mix_pipeline_run.py`; one extended `_DERIVED_TABLES`
list in the integration test; new unit/property tests and fabricated fixtures;
README and quality-tiers updates.

**Top 3 risks:**
1. SKU-table Blended Rate / Lbs Subtotal aggregation joins `mix_1_sku` on `(Customer, Category)` without `Country` (Excel SUMIFS parity). This is a meaningful blended rate only when each `(Customer, Category)` maps to a single `Country`; the expectation is documented but not enforced or warned at runtime.
2. Classification matching is case-sensitive against lowercase tokens; an upstream casing change would silently route a row to the wrong contribution branch. Mitigated by the tie-out and branch-activation tests, but there is no defensive assertion.
3. `fillna(0)` on unmatched rollup merges is correct for the Excel no-match semantics but would also mask an unexpected genuine join miss (e.g. a key typo upstream). Low likelihood given the real-chain fixture coverage.

**PR readiness recommendation:** **Go** — Toolchain is clean in a single pass, coverage exceeds thresholds, confidentiality holds, and all 14 acceptance criteria map to passing tests. The risks above are documented design decisions, not defects.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `src/mix_bottomsup.py` | `build_mix_2_sku_bottomsup` docstring + `_aggregate_rollup_pair` join on `(Customer, Category)` | The SKU rollup aggregation omits `Country` to match Excel SUMIFS; correct only under the single-country-per-(Customer,Category) expectation. Documented but unenforced. | Optional: add a non-fatal data-quality warning at the builder boundary (spec permits it) that emits no confidential values. | A multi-country customer-category would sum rates into a non-meaningful blended rate. | spec.md Constraints & Risks; builder docstring lines 270-276 |
| Info | `src/_mix_bottomsup_helpers.py` | `build_contribution_columns` classification masks (lines 137-142) | Case-sensitive classification matching has no defensive guard; a casing drift upstream would silently zero all contributions. | Optional: assert the classification column is a subset of the known token set, or document the upstream lowercase invariant inline. | Silent mis-routing is hard to detect without a tie-out failure. | Covered indirectly by tie-out/branch tests; spec Case-sensitive note |
| Nit | `src/mix_bottomsup.py` | `_derive_net_rev_per_lb` (lines 218-227) | Docstring states the frame is "Mutated in place"; the function both mutates and returns the same frame. | Optional: keep as-is (caller owns a fresh groupby result) or return a copy for symmetry with `build_contribution_columns`. | Minor consistency point; no correctness impact since the caller owns the frame. | mix_bottomsup.py lines 202-227 |

No Blocker or Major findings.

---

## Implementation Audit

### Python implementation audit

#### What changed well

- Clean separation: the three builders assemble inputs (row set, classification source, rollup merge) and delegate the identical contribution arithmetic to a single shared helper (`build_contribution_columns`), avoiding triplicated formula logic.
- The rollup aggregate/merge is itself factored (`_aggregate_rollup_pair`, `_merge_rollup_pair`) with module-level source/target column maps, so the per-table differences are reduced to the group keys and join keys.
- Divide-by-zero is centralized in `_safe_div` and masked `numpy.where` with `np.errstate` to suppress the harmless warning while keeping the masked-out quotient at exactly 0.0 — faithful to the Excel `IF(denominator, num/den, 0)` pattern.
- The `fillna(0)` on the four rollup-sourced columns correctly reproduces Excel SUMIFS no-match behavior for new-/lost-distribution rows that the rollup tables exclude.
- `classify_from_lbs` keeps the four-branch zero-test in one place with an explicit routing-table comment, reused by both the category and customer builders.

#### Typing and API notes

- All public functions carry full type hints (`pd.DataFrame` in/out, `list[str]`, `dict[str, str]`); Pyright reports 0 errors on the changed files. No `Any`.
- `pandas` is imported under `TYPE_CHECKING` in `mix_bottomsup.py` since the module only references it for annotations; the helper module imports `numpy`/`pandas` at runtime as required.
- `__all__` exports exactly the three builders (and the two helper functions in the helper module); assembly functions are `_`-prefixed and not exported.
- `zip(..., strict=True)` in `_classify_frame_from_lbs` fails fast on a length mismatch rather than silently truncating.

#### Error handling and logging

- The transforms are total pure functions over well-formed frames; there are no broad exception handlers and no `print`/logging side effects (correct for the pure-transform boundary). All divide-by-zero cases are guarded to 0.0 rather than raised, matching the documented Excel parity.

---

## Test Quality Audit

The tests exercise the real rollup builder chain via `build_chain()` rather than
constructing mock frames, so the BottomsUp builders are validated against
realistically-shaped inputs. The property test (`hypothesis`, 200 examples) verifies
the `SKU Mix = New + Disco + Normal` identity across all classifications with
magnitude-bounded floats (the bound is documented and justified to keep the identity
deterministic under float64). Unit tests cover columns/grain, the normal tie-out,
new/disco branch activation, the zero-subtotal share guard, and the classification
join; the integration test asserts all three tables land in `sqlite_master` after an
end-to-end run on a single in-memory connection.

### Reviewed test and QA artifacts

- `tests/test_mix_bottomsup.py` — 19 unit/property tests; AAA structure; one behavior per test; fabricated data only.
- `tests/mix_bottomsup_fixtures.py` — fabricated `Mix_Base` spanning every contribution branch plus the real-chain runner; keeps the test module under the line limit.
- `tests/test_mix_pipeline.py` — `_DERIVED_TABLES` extended with the three tables; verifies persistence (AC12).
- `artifacts/python/lcov.info` — regenerated by reviewer re-run; `src/mix_bottomsup.py` 57/57 lines + 2/2 branches, `src/_mix_bottomsup_helpers.py` 39/39 lines + 2/2 branches, `src/mix_pipeline_run.py` 24/24 lines.
- `evidence/qa-gates/confidentiality-review.2026-05-27T20-52.md` — confirms only fabricated data appears and the workbook was never read.

### Quality assessment prompts

- **Determinism:** No clock/RNG/network/disk; in-memory frames and a magnitude-bounded hypothesis strategy.
- **Isolation:** Each test targets a single behavior with its own fixture instance.
- **Speed:** 23 targeted tests in 3.92s.
- **Diagnostics:** Tie-out assertions use explicit tolerances; the integration assert names the missing table.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | Diff scan for workbook data tokens found only documented references to the workbook *filename* (schema, not secret) in docs/evidence; no data values. Workbook is gitignored and absent from the diff. |
| No unsafe subprocess or command construction | ✅ PASS | No subprocess use; pure pandas transforms. |
| Input validation at boundaries | ✅ PASS / N/A | Divide-by-zero guarded to 0.0; `zip(strict=True)` enforces column-length parity; transforms assume well-formed upstream frames per the pure-transform contract. |
| Error handling remains explicit | ✅ PASS | No broad catches; guards are explicit masks, not swallowed exceptions. |
| Configuration / path handling is safe | ✅ PASS / N/A | No paths or config introduced; all I/O remains in unchanged `src/pandas_io.py`. |
| Confidentiality (hard constraint) | ✅ PASS | No confidential workbook data in any committed source, test, fixture, doc, or evidence artifact; workbook untracked and gitignored. |

---

## Research Log

No external research was required. All evidence came from the repository diff,
the source and test files, the executor evidence artifacts, the regenerated
coverage artifact, and a reviewer re-run of the Python toolchain.

---

## Verdict

The change is ready for normal PR flow. It is a faithful, well-tested reproduction
of the three Excel BottomsUp tabs as pure pandas transforms, additive to the
existing pipeline, with clean toolchain results, 100% line/branch coverage on the
new and changed modules, and verified confidentiality. The three Info/Nit findings
are documented design decisions or cosmetic notes and do not block. Recommendation:
**Go.**
