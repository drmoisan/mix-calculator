# AOP `required` Flags — Before (cycle 2)

Timestamp: 2026-06-17T13-10

Command: `poetry run python -c "import json; d=json.load(open('src/schemas/default_aop.schema.json')); print([c['canonical_name'] for c in d['columns'] if c.get('required')])"`

EXIT_CODE: 0

Output Summary:
Pre-change required list still includes all twelve months, `YTD`, and `Q1`–`Q4`:

```
['Customer', 'SKU Descripiton', 'SKU #', 'Customer Master', 'Type', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'YTD', 'Q1', 'Q2', 'Q3', 'Q4', 'Super Category', 'PPG']
```

Confirms the pre-change state: 24 required columns (the 7 identity dimensions plus the 17
measures `Jan`–`Dec`, `YTD`, `Q1`–`Q4`). R2 (Phase 2) will flip the 17 measures to
`required: false` while leaving `in_output: true`.
