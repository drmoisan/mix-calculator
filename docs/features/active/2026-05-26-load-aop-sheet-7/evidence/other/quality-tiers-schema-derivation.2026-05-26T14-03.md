# quality-tiers.yml Schema Derivation

Timestamp: 2026-05-26T14-03

## Sources consulted

- `.claude/rules/quality-tiers.md` (present; authoritative for this repo).
- `docs/ci.research.md` — ABSENT (confirmed via directory listing). The rule
  names it as the tier-system source of truth "section 1", but the file does not
  exist in this repository at execution time, matching the plan's open-questions
  note. The schema is therefore derived from `.claude/rules/quality-tiers.md`.

## Source lines that justify the schema

From `.claude/rules/quality-tiers.md`:

- "The tier system source of truth is `docs/ci.research.md` section 1; the file
  `quality-tiers.yml` at the repository root maps every project to a tier."
- "## Source of Truth — `quality-tiers.yml` at repo root maps every project to
  one tier."
- "The CI pipeline's `tier-classification` stage validates that every project
  entry has a tier and that no unclassified project exists. Adding a project
  without a tier classification fails CI."
- Tier identifiers defined by the rule: `T1` (Critical), `T2` (Core),
  `T3` (Adapters & UI), `T4` (Scaffolding).

## Derived schema

The rule specifies a single, unambiguous obligation: a repo-root file
`quality-tiers.yml` that maps every project to exactly one tier, where the tier
value is one of `T1`, `T2`, `T3`, `T4`. The rule does not prescribe additional
keys, so the minimal conformant shape is a top-level `projects:` mapping from a
project identifier (the `src` module path) to its tier string:

```yaml
# Each project (src module) maps to exactly one tier: T1, T2, T3, or T4.
projects:
  <project-identifier>: <tier>   # tier in {T1, T2, T3, T4}
```

- Key: project identifier. Concretely, the `src/*.py` module path, which is the
  unit of code the gate matrix in the rule applies to.
- Value: the tier string, constrained to the four tier identifiers the rule
  defines.

This shape satisfies the only hard requirement the rule states ("maps every
project to one tier" / "every project entry has a tier"). The schema is fully
derivable from the rule; no fail-fast blocker is required.
