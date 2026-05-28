# Remediation Inputs: mix-category-customer-mix-tieout (#20)

**Timestamp:** 2026-05-27T22-34
**Feature Folder:** `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/`
**Base Branch:** `main` (commit `b0e048fe9f6d5004e158cac03c3c3261cbba0eb8`)
**Head Branch:** `fix/mix-category-customer-mix-tieout-20` (commit `98399b6b61efae4eb4fa9784925a8975dcb356ca`)
**Work Mode:** `full-bug`
**Source Audits:**
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/policy-audit.2026-05-27T22-34.md`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/code-review.2026-05-27T22-34.md`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/feature-audit.2026-05-27T22-34.md`

---

## Summary

The functional fix for issue #20 is correct, fully covered (100% line / 100% branch on changed source), and passes the entire Python toolchain in a single clean reviewer pass. All nine acceptance criteria evaluate to PASS. One Blocking general-code-change policy violation prevents a clean PASS verdict and requires remediation before merge.

Blocking findings count: 1
Non-blocking findings count: 0

---

## Remediation-Required Findings

### Finding 1 — Test file exceeds 500-line limit (Blocking)

**Severity:** Blocker
**Policy:** `.claude/rules/general-code-change.md` — File Size Limit: "No production code, test code, or reusable script file may exceed 500 lines. Exceptions: temporary throwaway scripts created and deleted within an agent session; raw text fixtures for language-processing test data; Markdown documentation files."
**File:** `tests/test_mix_rollups.py`
**Location:** whole file (562 lines; was 338 lines at merge-base `b0e048f`)
**Evidence:**
- `wc -l tests/test_mix_rollups.py` → 562
- `git show b0e048fe9f6d5004e158cac03c3c3261cbba0eb8:tests/test_mix_rollups.py | wc -l` → 338
- Source audit: `policy-audit.2026-05-27T22-34.md` Section 2.3 and Section 8.

**Why this is Blocking:**
The 500-line limit explicitly applies to test code and lists only three exceptions (throwaway scripts, raw text fixtures, Markdown). None apply: this is a persistent test module, contains Python code rather than raw text fixture data, and is not Markdown. The general code-change policy is non-overridable in this scope and a Blocking violation under the standard remediation handoff.

**Recommended remediation:**

Option A (preferred): split the issue #20 regression and identity tests into a sibling module.
- Create `tests/test_mix_rollups_tieout.py` containing:
  - `_mix_base_rows`, `_mix_base_fixture`, `_single_scenario_mix_base_fixture`, `_unfiltered_group_lbs_le`, and `_f` helpers (or import a shared `tests/_mix_rollups_fixtures.py` helper module instead — see Option B)
  - `test_category_layer_retains_single_scenario_volume`
  - `test_customer_layer_retains_single_scenario_volume`
  - `test_layer_mix_equals_full_aggregation_minus_rollup`
- Keep the original `tests/test_mix_rollups.py` for the layer-level and stage-level unit tests.
- Confirm both files are under 500 lines.

Option B (if preferred to avoid helper duplication): extract the shared fixture helpers to `tests/_mix_rollups_fixtures.py` (a non-test helper module under `tests/`), then both test files import from it. The helper module is reusable script code and must itself stay under 500 lines.

Either option keeps every test assertion intact. After splitting:

```bash
env -u VIRTUAL_ENV poetry run black --check tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py
env -u VIRTUAL_ENV poetry run ruff check tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py
env -u VIRTUAL_ENV poetry run pyright tests/test_mix_rollups.py tests/test_mix_rollups_tieout.py tests/_mix_rollups_fixtures.py
env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing
```

Acceptance for the remediation:
- Every file in `tests/` and `src/` is under 500 lines.
- All 220 tests still pass.
- Line coverage remains 100% on `src/mix_rollups.py`, `src/_mix_rollups_helpers.py`, and `src/mix_pipeline_run.py`; branch coverage remains 100%.
- Black/Ruff/Pyright remain clean.
- No source-code (`src/**`) behavior change accompanies the test split.

---

## Non-Blocking Findings

None.

The code review contains three `Info`-severity entries (an optional comment improvement in `src/mix_rollups.py::build_mix_4_country`, and two informational confirmations on `src/_mix_rollups_helpers.py` and `tests/mix_bottomsup_fixtures.py`). None of these are remediation-required; they are recorded only for reviewer transparency.

---

## Acceptance Criteria Status

All nine acceptance criteria in `spec.md` evaluate to PASS (see `feature-audit.2026-05-27T22-34.md`). No AC remediation is required. The single Blocking finding is a general-code-change policy violation outside the AC set.

---

## Handoff Notes for the Remediation Planner

- The fix is a pure test-file split with no production-code change. The atomic-planner should size this as a single small task (estimated under 30 lines of net diff: re-locate ~120 lines of helpers and three tests into the new module, import them back in the original file if needed, no new dependencies).
- The cross-feature `tests/mix_bottomsup_fixtures.py` is unaffected by the split and should not be touched.
- The remediation must not modify any `src/**` file, `spec.md`, `issue.md`, or any policy document under `.claude/rules/`.
- Evidence for the remediation should be stored under `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/remediation-baseline/` and `evidence/qa-gates/` per the canonical evidence-location scheme.
- After remediation, this feature audit should be rerun and the overall readiness verdict upgraded from `NEEDS REVISION` to `PASS`.
