# Mix Decomp Transforms — Research Findings (Issue #9)

**Date:** 2026-05-26  
**Feature:** LE v AOP Gross-to-Net Decomp — Python/pandas implementation over existing SQLite tables  
**Canonical issue:** 9

---

## 1. Source Schema Mapping

### 1.1 `LE` SQLite table (produced by `src/normalize_le.py`)

`TARGET_COLUMNS` (exact order, 26 columns):

```
KEY, Customer, SKU Descripiton, SKU #, Type, GtN Mapping,
Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
FY, Q1, Q2, Q3, Q4, YTG,
Super Category, PPG
```

Key points for the Power Query mapping:

- One row per unique KEY (`Customer + coerce_sku(SKU #) + Type`).
- `GtN Mapping` is the gross-to-net classification label. This is what the Power Query `LE` query pivots. Distinct values observed in practice include: `Gross Sales`, `Lbs`, `Off Invoice`, `Non-Trade`, `Trade`. The `Cases` GtN label may also be present.
- `YTG` = `sum(May..Dec)` per the 8+4 convention, already derived by the loader.
- `Super Category` and `PPG` are both populated from the source `PPG` column (as-built quirk in normalize_le). Neither contains confidential values per the schema definition, but in practice the cell values may be customer-visible names — treat them as confidential in fixtures.
- Monthly columns `Jan..Dec`, `FY`, `Q1..Q4` are retained in the persisted table even though the Power Query `LE` transform uses only `YTG`. This matters for `Q1 Results By Sku` (see §4.15).

**Columns dropped in the Power Query `LE` transform** (not needed for GtN decomp):
`Jan..Dec`, `FY`, `Q1..Q4`, `KEY`. The Python pivot reads only `Customer`, `Super Category`, `PPG`, `SKU Descripiton`, `SKU #`, `GtN Mapping`, `YTG`.

### 1.2 `aop` SQLite table (produced by `src/load_aop.py`)

`TARGET_COLUMNS` (full schema when YTG present):

```
KEY, Customer, SKU Descripiton, SKU #, Customer Master, Type,
Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec,
YTD, Q1, Q2, Q3, Q4, YTG,
Super Category, PPG
```

Key points for the Power Query mapping:

- One row per `(Customer, SKU #, Type)` source row. Unlike LE, rows are not collapsed by KEY; duplicate KEYs are tolerated and warned.
- `Type` is the gross-to-net line-item label. Distinct values include: `Gross Sales`, `LBs` (renamed to `Lbs`), `Cases`, `Off Invoice $`, `Trade Spend $`, `Non-Trade $`, `Trade Spend %`, `Non-Trade %`, `Off Invoice %`. The percent types are dropped early in the Power Query `AOP` transform.
- `YTG` is the measure the Power Query `AOP` pivot consumes. The Power Query transform removes `KEY`, `Jan..Dec`, `YTD`, `Q1..Q4` — it uses only `Customer Master`, `Customer`, `Super Category`, `PPG`, `SKU Descripiton`, `SKU #`, `Type`, `YTG`.
- `Customer Master` is present in `aop` but absent from `LE`.

**Columns dropped in the Power Query `AOP` transform:**
`KEY`, `Jan..Dec`, `YTD`, `Q1..Q4`.

### 1.3 Pivot mechanics: long → wide

Both tables are currently stored in **long form** — one row per `(…, label, measure)` pair — and must be pivoted **wide** before use as the Power Query `LE`/`AOP` tables.

| Table | Long key column | Long value column | Pivot produces |
|-------|-----------------|-------------------|----------------|
| `LE` | `GtN Mapping` | `YTG` | `Gross Sales`, `Lbs`, `Off Invoice`, `Non-Trade`, `Trade` as columns |
| `aop` | `Type` | `YTG` | `Gross Sales`, `Lbs`, `Cases`, `Off Invoice $`, `Trade Spend $`, `Non-Trade $` as columns (after dropping the `%` types and renaming `LBs`→`Lbs`) |

**Groupby aggregation before pivot:** The Power Query `LE` transform groups by `{KEY, Customer, Super Category, PPG, SKU Descripiton, SKU #, GtN Mapping}` summing `YTG`, then removes `KEY` and pivots. In pandas this is:

```python
# For LE:
grouped = le_raw[key_cols + ["GtN Mapping", "YTG"]].groupby(
    key_cols + ["GtN Mapping"], as_index=False
)["YTG"].sum()
wide = grouped.pivot_table(
    index=key_cols, columns="GtN Mapping", values="YTG", aggfunc="sum"
).reset_index()
wide = wide.fillna(0)
```

where `key_cols = ["Customer", "Super Category", "PPG", "SKU Descripiton", "SKU #"]`.

For `aop`: the Power Query reorders then pivots directly on `Type`/`YTG` using `List.Sum` — effectively a pivot_table with `aggfunc="sum"` on `{Customer Master, Customer, Super Category, PPG, SKU Descripiton, SKU #}`.

**Confidentiality note:** Column names (`Gross Sales`, `Lbs`, etc.) are schema labels, not secrets. Actual cell values (customer names, SKU descriptions, categories, SKU numbers) are secrets and must not appear in fixtures or tests.

---

## 2. Query Dependency DAG

### 2.1 Leaf / source nodes

- `LE` — depends on raw SQLite `LE` table
- `AOP` — depends on raw SQLite `aop` table
- `SkuLu` — depends on a separate `SkuLu` Excel sheet (see §6 risks)

### 2.2 First-tier derived

- `CustomerLU` — depends on `AOP`
- `AOP_NORM` — depends on `AOP`
- `LE_NORM` — depends on `LE`

### 2.3 Second-tier derived

- `AopVsLe` — depends on `AOP_NORM`, `LE_NORM`

### 2.4 Third-tier derived

- `Mix_Base` — depends on `AopVsLe`, `SkuLu`
- `Rate_Impacts` — depends on `AopVsLe` (buffered), `SkuLu`

### 2.5 Mix rollup chain (sequential, no cycles)

The chain is linear and acyclic:

```
Rate_Impacts
  → Mix-Rollup-1   (group Rate_Impacts by {Customer, Country, Category})
    → Mix-1-SKu    (joins Mix-Rollup-1)
      → Mix-Rollup-2 (group Mix-1-SKu by {Customer, Country})
        → Mix-2-Category (joins Mix-Rollup-2)
          → Mix-Rollup-3 (group Mix-2-Category by {Country})
            → Mix-3-Customer (joins Mix-Rollup-3)
              → Mix-Rollup-4 (scalar: List.Sum of Mix-3-Customer)
                → Mix-4-Country (uses scalar Mix-Rollup-4)
```

`Mix-0-Detail` depends on `Mix_Base` only — it is not part of the sequential chain.

**Confirmation this is a DAG:** Each node depends only on nodes listed before it in topological order. There are no back-edges or mutual dependencies. The appearance of a cycle is false: `Mix-Rollup-N` depends on `Mix-(N-1)-…`, not on `Mix-N-…`.

### 2.6 Evaluation order (topological)

```
1.  LE               (pivot raw LE table)
2.  AOP              (pivot raw aop table)
3.  CustomerLU       (from AOP)
4.  SkuLu            (from SkuLu Excel sheet / loader)
5.  AOP_NORM         (from AOP)
6.  LE_NORM          (from LE)
7.  AopVsLe          (from AOP_NORM + LE_NORM)
8.  Mix_Base         (from AopVsLe + SkuLu)
9.  Rate_Impacts     (from AopVsLe + SkuLu)
10. Mix-Rollup-1     (from Rate_Impacts)
11. Mix-1-SKu        (from Mix_Base + Mix-Rollup-1)
12. Mix-Rollup-2     (from Mix-1-SKu)
13. Mix-2-Category   (from Mix-1-SKu + Mix-Rollup-2)
14. Mix-Rollup-3     (from Mix-2-Category)
15. Mix-3-Customer   (from Mix-2-Category + Mix-Rollup-3)
16. Mix-Rollup-4     (scalar, from Mix-3-Customer)
17. Mix-4-Country    (from Mix-3-Customer + Mix-Rollup-4 scalar)
18. Mix-0-Detail     (from Mix_Base)
19. Q1 Results By Sku (from raw LE table, separate path)
```

`CustomerLU` is a supporting lookup; it does not feed any node in the DAG above, but it is persisted for downstream reporting.

---

## 3. Helper Transform Semantics

### 3.1 `NegateColumn(table, column_name)`

Multiplies every value in `column_name` by `-1`. In pandas:

```python
df[col] = df[col] * -1
```

Applied after pivot in both `LE` and `AOP` transforms to `Off Invoice $`, `Trade Spend $`, `Non-Trade $`. Applied because the source data records these deductions as positive; downstream calcs add them to Gross Sales.

### 3.2 `CalcRatios(input_table)`

Appends eight derived ratio columns using the named measure columns already present. Each ratio guards against a zero or negative denominator by returning `0`. Pandas equivalent (applied row-wise):

| Output column | Formula | Guard |
|---|---|---|
| `Gross Sales Per Lb` | `Gross Sales / Lbs` | `if Lbs > 0 else 0` |
| `OI Per Lb` | `Off Invoice $ / Lbs` | `if Lbs > 0 else 0` |
| `Trade Per Lb` | `Trade Spend $ / Lbs` | `if Lbs > 0 else 0` |
| `Non-Trade Per Lb` | `Non-Trade $ / Lbs` | `if Lbs > 0 else 0` |
| `Net Rev Per Lb` | `Net-Revenue $ / Lbs` | `if Lbs > 0 else 0` |
| `OI %GS` | `Off Invoice $ / Gross Sales` | `if Gross Sales > 0 else 0` |
| `Trade %GS` | `Trade Spend $ / Gross Sales` | `if Gross Sales > 0 else 0` |
| `Non-Trade %GS` | `Non-Trade $ / Gross Sales` | `if Gross Sales > 0 else 0` |

In pandas use `numpy.where` or a masked series to avoid division warnings:

```python
def _safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return pd.Series(
        numpy.where(den > 0, num / den, 0.0), index=num.index
    )
```

`CalcRatios` is called on both the long-→-wide pivoted LE and AOP frames (after `Net-Revenue $` is added), and again inside `AddRatios` per-scenario.

### 3.3 `ClassifyTable(input_table)`

Two-level classification; input is `AopVsLe` (Customer, SKU #, Attribute, AOP, LE, Diff columns).

**Level 1 — SKU classification** (group by `SKU #`, look at `Lbs` rows only):

```
AOPTotal = sum of AOP where Attribute == "Lbs"  (across all customers)
LETotal  = sum of LE  where Attribute == "Lbs"  (across all customers)
```

| Condition | SKU Classification |
|---|---|
| `AOPTotal == 0` and `LETotal == 0` | `inactive` |
| `AOPTotal != 0` and `LETotal == 0` | `eliminated` |
| `AOPTotal == 0` and `LETotal != 0` | `new` |
| otherwise | `exists` |

**Level 2 — Customer+SKU classification** (group by `Customer + SKU #`):

If `SKUClassification != "exists"`: use `SKUClassification` directly as `Classification`.

Otherwise (SKU-level is `"exists"`), look at the single `Lbs` row for this `Customer + SKU #` combination:

```
AOPVal = AOP where Attribute == "Lbs"
LEVal  = LE  where Attribute == "Lbs"
```

| Condition | Classification |
|---|---|
| `AOPVal == 0` and `LEVal == 0` | `inactive` |
| `AOPVal != 0` and `LEVal != 0` | `normal` |
| `AOPVal != 0` and `LEVal == 0` | `lost distribution` |
| `AOPVal == 0` and `LEVal != 0` | `new distribution` |

Implementation note: Use exact equality for the zero test on the aggregated Lbs value, consistent with the M code. Float tolerance should not be applied here because the M code uses `<> 0` / `= 0` without tolerance.

### 3.4 `StackPivot(input_table, columns_to_stack, value_column)`

1. For each row, build a header string by joining the values of `columns_to_stack` with `" - "` (e.g., `["Attribute", "Scenario"]` values `"Lbs"` and `"AOP"` → `"Lbs - AOP"`).
2. Remove the individual `columns_to_stack` columns from the frame.
3. Pivot the resulting header column against `value_column` using `List.Sum` (sum aggregation).

In pandas:

```python
df["_header"] = df[columns_to_stack].apply(
    lambda row: " - ".join(str(v) for v in row), axis=1
)
id_cols = [c for c in df.columns if c not in columns_to_stack + [value_column, "_header"]]
result = df.pivot_table(
    index=id_cols, columns="_header", values=value_column, aggfunc="sum"
).reset_index()
result.columns.name = None
result = result.fillna(0)
```

Result columns are named `"<Attribute> - <Scenario>"` (e.g., `"Lbs - AOP"`, `"Net Rev Per Lb - LE"`, `"Gross Sales Per Lb - Diff"`).

### 3.5 `AddRatios(input_table, scenarios_to_process)`

The function appends new ratio-attribute rows to a long-format table. Steps:

1. Identify the set of attribute names already present in the input (`original_attributes`).
2. For each scenario in `scenarios_to_process` (e.g., `["AOP", "LE"]`):
   a. Filter rows where `[Scenario] == scenario`.
   b. Pivot `Attribute` → `Value` (wide form with one column per attribute).
   c. Call `CalcRatios` to add the eight ratio columns.
   d. Unpivot (melt) back to long form keeping all non-Attribute/Value columns as id_vars.
   e. Retain only rows whose `Attribute` value is NOT in `original_attributes` (i.e., only the eight newly added ratio rows).
3. Concatenate all per-scenario ratio rows together.
4. `pd.concat([input_table, ratio_rows])` to append.

The key invariant is that `AddRatios` does NOT duplicate original rows — it only appends the computed ratio rows.

### 3.6 `FillZeroWithAvg(input_table, lbs_col, net_rev_col, net_rev_per_lb_col)`

Computes a cross-row average `Net Rev Per Lb` and replaces zero values in `net_rev_per_lb_col` with that average:

```
avg = sum(net_rev_col) / sum(lbs_col)  if sum(lbs_col) > 0 else 0
result[net_rev_per_lb_col] = result[net_rev_per_lb_col].replace(0, avg)
```

Applied in `Mix-3-Customer` and `Mix-4-Country` to prevent zero rates from distorting the price/mix decomposition for new or lost-distribution lines.

### 3.7 `GroupAndLookUp` (inferred from rollup pattern)

Not an explicit M function but the recurring pattern in all Mix-Rollup-N queries: `groupby(key_cols).agg({"Calc Net Price Impact": "sum"})`, used as a lookup table joined back to the corresponding Mix-N-X table.

---

## 4. Per-Query Pandas Recipe

### 4.1 `LE` (Wide pivot from raw `LE` SQLite table)

```
1. Read raw LE table (all TARGET_COLUMNS present).
2. Select: Customer, Super Category, PPG, SKU Descripiton, SKU #, GtN Mapping, YTG.
3. Groupby {Customer, Super Category, PPG, SKU Descripiton, SKU #, GtN Mapping}, sum YTG.
4. pivot_table: index={Customer,Super Category,PPG,SKU Descripiton,SKU #},
               columns=GtN Mapping, values=YTG, aggfunc=sum.
5. fillna(0) on {Gross Sales, Lbs, Off Invoice, Non-Trade, Trade}.
6. Rename: Off Invoice→"Off Invoice $", Non-Trade→"Non-Trade $", Trade→"Trade Spend $".
7. Negate: Off Invoice $, Trade Spend $, Non-Trade $.
8. Add: Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $.
9. CalcRatios (add 8 ratio columns).
10. Melt (unpivot) keeping {Customer, Super Category, PPG, SKU Descripiton, SKU #} as id_vars.
    Attribute column = former column name; Value column = value.
```

Output: long-format with columns `{Customer, Super Category, PPG, SKU Descripiton, SKU #, Attribute, Value}`.

### 4.2 `AOP` (Wide pivot from raw `aop` SQLite table)

```
1. Read raw aop table.
2. Select: Customer Master, Customer, Super Category, PPG, SKU Descripiton, SKU #, Type, YTG.
3. pivot_table: index={Customer Master,Customer,Super Category,PPG,SKU Descripiton,SKU #},
               columns=Type, values=YTG, aggfunc=sum.
4. Drop columns: Trade Spend %, Non-Trade %, Off Invoice %.
5. Rename: LBs → Lbs (if present as "LBs").
6. Reorder: Customer Master,Customer,Super Category,PPG,SKU Descripiton,SKU #,Cases,Gross Sales,Lbs,Off Invoice $,Trade Spend $,Non-Trade $.
7. Negate: Off Invoice $, Trade Spend $, Non-Trade $.
8. Add: Net-Revenue $ = Gross Sales + Off Invoice $ + Trade Spend $ + Non-Trade $.
9. CalcRatios.
10. Melt keeping {Customer Master,Customer,Super Category,PPG,SKU Descripiton,SKU #} as id_vars.
```

Output: long-format with columns `{Customer Master, Customer, Super Category, PPG, SKU Descripiton, SKU #, Attribute, Value}`.

### 4.3 `CustomerLU`

```
1. From AOP (wide, before melt, or from raw aop — either works).
   Use raw aop: select Customer Master, Customer.
2. groupby({Customer Master, Customer}), keep distinct pairs (drop count column).
3. Reorder: Customer, Customer Master.
```

Output: two-column lookup `{Customer, Customer Master}`. Useful for enriching LE rows (which have no Customer Master) with their master grouping.

### 4.4 `SkuLu`

```
1. Read the "SkuLu" Excel sheet from the source workbook.
2. Rename column: International → Country.
3. Cast types: Country (text), SKU Description (text), SKU (text), Category (text).
4. Replace in Country: "0" → "US", "1" → "Canada".
```

Output: `{SKU, SKU Description, Category, Country}`.

**CONFIDENTIALITY NOTE:** `SKU Description` and `Category` are secrets. The `SkuLu` table must be loadable and joinable but `SKU Description` and `Category` values must never appear in test fixtures or persisted test databases. Test fixtures for `SkuLu` must use fabricated values (e.g., `"Widget A"`, `"Category X"`). `Country` values (`"US"`, `"Canada"`) are not secret.

**Sourcing question (open):** The `SkuLu` sheet is a separate named range in the workbook. It does not currently have a dedicated Python loader; see §6.

### 4.5 `AOP_NORM`

```
1. From AOP (long form, step 10 above).
2. Drop: Customer Master, Super Category, PPG, SKU Descripiton.
   Remaining: Customer, SKU #, Attribute, Value.
3. Add column: Scenario = "AOP" (literal constant).
```

Output: `{Customer, SKU #, Attribute, Scenario, Value}`.

### 4.6 `LE_NORM`

```
1. From LE (long form).
2. Drop: Super Category, PPG, SKU Descripiton.
   Remaining: Customer, SKU #, Attribute, Value.
3. Add column: Scenario = "LE" (literal constant).
```

Output: `{Customer, SKU #, Attribute, Scenario, Value}`.

### 4.7 `AopVsLe`

```
1. pd.concat([AOP_NORM, LE_NORM]).
2. Reorder: Customer, SKU #, Attribute, Scenario, Value.
3. pivot_table: index={Customer,SKU #,Attribute}, columns=Scenario, values=Value, aggfunc=sum.
4. fillna(0) on AOP and LE columns.
5. Filter: Attribute != "Cases".
6. Add: Diff = LE - AOP.
7. ClassifyTable (adds Classification column using the two-level logic in §3.3).
```

Output: `{Customer, SKU #, Attribute, AOP, LE, Diff, Classification}`.

Note: `SKU #` remains its original dtype here; it is cast to `str` in `Mix_Base`.

### 4.8 `Mix_Base`

```
1. From AopVsLe.
2. Cast SKU # to str.
3. Left-join SkuLu on SKU # = SKU.
4. Expand joined columns: SKU Description, Category, Country (fill NaN with appropriate defaults — M uses LeftOuter so unmatched get null/blank).
5. Reorder: Customer, SKU #, SKU Description, Category, Country, Attribute, AOP, LE, Diff, Classification.
6. Filter: Attribute in {"Gross Sales","Lbs","Net-Revenue $","Non-Trade $","Off Invoice $","Trade Spend $"}
           AND Classification != "inactive".
```

Output: `{Customer, SKU #, SKU Description, Category, Country, Attribute, AOP, LE, Diff, Classification}`.

### 4.9 `Rate_Impacts`

This is the most complex single transform. Steps:

```
1. From AopVsLe (buffer — compute once).
2. Filter: Classification == "normal".
3. Melt: keep {Customer, SKU #, Attribute, Classification}, unstack Scenario/Value.
   i.e., melt columns AOP, LE, Diff into Scenario/Value long format.
4. StackPivot({Attribute, Scenario}, "Value") → wide columns named "Attr - Scenario".
   e.g., "Lbs - AOP", "Lbs - LE", "Gross Sales - AOP", "Gross Sales Per Lb - Diff", etc.
5. Compute derived columns (row-wise, all normal rows):
   a. "Calc Gross Price Impact on Gross" = [Gross Sales Per Lb - Diff] * [Lbs - LE]
   b. "Calc Gross Price Impact on Net"   = [Calc Gross Price Impact on Gross]
         * (1 + [OI %GS - AOP] + [Trade %GS - AOP] + [Non-Trade %GS - AOP])
   c. "OI Rate Impact"        = [OI %GS - Diff]    * [Gross Sales - LE]
   d. "Trade Rate Impact"     = [Trade %GS - Diff]  * [Gross Sales - LE]
   e. "Non-Trade Rate Impact" = [Non-Trade %GS - Diff] * [Gross Sales - LE]
   f. "Calc Net Price Impact" = [Net Rev Per Lb - Diff] * [Lbs - LE]
6. Left-join SkuLu on SKU # → expand {SKU Description, Category, Country}.
```

Output: one row per `{Customer, SKU #}` combination (normal only), with the wide stacked columns plus the six derived impact columns plus the SkuLu enrichment columns.

**Note:** Steps 3–4 require that `AopVsLe` has already had `CalcRatios`-derived columns present. Looking at the M code carefully: `AopVsLe` is the source and it already contains ratio attributes (because both `AOP_NORM` and `LE_NORM` come from `AOP`/`LE` which had `CalcRatios` applied before melting). So `AopVsLe` long rows include ratio attributes like `"Gross Sales Per Lb"`, `"OI %GS"`, etc. for both AOP and LE scenarios. This means after `StackPivot` the columns `"Gross Sales Per Lb - AOP"`, `"Gross Sales Per Lb - LE"`, `"Gross Sales Per Lb - Diff"`, `"OI %GS - AOP"`, etc. are all available.

### 4.10 `Mix-Rollup-1`

```
groupby({Customer, Country, Category})["Calc Net Price Impact"].sum()
```

Used as a join target in `Mix-1-SKu`. Produces one row per `{Customer, Country, Category}` with the summed `Calc Net Price Impact`.

### 4.11 `Mix-1-SKu`

This is the most involved Mix-N table. Steps:

```
1. From Mix_Base (buffer).
2. groupby({Customer, Category, Country, Attribute}), sum AOP, LE, Diff.
3. Melt: AOP, LE, Diff → Scenario / Value (long).
   Rename the newly created "Attribute.1" or second attribute axis → "Scenario".
4. Filter: Scenario != "Diff".
5. AddRatios for scenarios {AOP, LE}.
   (This appends ratio rows for each scenario.)
6. pivot_table: index={Customer,Category,Country,Attribute},
               columns=Scenario, values=Value, aggfunc=sum → AOP, LE columns.
7. fillna(0) on AOP, LE.
8. Add: Diff = LE - AOP.
9. Melt back to long (Scenario in {AOP, LE, Diff}).
10. Filter: Attribute in {"Lbs", "Net Rev Per Lb", "Net-Revenue $"}.
11. StackPivot({Attribute, Scenario}, "Value") → wide columns.
12. Filter: [Lbs - AOP] != 0 AND [Lbs - LE] != 0.
13. Recompute: [Net Rev Per Lb - Diff] = [Net Rev Per Lb - LE] - [Net Rev Per Lb - AOP].
14. Add: "Calc Net Price Impact" = [Net Rev Per Lb - Diff] * [Lbs - LE].
15. Left-join Mix-Rollup-1 on {Customer, Category, Country}.
    Expand "Calc Net Price Impact" from the join (rename to "Rate-Rollup-1.Calc Net Price Impact", fill NaN with 0).
16. Add: "SKU Mix" = [Calc Net Price Impact] - [Rate-Rollup-1.Calc Net Price Impact].
```

Output: one row per `{Customer, Category, Country}` with wide stacked columns plus `Calc Net Price Impact`, `SKU Mix`.

### 4.12 `Mix-Rollup-2`

```
groupby({Customer, Country})["Calc Net Price Impact"].sum()
  (from Mix-1-SKu)
```

### 4.13 `Mix-2-Category`

Same shape as `Mix-1-SKu` but grouped by `{Customer, Country, Attribute}`. Steps:

```
1. From Mix-1-SKu (grouped by {Customer, Country}).
2. Same melt/AddRatios/pivot/StackPivot/filter pattern as Mix-1-SKu.
3. Left-join Mix-Rollup-2 on {Customer, Country}.
4. Add: "Category Mix" = [Calc Net Price Impact] - [rollup.Calc Net Price Impact].
```

### 4.14 `Mix-3-Customer`

Grouped by `{Country, Attribute}`. Additional step: `FillZeroWithAvg` applied to both AOP and LE `Net Rev Per Lb` columns after StackPivot. Then:

```
Left-join Mix-Rollup-3 on {Country}.
"Category Mix" (column name appears to be reused for Customer Mix as well in M — treat as "Customer Mix").
```

Note: the M code uses the name "Category Mix" here too, which appears to be a copy-paste in the M source. Python implementation should use a distinct name `Customer Mix` for clarity.

### 4.15 `Mix-Rollup-4`

A scalar (Python `float`):

```python
mix_rollup_4 = mix_3_customer["Calc Net Price Impact"].sum()
```

### 4.16 `Mix-4-Country`

Grouped by `{Attribute}`. `FillZeroWithAvg` applied. Then:

```
Add: "Country Mix" = [Calc Net Price Impact] - mix_rollup_4  (scalar subtraction)
```

The M code references `Mix-Rollup-4` as a scalar directly. In Python, pass it as a parameter to the function.

### 4.17 `Mix-0-Detail`

From `Mix_Base`:

```
1. Melt: AOP, LE, Diff → long (Scenario/Value).
2. Filter: Scenario != "Diff".
3. AddRatios for {AOP, LE}.
4. pivot_table → AOP, LE columns.
5. fillna(0). Add Diff = LE - AOP.
6. Melt back.
7. StackPivot({Attribute, Scenario}, "Value").
8. Add composite key columns:
   - CustSkuCountry  = Customer + " - " + SKU # + " - " + Country
   - CustCatCountry  = Customer + " - " + Category + " - " + Country
   - CustCountry     = Customer + " - " + Country
```

This is the row-level detail table feeding drill-through. No filtering on Lbs > 0 (unlike Mix-1-SKu through Mix-4-Country).

### 4.18 `Q1 Results By Sku`

**Key difference:** This query reads the raw `LE` SQLite table including the monthly columns `Jan`, `Feb`, `Mar` — columns that the main `LE` query discards. The persisted table retains them.

```
1. Read raw LE table. Select: Customer, SKU Descripiton, SKU #, GtN Mapping, Jan, Feb, Mar.
   (Drop: KEY, Type, Apr..Dec, FY, Q1..Q4, YTG, Super Category, PPG)
2. Add: Q1 = Jan + Feb + Mar.
3. groupby({Customer, SKU Descripiton, SKU #, GtN Mapping}), sum Q1.
4. pivot_table: index={Customer, SKU Descripiton, SKU #},
               columns=GtN Mapping, values=Q1, aggfunc=sum.
5. fillna(0) on measure columns.
6. Add: Net Rev = Gross Sales - Off Invoice - Non-Trade - Trade.
   (Note: signs here are pre-negation, so subtraction is used instead of addition.)
7. Rename to "$ names" (Off Invoice $, etc.).
8. CalcRatios.
```

Output: one row per `{Customer, SKU Descripiton, SKU #}` with Q1 versions of all GtN measures and ratios.

---

## 5. Recommended Module Decomposition

### 5.1 New `src/` modules

All new modules classified **T2** (Core — same rationale as existing ETL modules: bugs cause feature regressions, not data loss; per-row and cross-table tie-outs are the correctness gate).

| Module | Responsibility | Est. lines |
|---|---|---|
| `src/load_skulu.py` | Load and clean the `SkuLu` sheet into SQLite `sku_lu` table. Mirror `load_aop.py` structure. | ~200 |
| `src/mix_transforms.py` | Pure transforms: `pivot_le`, `pivot_aop`, `negate_column`, `calc_ratios`, `classify_table`, `stack_pivot`, `add_ratios`, `fill_zero_with_avg`. All pure functions, no I/O. | ~350 |
| `src/mix_lookups.py` | `build_customer_lu`, `build_aop_norm`, `build_le_norm`, `build_aop_vs_le`, `build_mix_base`. Pure transforms that depend on pivoted AOP/LE and SkuLu. | ~250 |
| `src/mix_rate_impacts.py` | `build_rate_impacts` and the six derived-impact columns. Separated because this transform is the most complex single step. | ~200 |
| `src/mix_rollups.py` | `build_mix_rollup_1..4`, `build_mix_1_sku`, `build_mix_2_category`, `build_mix_3_customer`, `build_mix_4_country`, `build_mix_0_detail`. Sequential rollup chain. | ~400 |
| `src/mix_q1.py` | `build_q1_results_by_sku`. Separate because it uses a different LE projection (monthly, not YTG). | ~100 |
| `src/mix_pipeline.py` | Orchestration: reads SQLite tables, calls transforms in topological order, writes derived tables back to SQLite. All I/O routes through `pandas_io`. No transform logic here. | ~300 |

**Total estimated new `src/` code: ~1,800 lines across 7 modules. No module exceeds 500 lines.**

### 5.2 Derived SQLite table names (snake_case)

| Power Query name | SQLite table name |
|---|---|
| `LE` (pivoted wide) | `le_wide` |
| `AOP` (pivoted wide) | `aop_wide` |
| `CustomerLU` | `customer_lu` |
| `SkuLu` | `sku_lu` |
| `AOP_NORM` | `aop_norm` |
| `LE_NORM` | `le_norm` |
| `AopVsLe` | `aop_vs_le` |
| `Mix_Base` | `mix_base` |
| `Rate_Impacts` | `rate_impacts` |
| `Mix-Rollup-1` | `mix_rollup_1` |
| `Mix-1-SKu` | `mix_1_sku` |
| `Mix-Rollup-2` | `mix_rollup_2` |
| `Mix-2-Category` | `mix_2_category` |
| `Mix-Rollup-3` | `mix_rollup_3` |
| `Mix-3-Customer` | `mix_3_customer` |
| `Mix-Rollup-4` | stored as a single-row single-column table `mix_rollup_4` or as a metadata entry |
| `Mix-4-Country` | `mix_4_country` |
| `Mix-0-Detail` | `mix_0_detail` |
| `Q1 Results By Sku` | `q1_results_by_sku` |

`mix_rollup_4` is a scalar (float). Options: persist as a one-row one-column table, or compute on demand from `mix_3_customer`. Persisting it as a table avoids recomputing but requires a special read path. Recommended: persist as a single-row table `{value: float}` and read back with `df.iloc[0, 0]`.

**Intermediate tables** (`le_wide`, `aop_wide`, `aop_norm`, `le_norm`) may optionally be omitted from the persisted database and computed in-memory only, since they are only used as inputs to higher-level tables. However, persisting them supports incremental re-runs and debugging tie-outs.

### 5.3 CLI entry point

`src/mix_pipeline.py` provides the `main()` entry point (following the pattern of `normalize_le.main` and `load_aop.main`):

```
mix-pipeline --input <workbook.xlsx> --output <database.db>
             [--le-sheet "LE-8 + 4"]
             [--aop-sheet "AOP1"]
             [--skulu-sheet "SkuLu"]
```

`main()` calls:
1. `normalize_le.load_source` + `normalize_le.normalize` + `normalize_le.write_sqlite` (or reuses the already-populated `LE` table)
2. `load_aop.load_aop` + `load_aop.persist_aop` (or reuses populated `aop` table)
3. `load_skulu.load_skulu` + `load_skulu.persist_skulu`
4. Runs the transform pipeline in topological order, writing each derived table.

All I/O routes through `src/pandas_io.read_table` and `src/pandas_io.write_table`.

### 5.4 New test files

| Test file | Covers | Est. lines |
|---|---|---|
| `tests/test_mix_transforms.py` | `negate_column`, `calc_ratios`, `classify_table`, `stack_pivot`, `add_ratios`, `fill_zero_with_avg`, `pivot_le`, `pivot_aop` — all pure | ~400 |
| `tests/test_mix_lookups.py` | `build_customer_lu`, `build_aop_norm`, `build_le_norm`, `build_aop_vs_le`, `build_mix_base` | ~300 |
| `tests/test_mix_rate_impacts.py` | `build_rate_impacts`, six derived columns | ~250 |
| `tests/test_mix_rollups.py` | Rollup chain, Mix-1-SKu through Mix-4-Country, Mix-0-Detail | ~400 |
| `tests/test_mix_q1.py` | `build_q1_results_by_sku` | ~150 |
| `tests/test_load_skulu.py` | `load_skulu` — I/O boundary, column rename, country replacement | ~150 |
| `tests/test_mix_pipeline.py` | `main()` end-to-end with in-memory SQLite (integration) | ~200 |

**Total estimated new test code: ~1,850 lines across 7 files. No file expected to exceed 500 lines.**

**Test data requirements:**
- All fixtures use fabricated customer names (Acme Foods, Globex Market, Initech Grocers, etc.) per the existing suite conventions.
- No real SKU descriptions, category names, product numbers, sales prices, or discounts.
- `SkuLu` fixture uses made-up SKU codes (`"SKU-001"`, `"SKU-002"`), fabricated descriptions (`"Widget A"`, `"Widget B"`), fabricated categories (`"Category X"`, `"Category Y"`), and only the two known Country values (`"US"`, `"Canada"`).

---

## 6. Risks and Open Questions

### 6.1 `SkuLu` sheet sourcing

**Risk (High):** No existing loader reads the `SkuLu` sheet. The current loaders read `LE-8 + 4` and `AOP1`. If the `SkuLu` sheet is in a different workbook from the two source workbooks, a third `--input` path is needed. If it is in the same workbook as `LE` or `AOP`, the existing CLI contract (single `--input`) is sufficient.

**Recommendation:** Determine which workbook contains `SkuLu` before implementation. If it is in the LE workbook, the `mix-pipeline` CLI can read it with one `--input`. If separate, add `--skulu-input`.

**Test impact:** `SkuLu` fixtures must use only fabricated values for `SKU Description` and `Category`. The `Country` replacement logic (`"0"`→`"US"`, `"1"`→`"Canada"`) is non-confidential and can be tested directly.

### 6.2 Two source workbooks vs. one

**Risk (Medium):** It is not verified from the code whether the `LE` and `AOP` data come from the same workbook or two separate workbooks. The existing CLIs take separate `--input` paths. The `mix-pipeline` CLI design should accommodate either topology via separate optional `--le-input` and `--aop-input` arguments (defaulting to the same `--input`).

### 6.3 Persisted vs. pivoted shape

**Confirmed:** Neither the `LE` nor `aop` SQLite tables are stored in pivoted form. Both must be pivoted in the Python transforms. The `pivot_le` and `pivot_aop` functions are required first steps.

### 6.4 Float tolerance for tie-outs

The CalcRatios zero-guards use `> 0` (strict). The ClassifyTable zero tests use `== 0` / `!= 0` on aggregated Lbs values. When comparing transform outputs for regression tests, a tolerance of `1e-9` is appropriate for ratio columns; exact equality is appropriate for integer-valued measure columns (Lbs, Cases).

### 6.5 `Mix-4-Country` scalar reference ambiguity

The M code references `Mix-Rollup-4` as a scalar via `List.Sum(...)`. In Python this is `mix_3_customer["Calc Net Price Impact"].sum()`. The subtraction `[Calc Net Price Impact] - Mix-Rollup-4` is a broadcast scalar subtraction on the `Mix-4-Country` DataFrame. This is straightforward in pandas but should be documented explicitly in code so the intent is clear.

### 6.6 `Mix-3-Customer` column name "Category Mix"

The M source appears to reuse the label "Category Mix" for the derived column in `Mix-3-Customer`, which logically should be "Customer Mix". This is likely a copy-paste error in the M source. The Python implementation should use `Customer Mix` in `Mix-3-Customer` and reserve `Category Mix` for `Mix-2-Category`, and document the deviation from the M source.

### 6.7 `Cases` column in `AopVsLe`

The `AOP` pivoted wide table includes a `Cases` column; `LE` does not (LE has no `Cases` GtN mapping in the source). After `AOP_NORM`+`LE_NORM` concat and pivot, the `AOP` column will have values for `Cases` but `LE` will be `0` (filled). The M code explicitly filters `Attribute != "Cases"` in `AopVsLe`, which removes this row from downstream processing. The Python implementation must replicate this filter.

### 6.8 `YTG` column optionality in `aop`

The `aop` loader marks `YTG` as optional. If the source AOP sheet predates `YTG`, the `aop` table will not have a `YTG` column, and the `pivot_aop` step must fall back to summing the `YTG_MONTHS` (May..Dec) directly — the same derivation the LE loader applies. This fallback should be implemented in `pivot_aop`.

### 6.9 `Q1 Results By Sku` month column availability

The persisted `LE` SQLite table includes `Jan`, `Feb`, `Mar` columns. This is verified from `TARGET_COLUMNS` in `normalize_le.py`. No schema gap here. The `build_q1_results_by_sku` function reads `{Jan, Feb, Mar, GtN Mapping}` plus dimension columns from the raw `LE` table.

### 6.10 `SKU #` type coercion in `Mix_Base`

The M code explicitly casts `SKU #` to `type text` before the `SkuLu` join (`"Changed Type"` step). The persisted `LE` and `aop` tables may carry `SKU #` as numeric (float). The join must use string comparison: cast `SKU #` in `AopVsLe` to `str` before joining, and ensure `SkuLu.SKU` is also `str`.

---

## 7. Recommended Evaluation Order (Final)

```
Step  Function                   Input tables                    Output table
 1    pivot_le                   LE (SQLite)                     le_wide
 2    pivot_aop                  aop (SQLite)                    aop_wide
 3    build_customer_lu          aop_wide                        customer_lu
 4    load_skulu                 SkuLu sheet                     sku_lu
 5    build_aop_norm             aop_wide                        aop_norm
 6    build_le_norm              le_wide                         le_norm
 7    build_aop_vs_le            aop_norm, le_norm               aop_vs_le
 8    build_mix_base             aop_vs_le, sku_lu               mix_base
 9    build_rate_impacts         aop_vs_le (buffer), sku_lu      rate_impacts
10    build_mix_rollup_1         rate_impacts                    mix_rollup_1
11    build_mix_1_sku            mix_base (buffer), mix_rollup_1 mix_1_sku
12    build_mix_rollup_2         mix_1_sku                       mix_rollup_2
13    build_mix_2_category       mix_1_sku, mix_rollup_2         mix_2_category
14    build_mix_rollup_3         mix_2_category                  mix_rollup_3
15    build_mix_3_customer       mix_2_category, mix_rollup_3    mix_3_customer
16    build_mix_rollup_4 (scalar) mix_3_customer                 mix_rollup_4
17    build_mix_4_country        mix_3_customer, mix_rollup_4    mix_4_country
18    build_mix_0_detail         mix_base                        mix_0_detail
19    build_q1_results_by_sku    LE (SQLite, raw)                q1_results_by_sku
```

Steps 1–4 have no inter-dependencies and can run in any order (or in parallel). Steps 5–6 depend only on step 1 or 2 respectively. All subsequent steps follow strict topological order.

---

## 8. Proposed File / Module List with Line-Count Estimates

```
src/
  load_skulu.py          ~200 lines  T2 — SkuLu sheet loader and persister
  mix_transforms.py      ~350 lines  T2 — pure transform primitives
  mix_lookups.py         ~250 lines  T2 — AOP/LE normalization and AopVsLe/Mix_Base
  mix_rate_impacts.py    ~200 lines  T2 — Rate_Impacts derived impact columns
  mix_rollups.py         ~400 lines  T2 — Mix-1..4 rollup chain + Mix-0-Detail
  mix_q1.py              ~100 lines  T2 — Q1 Results By Sku
  mix_pipeline.py        ~300 lines  T2 — orchestration and CLI entry point

tests/
  test_mix_transforms.py     ~400 lines
  test_mix_lookups.py        ~300 lines
  test_mix_rate_impacts.py   ~250 lines
  test_mix_rollups.py        ~400 lines
  test_mix_q1.py             ~150 lines
  test_load_skulu.py         ~150 lines
  test_mix_pipeline.py       ~200 lines

quality-tiers.yml   — add 7 new src/ entries at T2
```

**Total new production code: ~1,800 lines. Total new test code: ~1,850 lines. No file exceeds 500 lines.**
