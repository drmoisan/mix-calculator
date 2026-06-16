# `schema-builder-ux-overhaul` — User Story

- Issue: #72
- Owner: drmoisan
- Status: Draft
- Last Updated: 2026-06-16T14-25

## Story Statement

- As a ..., I want ..., so that ...
- As a ..., I want ..., so that ...

## Problem / Why

The Schema Builder dialog (`SchemaBuilderDialog` plus its tab/state/presenter
helpers) has several usability gaps and at least two tabs whose purpose is
unclear to the user. The window cannot be resized vertically, the Identity
description is a single non-wrapping line, the Derived tab uses a `|` separator
and unbracketed column references, the Columns tab shows a dtype checkmark rather
than the underlying value and offers no way to inspect a specific source row, and
the Preview tab does not render a result table. The Key and Dedup tabs duplicate
or obscure behavior that the user believes should be expressed through the
Derived and Columns tabs.


## Personas & Scenarios

- Persona: ...
  - who the user is
  - what they care about
  - their constraints
  - their goals and frustrations
  - their context and motivations
- Scenario: ...
  - A concrete, step-by-step narrative that describes how a user accomplishes a goal in a real-world context using the system.
  - who is acting?
  - what triggered the action?
  - what steps do they take?
  - what obstacles or decisions occur?
  - what outcome do they expect?


## Acceptance Criteria

- [x] The schema-builder window can be resized vertically as well as horizontally.
- [x] The Identity description wraps across multiple lines and resizes with the window.
- [x] The Derived tab renders/parses `name = expression` and brackets column refs with the comma outside the brackets.
- [x] Double-clicking a column name in the New-derived dialog inserts the bracketed name into the expression.
- [x] The Columns tab has a row-number chooser that updates every field's displayed value; the value is shown to the right of the blue object instead of a checkmark.
- [x] The Key tab purpose is resolved (removed/repurposed) per the agreed design; key authored via Derived and assigned via Columns where decided.
- [x] The Dedup tab purpose is resolved (groupby on non-value assignments) per the agreed design.
- [x] The Preview tab renders the result table from the configured tabs and reports specific missing inputs.


## Non-Goals

Call out what is explicitly excluded from this feature.
