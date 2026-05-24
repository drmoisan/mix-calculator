---
paths:
  - "**/*.ts"
description: TypeScript-specific toolchain and coding standards.
---

# TypeScript Code Standards

This rule file summarizes the TypeScript-specific policies for this repository.

## Toolchain

1. **Formatting — Prettier**: All TypeScript must be formatted with the repository Prettier configuration. Command: `npm run format`
2. **Linting — ESLint**: TypeScript must pass ESLint using the repository configuration. Command: `npm run lint`
3. **Type Checking — TSC**: TypeScript must pass the compiler type-check. Avoid `any`; prefer `unknown` plus narrowing. Command: `npm run typecheck`
4. **Testing — Vitest**: All TypeScript unit tests must use Vitest. Command: `npm run test`

Run the toolchain in order: format → lint → type-check → test. Restart from step 1 if any step fails or changes files.

## Coding Standards

- New user-invocable workflows belong under `.claude/skills/` rather than `.claude/commands/`.
- **Strong typing**: Public functions, methods, and exported APIs must have clear, intentional types. Avoid type assertions (`as X`) unless justified.
- **ES modules**: Use ES module syntax. Do not introduce CommonJS patterns (`require`, `module.exports`).
- **Domain types**: Model domain concepts with interfaces/types that encode invariants. Prefer discriminated unions for state machines.
- **Naming**: `PascalCase` for classes, interfaces, enums, and type aliases. `camelCase` for functions, methods, variables, and object properties. No `I` prefix on interfaces.
- **File naming**: Prefer kebab-case filenames (e.g., `user-session.ts`, `task-runner.ts`).
- **Separation of concerns**: Keep pure logic separate from Office.js, Microsoft Graph SDK, and other host-bound APIs, filesystem/network I/O, and UI wiring.
- **Error handling**: Fail fast with clear errors. Avoid catch-all `catch (e)` without rethrowing or adding context.
- **Dependencies**: Do not add new runtime dependencies unless explicitly approved.

## ESLint Stack

- Require `typescript-eslint` strict-type-checked + stylistic-type-checked rule sets.
- Enable type-aware parsing (`parserOptions.project = true`).
- Required plugins: `eslint-plugin-office-addins`, `eslint-plugin-promise`, `eslint-plugin-security`, `eslint-plugin-import`.
- Error-level rules: `no-floating-promises`, `no-misused-promises`, all `no-unsafe-*`.
- Add a `no-restricted-syntax` rule banning `Date.now`, `setTimeout`, `setInterval`, and `Math.random` outside an explicit infrastructure allowlist.

## Testing Standards

- Use **Vitest** as the test framework.
- Name test files `*.test.ts`.
- Unit tests must not require the Outlook host runtime.
- Follow Arrange–Act–Assert structure.
- Each test targets one behavior.
- Use `vi.spyOn` or `vi.mock` for targeted mocking; reset mocks with `afterEach(() => { vi.resetAllMocks(); })`.
- No external dependencies (network, filesystem temp files, external processes) in unit tests.
- Avoid snapshot tests unless stable and intentional.
- Coverage thresholds follow the uniform tier rule defined in `.claude/rules/quality-tiers.md`: line coverage >= 85% and branch coverage >= 75% across all tiers (T1–T4).
- Coverage command: `npm run test:coverage` (the script is wired in Prompt B1 alongside the Vitest dependency).
- Coverage regression on changed lines is a blocking finding.

## Architecture Boundaries

Layer rules and the No-COM architecture assertions are defined in `.claude/rules/architecture-boundaries.md`. The TypeScript enforcement tool is `dependency-cruiser` with configuration file `.dependency-cruiser.cjs`.

## Property-Based and Mutation Testing

- `fast-check` provides property-based tests; T1 and T2 modules require >= 1 property test per pure function.
- `StrykerJS` provides mutation testing; T1 modules require mutation score >= 75%.
- Both run in pre-merge or nightly pipelines per `general-code-change.md`.

## Golden Tests

- T1 classifier modules require golden-output snapshots tested against a versioned corpus.
- The general guidance to avoid snapshot tests unless stable and intentional remains in force for all other scenarios; classifier-output and schema-evolution snapshots are explicitly permitted when versioned.

## Runtime Determinism

- `Date`, `Math.random`, and `setTimeout` access must flow through an injected `Clock` / `Random` interface.
- Tests use Vitest fake timers (`vi.useFakeTimers()`).
- Prefer `await flushPromises()` over `setTimeout(0)` for awaiting micro-tasks.
