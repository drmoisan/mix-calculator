---
name: s9-ci-gate-parser-fallback
description: The S9 CI-gate parser script is not present in this repo; derive ci_gate from gh JSON directly
metadata:
  type: feedback
---

The orchestrate skill's S9 procedure references `scripts/orchestration/Invoke-CiGateParser.ps1` to parse `gh pr checks` JSON into the `ci_gate` object, but that script (and the whole `scripts/orchestration/` dir) does not exist in this repo. Do not treat its absence as a blocker.

**Why:** The parser only transforms gh JSON into `{head_sha, run_id, run_url, conclusion}`; the orchestrator can compute that mapping directly. Failing closed on a missing helper would stall a green PR.

**How to apply:** Run `gh pr checks <pr> --json bucket,name,state,link,workflow` and derive `conclusion`: `success` if all required buckets are `pass`, `failure` if any failed, `pending` if any in progress. `gh pr checks --required` may exit 2 right after PR creation (checks not yet registered) — query without `--required` and match against the known required set. To wait, `gh run watch <run-id> --exit-status` blocks until completion (exit 0 = success). Required checks on `main` (this repo): actionlint, Dependency review, Python toolchain py3.12, py3.13, CodeQL analyze (python) — see [[ci-required-checks-enforceable]]. Set `step9_status: passed` only when `conclusion == success` AND `ci_gate.head_sha == current PR head SHA`.
