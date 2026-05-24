---
name: remediation-handoff-atomic-planner
description: 'Reusable remediation trigger and atomic_planner handoff steps. Use when audits require remediation inputs and a delegated remediation plan.'
---

# Remediation Handoff to atomic_planner

Shared remediation workflow and handoff expectations for agents that delegate to `atomic_planner`.

## When to Use This Skill

Use this skill when:
- Audit findings require remediation.
- You must create remediation inputs and delegate plan creation to `atomic_planner`.

## Trigger Conditions (Generic)

Trigger remediation when any of these are true:
- Audit artifacts contain FAIL or meaningful PARTIAL findings.
- Toolchain checks fail.
- Acceptance criteria are not met.

## Required Remediation Inputs

Create `remediation-inputs.<timestamp>.md` with:
- Enumerated fix list with file paths, expected behavior, and verification commands.
- A “do not do” list (no scope creep, no policy weakening, no silent skips).

## Plan Creation and Handoff

1) Create a remediation plan target file using the repo’s plan template.
2) Delegate to `atomic_planner` with:
   - `${spec}` pointing to remediation inputs (authoritative)
   - `${file}` pointing to the remediation plan target file
3) Require `atomic_planner` to output a deterministic, atomic plan with phases and `[P#-T#]` IDs.
4) Require the same `${file}` path to be updated in place across all remediation-plan revisions in the same remediation loop.
5) The caller owns the downstream clearance loop:
   - hand the resulting remediation plan to `atomic_executor` in preflight-validation mode,
   - if preflight returns `PREFLIGHT: REVISIONS REQUIRED`, re-delegate to `atomic_planner` against the same `${file}` path,
   - execute the remediation plan only after `PREFLIGHT: ALL CLEAR`.

## Context Package (When Required)

If the calling agent requires a context package, inline the specified audit artifacts, PR context artifacts, and any relevant plan files in the delegated prompt.
