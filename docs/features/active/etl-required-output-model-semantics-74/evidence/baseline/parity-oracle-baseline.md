# Parity Oracle Baseline (AOP + LE) — cycle 2

Timestamp: 2026-06-17T13-10

Command: `poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py -q`

EXIT_CODE: 0

Output Summary:
11 passed in 1.25s. The AOP and LE SchemaLoader parity oracles pass on the clean tree before
any edit. This is the zero-regression reference: both `tests/test_schema_loader_parity_aop.py`
and `tests/test_schema_loader_parity_le.py` must continue to pass UNCHANGED after R1 and R2.

Empirical AOP output column order (with-YTG fixture), confirmed equal between
`SchemaLoader(default_aop).load(...)` and `load_aop.load_aop(...)`:

```
Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG, YTG, KEY
```
