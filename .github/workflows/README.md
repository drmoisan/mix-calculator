# CI workflows

This directory holds the repository's GitHub Actions workflows. CI is composed
from small, single-purpose **reusable workflows** that an **orchestrator**
workflow calls. This mirrors the repository convention: every CI gate ships as a
callable reusable workflow named `_<name>.yml` that declares both
`on: workflow_call:` and `on: workflow_dispatch:`, and orchestrator workflows
reference those callees with `uses: ./.github/workflows/_<name>.yml` and contain
no inline `steps:` of their own.

## Files

| File | Kind | Purpose |
|------|------|---------|
| `ci.yml` | Orchestrator | Entry point. Runs on PRs into `main`, pushes to `main`, and `workflow_dispatch`. Composes the gates below. |
| `_python-quality.yml` | Gate | Full Python toolchain: Black (format) -> Ruff (lint) -> Pyright (types) -> Pytest with coverage (`--cov-fail-under=85`). Matrix: Python 3.12 and 3.13. |
| `_actionlint.yml` | Gate | Lints all workflow YAML with a pinned `actionlint` release. |
| `_codeql.yml` | Gate | CodeQL static application security testing (SAST) for Python (`security-extended`). |
| `_dependency-review.yml` | Gate | Scans dependency changes on pull requests for known vulnerabilities and disallowed licenses. |

## Triggers

`ci.yml` runs on:

- `pull_request` targeting `main`
- `push` to `main`
- `workflow_dispatch` (manual, on demand)

`dependency-review` runs only on `pull_request`; the underlying action requires
PR context to diff base against head.

## Coverage policy

`_python-quality.yml` enforces line coverage `>= 85%` via `--cov-fail-under=85`,
consistent with `.claude/rules/quality-tiers.md`. Branch coverage (`>= 75%` per
policy) is reported via `--cov-branch` in the run log.

## Permissions

The orchestrator sets a least-privilege default of `contents: read`. The CodeQL
calling job raises this to `security-events: write` and `actions: read`, because
a reusable workflow cannot request more `GITHUB_TOKEN` scope than its caller
grants.

## Running a single gate on demand

Each `_<name>.yml` declares `workflow_dispatch`, so any gate can be run in
isolation from the **Actions** tab by selecting the workflow and clicking
**Run workflow**. This is useful for re-running, for example, only CodeQL or only
the Python toolchain without triggering the full orchestrator.

Locally, the workflow-lint gate has an equivalent script:

```powershell
pwsh scripts/dev-tools/run-actionlint.ps1
```

## Reusable-workflow nesting

GitHub Actions caps reusable-workflow nesting depth at 4. This repository uses a
single level of nesting (`ci.yml` -> `_<name>.yml`) and does not add further
levels without an explicit design review. Any job that must share files with
another job uses explicit `actions/upload-artifact` + `actions/download-artifact`;
cross-job filesystem state is not implicit.

## Branch-protection rename procedure

Branch protection matches required status checks by their reported **job name**,
not by workflow file name. When renaming a job or workflow:

1. Land the rename on a branch and open a PR so the new check name is reported at
   least once against a commit.
2. In **Settings -> Branches -> Branch protection rules** for `main`, add the new
   check name to the required-checks list (it becomes selectable only after it
   has reported once).
3. Remove the old check name from the required list.
4. Merge. Removing the old name before the new one is required can leave a window
   where no check is enforced, so add-then-remove in that order.

The job names currently surfaced to branch protection are: `Python quality`,
`Workflow lint`, `CodeQL SAST`, and (on PRs) `Dependency review`.
