---
description: "Pre-authorized patterns for ESLint and TypeScript suppressions in TypeScript code"
applyTo: "**/*.ts"
name: typescript-suppressions-policy
---

# Pre-Authorized Suppression Patterns (TypeScript)

This policy defines the **only** patterns of ESLint and TypeScript suppression directives that are pre-authorized for use in TypeScript code without explicit user approval.

**Authorization requirement:**

- All ESLint and TypeScript suppressions must either:
  1. **Match a pre-authorized pattern** defined in this file, OR
  2. **Have explicit user approval** for that specific suppression

**If you encounter an error that seems to require a suppression not matching a pre-authorized pattern:**

1. First, attempt to resolve it without a suppression (refactor, restructure, adjust types)
2. If that fails, try at least five more distinct approaches
3. Continue iterating until you solve the problem or demonstrate why each approach fails
4. Only after multiple documented failed attempts may you request user approval, providing:
   - The specific rule/error and diagnostic code
   - Each approach you tried and why it failed
   - Why a suppression is the only remaining option

---

## ESLint Suppressions

### eslint-disable-next-line (single rule)

**When pre-authorized:**

You must suppress **exactly one** ESLint rule for **exactly one** following line, and you can provide a concrete, local justification.

**Required pattern:**

- `// eslint-disable-next-line <rule-name> -- <reason>`

**Required context:**

- The suppressed rule must apply to the next line only.
- The reason must be specific and local to the code (not “annoying rule” / “temporary” / “works”).
- The suppression must not hide a real bug or broaden the type surface unnecessarily.

**Justification:**

Single-line, single-rule disables keep blast radius small, preserve lint value elsewhere, and ensure reviewers can see exactly what is being waived and why.

**Examples:**

- Narrowly suppressing an intentional non-null assertion when the invariant is enforced immediately above.
- Suppressing a rule for an unavoidable API shape mismatch while keeping runtime checks.

---

## TypeScript Suppressions

### @ts-expect-error (single line)

**When pre-authorized:**

You have a single line that TypeScript flags, you can explain the mismatch precisely, and you can justify why it is safe in this local context.

**Required pattern:**

- `// @ts-expect-error -- <reason>`

**Required context:**

- Prefer fixing types, adding runtime guards, or refining control flow over suppressions.
- The reason must be specific:
  - what TypeScript is complaining about, and
  - why this line is safe anyway.
- The suppression must be on the line immediately preceding the flagged line.

**Justification:**

`@ts-expect-error` is self-auditing: it fails the build if the error disappears, preventing stale suppressions from lingering indefinitely.

**Examples:**

- Narrowly suppressing a known incorrect upstream type declaration when wrapping the call with runtime validation.
- Narrowly suppressing an intentional type-level limitation when bridging legacy shapes.

---

## Non-authorized Patterns (Explicitly Prohibited - with Workarounds)

The following patterns are **NOT** pre-authorized. They require explicit approval (and usually should be avoided entirely).

### File-level ESLint disables

**Prohibited patterns:**

- `/* eslint-disable */`
- `/* eslint-disable <rule> */`

**Why NOT authorized:**

File-level disables have an extremely large blast radius and tend to hide unrelated problems over time.

**Recommended alternative pattern:**

- Rewrite the code to satisfy the rule, or
- Use a single-line `eslint-disable-next-line` suppression with a specific reason (if the rule truly cannot be satisfied).

### @ts-ignore

**Prohibited pattern:**

- `// @ts-ignore`

**Why NOT authorized:**

`@ts-ignore` can silently mask real problems and does not fail when the error disappears.

**Recommended alternative pattern:**

- Prefer `// @ts-expect-error -- <reason>`.

### @ts-nocheck / @ts-check

**Prohibited patterns:**

- `// @ts-nocheck`

**Why NOT authorized:**

Disabling type checking for a file defeats the repo’s type-safety standards.

**Recommended alternative pattern:**

- Fix the typing issue locally, or isolate the untyped/unsafe boundary behind a small adapter with runtime validation.

---

## Policy Enforcement

### Pre-authorized pattern checklist

Before using a suppression, verify:

- [ ] Pattern **exactly** matches a pre-authorized pattern above
- [ ] Required comment format is used verbatim
- [ ] Scope is the smallest possible (single rule, single line)
- [ ] The reason is specific and explains why the code is safe

### Requesting new pre-authorized patterns

If you encounter a recurring suppression need that should be pre-authorized:

1. Document the pattern with full justification
2. Show why it is deterministic and can be codified
3. Propose the required comment format
4. Request user approval to add it to this file
