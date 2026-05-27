---
name: evidence-validator-script-absent
description: scripts/validate_evidence_locations.py does not exist in this repo; use a git-diff scan for evidence-location compliance instead
metadata:
  type: project
---

The feature-review agent brief instructs running `validate_evidence_locations.py --root .` to scan for non-canonical evidence-location violations, but `scripts/validate_evidence_locations.py` does not exist in this repository.

**Why:** Only the PowerShell PreToolUse hook `enforce-evidence-locations.ps1` exists as the enforcement mechanism; the Python validator script the brief references was never added here. Re-confirmed absent during the issue #11 review (2026-05-27).

**How to apply:** For the Evidence Location Compliance section, perform a git-diff scan instead:
`git diff --name-only <merge-base>..<head> -- 'artifacts/baselines/**' 'artifacts/qa/**' 'artifacts/evidence/**' 'artifacts/coverage/**'`
Zero results means no non-canonical evidence-location violations. Document the script's absence and that the git-diff scan was used in its place. Related: [[issue2-file-size-watch]].
