---
name: invoke-python-engineer
description: Invoke the python-typed-engineer worker to design, implement, and verify Python changes within typed repository boundaries. Applies Black -> Ruff -> Pyright -> Pytest toolchain, the 3-production + 3-test per-batch budget, and zero-regression quality gates.
---

# Implement Python Skill

This direct-use wrapper delegates Python implementation work to the `python-typed-engineer` worker. Use this entry point when a prompt needs a scoped Python change that must stay inside the typed engineer's guardrails.

## When to Use This Skill

Use this skill when:

- The user requests a Python code change, bug fix, refactor, or test addition.
- Estimated scope fits the small path (1-3 production files plus corresponding tests).
- The toolchain (Black, Ruff, Pyright, Pytest) can be run in the current environment, or the user has explicitly authorized an unverified plan-only response.

If the estimated scope exceeds the small-path budget, this skill defers to the orchestrated flow via `python-change-budget-router` instead of proceeding directly.

## Inputs

- Objective statement (what the change must accomplish).
- Files or entrypoints in scope.
- Constraints, including public APIs that must be preserved.
- Optional approved plan. If none is supplied, the worker delegates plan authoring to `atomic_planner` before any edits.
- Optional budget override in the form `budget: prod=<N>, test=<M>` subject to repo policy compliance.

## Output Paths

- Python source and test files within the approved scope.
- Baseline evidence under `<FEATURE>/evidence/baseline/<timestamp>/` and post-change evidence under `<FEATURE>/evidence/qa-gates/<timestamp>/` per `evidence-and-timestamp-conventions`.
- This location is canonical per evidence-and-timestamp-conventions and is not overridable. See `.claude/skills/evidence-and-timestamp-conventions/SKILL.md` for the canonical evidence path authority.
- Plan artifacts under the active feature folder when the task is feature-scoped.

## Required Reporting Block

The worker must return the `python-qa-gate` reporting block:

1. Scope (exact file list).
2. Baseline (Ruff, Pyright, Pytest, coverage status).
3. Plan (design and test strategy).
4. Diffs (patch-style or full-file replacements).
5. QA Gate Results (Ruff, Pyright, Pytest, and coverage deltas, or clearly marked **unverified**).

## Worker Routing

- Worker: `python-typed-engineer`

## Preloaded Contracts

The worker operates under the following preloaded skills and rules:

- `policy-compliance-order`
- `python-change-budget-router`
- `atomic-plan-contract`
- `python-qa-gate`
- `acceptance-criteria-tracking`
- `feature-promotion-lifecycle`
- `remediation-handoff-atomic-planner`
- `evidence-and-timestamp-conventions`
- `.claude/rules/python.md` (path-scoped for `**/*.py`)
- `.claude/rules/general-code-change.md`
- `.claude/rules/general-unit-test.md`
- `.claude/rules/tonality.md`
