# Authoritative AOP Output Column Order (binding oracle) — cycle 2

Timestamp: 2026-06-17T13-10

Oracle source: `src/load_aop.py` (`load_aop`), with the keep-list built from
`src/_load_aop_helpers.py` `EXPECTED_COLUMNS` (= `SOURCE_COLUMNS` minus `KEY` and `YTG`).

## Derivation

`src/_load_aop_helpers.py`:
- `SOURCE_COLUMNS = [KEY, Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, YTG, Super Category, PPG]`
- `EXPECTED_COLUMNS = [c for c in SOURCE_COLUMNS if c not in {"KEY", "YTG"}]`
  = `Customer, SKU Descripiton, SKU #, Customer Master, Type, Jan..Dec, YTD, Q1..Q4, Super Category, PPG`

`src/load_aop.py` `load_aop` (lines ~239-247):
- `columns_to_keep = [mapping[expected] for expected in EXPECTED_COLUMNS]`
- then, when present, appends `KEY` (line 241-243), then `YTG` (line 244-246).

## Emitted order (the binding oracle, with-YTG fixture)

Empirically verified (this cycle) against both `load_aop.load_aop(...)` and the current
`SchemaLoader(default_aop).load(...)`; both produce the identical column order:

```
Customer, SKU Descripiton, SKU #, Customer Master, Type,
Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
YTD, Q1, Q2, Q3, Q4, Super Category, PPG, YTG, KEY
```

Note: although `load_aop` appends the located `KEY` column to its keep-list before `YTG` in
source code, `resolve_key` subsequently re-establishes `KEY` and the column ends up LAST in
the emitted frame, so the trailing two columns are `YTG, KEY`. This matches the protected
order recorded in the cycle-1 regression dossier and the frame order asserted by the parity
oracle. The zero-regression gate is `tests/test_schema_loader_parity_aop.py`, which asserts
`list(schema_output.columns) == list(load_aop.load_aop(...).columns)`.

The R1 mechanism orders the resolved (non-by-name) columns by declared `schema.columns`
index (flag-independent) and appends located by-name optionals after them in by-name order;
because the current SchemaLoader output already equals the oracle order, R1 must reproduce
this exact order with the required-flag dependency removed so R2's flag flip cannot move any
column.

Empirical verification commands (this cycle):
- `SchemaLoader(default_aop).load(...)` -> ends `Super Category, PPG, YTG, KEY` (confirmed)
- `load_aop.load_aop(...)` -> ends `Super Category, PPG, YTG, KEY` (confirmed)
