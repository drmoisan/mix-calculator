---
name: python-change-budget-router
description: Budget-first routing and batch-scope contract for Python work. Estimate production-file scope, choose small vs large path, enforce the 3 production + 3 test per-batch cap, and halt the agent for scope expansion approval when the estimate exceeds the budget.
---

# Python Change Budget Router

Canonical guidance for deciding whether Python work stays on the small path (`python-typed-engineer` direct mode) or escalates to the full orchestration workflow, and for enforcing per-batch change budgets during execution.

## When to Use This Skill

Use this skill when:

- Intake starts from a natural-language Python request.
- An agent must decide the execution path before planning or implementation.
- A direct-mode route must reject over-budget requests and switch to orchestrated flow.
- An executor must confirm a batch fits within the 3 production + 3 test file cap before editing.

## Canonical Routing Rules

1. Estimate rough change budget first based on likely **production Python files** touched.
2. Route:
   - `1-3` production files (plus corresponding tests) → **small path** (`python-typed-engineer` direct mode).
   - `>3` production files → **large path** (orchestration workflow with promotion, research, spec, planning, execution, and review).

## Per-Batch Change Budget (Hard Gate)

During Phase C execution:

- A single batch may change at most **3 production files** and **3 test files**.
- The default cap applies unless the user supplies an override of the form `budget: prod=<N>, test=<M>` in the initiating prompt.
- A user override may be honored only if it complies with repo policy and approved scope. If the requested scope exceeds 3 production files overall, stop before execution and seek explicit approval.
- If an override is requested, confirm compliance with repo policy before entering Phase C.

## Scope Expansion Protocol

When in-scope work is required beyond 3 production files, stop and return:

- a one-paragraph justification for the additional files,
- the exact additional file paths,
- the smallest alternative that avoids expanding scope,

and wait for explicit user approval before proceeding.

Allowed minimal-seam exceptions (still within the 3-file cap) are:

- introducing a minimal seam for testability (I/O boundary isolation, dependency injection),
- typing changes required for Pyright cleanliness in the slice,
- updating the smallest set of call sites needed to preserve a stable public API.

## Direct-Mode Rejection Rule

If `python-typed-engineer` is invoked directly and estimated scope is `>3` production files:

- Stop before implementation.
- Return an explicit routing instruction to invoke the orchestrated workflow.

## Orchestrated Small-Path Requirements

When routed through the orchestrator, the small path still requires lifecycle scaffolding before implementation:

- invoke promotion and folder lifecycle steps through `vscode/runCommand` and extension access per `feature-promotion-lifecycle` when available. Use script or CLI fallback only when direct extension command execution is unavailable.
- promote the potential item to a GitHub issue with `--work-mode minor-audit`,
- create the active feature folder with `--work-mode minor-audit`,
- delegate minimal-audit plan creation to `atomic_planner` with `DIRECTIVE: MINIMAL-AUDIT PLAN REQUIRED`,
- require `atomic_executor` preflight until `PREFLIGHT: ALL CLEAR`,
- execute Phase 0 only via `atomic_executor` before branching,
- run the reduced small-audit after implementation and QC.

Direct invocation of `python-typed-engineer` remains implementation-focused and does not replace orchestrator lifecycle steps.

## Documentation Expectations

Record in the agent response or logs:

- estimated production file count,
- chosen path (`small` or `large`),
- rationale summary (1-3 bullets),
- any requested budget override and its approval state.
