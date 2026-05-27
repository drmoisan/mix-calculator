---
name: mcp-gate-is-runnable
description: Do not declare the canonical PoshQC/MCP QA gate or promotion lifecycle unrunnable based on the tools not appearing in your session; attempt them, and escalate to the orchestrator if needed
metadata:
  type: feedback
---

Do not report the canonical PowerShell QA gate (`run_poshqc_format` / `run_poshqc_analyze` / `run_poshqc_test`) or the promotion lifecycle as "unrunnable", "unverified-by-default", or "blocked" on the grounds that the `mcp__drm-copilot__*` tools are absent from your session. First attempt the tools; do not assume absence.

**Why:** The tools are real and working in this repo. `.mcp.json` declares the `drm-copilot` server, `.claude/agents/powershell-typed-engineer.md` grants `mcp__drm-copilot__.*`, and on 2026-05-27 the orchestrator executed `run_poshqc_format/analyze/test` (all ok) plus the full promotion lifecycle (`new_potential_bug_entry`, `potential_to_issue`, `new_active_feature_folder`) in the same session a worker had claimed they were unavailable. A prior project memory generalized one session's observation into a permanent false fact ("MCP tools not exposed; gate cannot run canonically") and became self-reinforcing: each spawned worker read it, declined to attempt the tools, blocked, and re-affirmed it. That memory was removed.

**How to apply:**
- The PoshQC scripts and `pester.runsettings` being absent from the checkout is expected — the MCP server provides them as bundled resources. Their absence is NOT evidence the gate cannot run; do not cite it as a blocker.
- If the `mcp__drm-copilot__*` tools genuinely do not surface in your spawned session after you attempt them, treat that as a transient session condition: escalate to the orchestrator to run the canonical gate and the MCP promotion lifecycle. The orchestrator owns and can execute both.
- Never mark a QA result UNVERIFIED or declare the lifecycle blocked solely because the tools did not appear in your tool list. Local PSScriptAnalyzer/Pester remain a labeled fallback for self-checks only, not a reason to give up on the canonical gate.
