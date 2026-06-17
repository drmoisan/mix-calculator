# AOP Output-Identity Dimension Set — confirmed from src/_load_aop_helpers.py

Timestamp: 2026-06-17T12-35

Source of truth: `src/_load_aop_helpers.py` (`SOURCE_COLUMNS`, `EXPECTED_COLUMNS`, `LABEL_COLUMNS`).

Declared column order (SOURCE_COLUMNS = TARGET_COLUMNS):
`KEY, Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, YTG, Super Category, PPG`

Required-output dimensions (in declared order, after R1):
1. Customer
2. SKU Descripiton
3. SKU #
4. Customer Master
5. Type
6. Super Category
7. PPG

Optional (required: false, in_output: true):
- `KEY` and `YTG` — both excluded from `EXPECTED_COLUMNS` (resolved by name only; older sheets predate them).

Measures (required: false after R1, in_output: true): `Jan`–`Dec`, `YTD`, `Q1`–`Q4`.

Label columns (sentinel-cleaned, remain required dimensions): `Super Category`, `PPG` (per `LABEL_COLUMNS`).
