# etl-loader-output-required-and-drop - User Story (epic #74, CF2)

- **Issue:** #74 (epic child CF2)
- **Parent:** docs/features/active/2026-06-17-configurable-etl-required-column-contract-74/
- **Owner:** drmoisan
- **Last Updated:** 2026-06-17

## Story

As a maintainer of the configurable ETL subsystem, I want the schema-driven loader to honor the
redefined `required` (required-output) semantics without coupling load behavior to the `required`
flag, so that any schema can mark columns `required: false` (including the AOP measure columns)
without changing which columns are emitted or their order.

## Context

CF1 redefined `required` to mean "required OUTPUT column." The loader, however, still infers
"located by name / tolerate-absent" from `not required` and orders the `none`-dedup (AOP) output by
required-vs-optional grouping. Flipping AOP measures to `required: false` therefore reorders AOP
output (verified in CF1 remediation). CF2 adds an explicit located-by-name signal, decouples
which-columns-to-keep and output order from `required`, and minimizes the `default_aop` required
flags that were deferred from CF1.

## Acceptance Criteria

(Authoritative AC list; mirrors `spec.md` Definition of Done.)

- [x] `ColumnSpec` has a typed located-by-name signal (default off), serialized and migration-seeded
      from prior loader behavior.
- [x] The loader's which-columns-to-keep decision and the `none`-dedup emitted column ORDER are
      independent of the `required` flag; a `required` source column still raises when absent.
- [x] `default_aop` measures (`Jan`–`Dec`, `YTD`, `Q1`–`Q4`) are `required: false` with
      `in_output: true`; dimensions remain `required: true`.
- [x] AOP and LE SchemaLoader parity tests pass unchanged (zero output regression).
- [x] A fabricated `none`-dedup schema with `required: false, in_output: true` measures emits columns
      in the expected order (order independent of `required`); negative presence tests pass.
- [x] Toolchain clean (format → lint → type-check → test); coverage >= 85% line / >= 75% branch;
      all changed files <= 500 lines.

## Out of Scope

- Formula-stage coercion (CF3), schema auto-identification (CF4), GUI tabs (CF5), and the
  `normalize_le` migration/removal (CF6/CF7).
- Any change to emitted output for the bundled schemas.
