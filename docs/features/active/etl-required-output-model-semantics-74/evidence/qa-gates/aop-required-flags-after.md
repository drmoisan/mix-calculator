# AOP required-flag set — AFTER R1 (REVERTED — see regression dossier)

Timestamp: 2026-06-17T12-35

STATUS: The edits this artifact describes were applied, then REVERTED because they
caused an AOP output column-ORDER regression in the SchemaLoader `none`-dedup path
(see `../regression-testing/r1-output-order-regression.2026-06-17T12-35.md`). The
schema file on disk is back at the pre-change baseline. The list below records what
the post-edit `required` set WOULD be once a loader-helper ordering fix is authorized.


Command: python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"

EXIT_CODE: 0

Output Summary:
['Customer', 'SKU Descripiton', 'SKU #', 'Customer Master', 'Type', 'Super Category', 'PPG']

Post-change required list contains only the seven output-identity dimensions in declared order; all seventeen measures (Jan..Dec, YTD, Q1..Q4) are now required: false (in_output: true unchanged). KEY/YTG remain required: false.

git diff confirmation: only seventeen lines changed, each `"required": true,` -> `"required": false,` on the measure columns; no other field altered (P1-T5 invariant).
