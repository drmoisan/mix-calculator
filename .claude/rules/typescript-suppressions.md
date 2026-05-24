---
paths:
  - "**/*.ts"
description: Pre-authorized ESLint and TypeScript suppression patterns. Applies to TypeScript files.
---

# TypeScript Suppression Policy

This rule file summarizes the suppression authorization policy for TypeScript code.

## Authorization Requirement

All ESLint and TypeScript suppressions must either:
1. **Match a pre-authorized pattern** defined in this file, OR
2. **Have explicit user approval** for that specific suppression.

**Escalation path before requesting approval:**
1. First, attempt to resolve the error without a suppression (refactor, restructure, adjust types).
2. If that fails, try at least five more distinct approaches.
3. Continue iterating until you solve the problem or clearly demonstrate why each approach fails.
4. Only after multiple documented failed attempts may you request user approval, providing: the specific rule/error code, each approach tried and why it failed, and why a suppression is the only remaining option.

## Pre-Authorized Patterns

### ESLint — Single-rule, single-line disable

**Pattern:** `// eslint-disable-next-line <rule-name> -- <reason>`

**When authorized:**
- Suppresses exactly one ESLint rule for exactly one following line.
- The reason is specific and local to the code (not "annoying rule", "temporary", or "works").
- The suppression does not hide a real bug or broaden the type surface unnecessarily.

**Required comment format:** The `-- <reason>` suffix is mandatory and must explain why the suppression is safe in this specific local context.

### TypeScript — Single-line expect-error

**Pattern:** `// @ts-expect-error -- <reason>`

**When authorized:**
- A single line is flagged by TypeScript and you can explain the mismatch precisely.
- The reason explains what TypeScript is complaining about AND why this line is safe anyway.
- Prefer fixing types, adding runtime guards, or refining control flow over suppressions.

**Self-auditing:** `@ts-expect-error` fails the build if the error disappears, preventing stale suppressions.

**Required comment format:** The `-- <reason>` suffix is mandatory.

## Explicitly Prohibited Patterns

These patterns require explicit user approval and should generally be avoided:

| Pattern | Reason prohibited |
|---------|-------------------|
| `/* eslint-disable */` | File-level; extremely large blast radius; hides unrelated problems. |
| `/* eslint-disable <rule> */` | File-level; use single-line suppression instead. |
| `// @ts-ignore` | Can silently mask real problems; does not fail when the error disappears. |
| `// @ts-nocheck` | Disables type checking for the entire file; defeats repo type-safety standards. |

## Policy Enforcement Checklist

Before using any suppression, verify:
- [ ] Pattern exactly matches a pre-authorized pattern above.
- [ ] Required comment format (`-- <reason>`) is used.
- [ ] Scope is the smallest possible (single rule, single line).
- [ ] The reason is specific and explains why the code is safe.
