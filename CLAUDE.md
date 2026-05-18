# Airline Operating Metrics Dataset

## Project Purpose

Build and maintain a structured dataset of airline operating metrics sourced
exclusively from free public sources (DOT BTS Form 41, MIT Airline Data
Project, and company IR supplements). The dataset supports both spreadsheet
analysis (Excel, Google Sheets) and Python/pandas analysis.

---

## Project Layout

```
airlines_data/          # Claude Code project root
  CLAUDE.md
  sources/              # Original source files (PDFs, screenshots, IR supplements)
  raw/                  # One CSV per airline — append only, never edit in place
    american.csv
    avianca.csv
    copa.csv
    delta.csv
    jetblue.csv
    latam.csv
    southwest.csv
    united.csv
  processed/            # Derived, calculated, or contextual data
    colombia_market_share.csv
```

**`raw/`** contains only observable, source-reported metrics. No calculated
or derived values (no NEEDED_INCREASE, no EBITDA-INT/ASK ratios, etc.).

**`processed/`** contains everything derived: calculated metrics, market
share data, normalized cross-carrier views, or any data that cannot be
directly traced to a single source figure.

**`sources/`** stores the original documents (IR supplement PDFs, screenshots,
BTS downloads) that back the raw/ entries. Filename convention:
`<AIRLINE>_<PERIOD>_<source_type>.<ext>` — e.g., `COPA_FY2025_IR.pdf`.

---

## Current Airlines

| Code      | Full Name          | Geography | Primary Source                                     |
|-----------|--------------------|-----------|----------------------------------------------------|
| AMERICAN  | American Airlines  | US        | BTS Form 41, IR supplement                         |
| AVIANCA   | Avianca            | LatAm     | IR supplement (investor.avianca.com)               |
| COPA      | Copa Airlines      | LatAm     | IR supplement (investors.copa.com)                 |
| DELTA     | Delta Air Lines    | US        | BTS Form 41, IR supplement                         |
| JETBLUE   | JetBlue Airways    | US        | BTS Form 41, IR supplement                         |
| LATAM     | LATAM Airlines     | LatAm     | IR supplement (investor.latamairlinesgroup.net)     |
| SOUTHWEST | Southwest Airlines | US        | BTS Form 41, IR supplement                         |
| UNITED    | United Airlines    | US        | BTS Form 41, IR supplement                         |

### Notes on specific carriers
- **LATAM and Avianca**: have restructuring gaps in historical data (bankruptcy
  periods). Treat pre-2022 data with caution.
- **JetBlue and Southwest**: report in ASM/RPM (miles), not ASK/RPK (km).
  Their `unit` values will differ from LatAm carriers — see unit vocabulary.
- **LatAm carriers**: unit costs reported in `usd_per_ask`; US carriers report
  in `cents_per_ask`. Same economic concept, different scale — always check
  `unit` column before cross-carrier comparisons.

---

## Data Sources

### US Carriers
- **MIT Airline Data Project**: https://web.mit.edu/airlinedata/www/default.html
- **BTS Form 41**: https://www.transtats.bts.gov/
  - Schedule P-12: Operating statistics (ASM, RPM, load factor)
  - Schedule P-5.2: Unit costs (CASK, CASK_EX, FUEL_CASK)
- **IR Supplements**: Quarterly data books on each airline's IR page

### LatAm Carriers
- **Copa**: https://investors.copa.com
- **LATAM**: https://investor.latamairlinesgroup.net
- **Avianca**: https://investor.avianca.com

### Colombia Market Data (processed/ only)
- **Aerocivil**: Colombian civil aviation authority — passenger traffic and
  market share by carrier, domestic and international

---

## Storage Format

### Schema (all raw/ files)

| Column  | Type   | Description                                           |
|---------|--------|-------------------------------------------------------|
| airline | string | Carrier code in uppercase (e.g., COPA, DELTA)         |
| year    | int    | Fiscal year as integer (e.g., 2025)                   |
| quarter | string | `FY` for full year, `Q1`–`Q4` for quarterly          |
| metric  | string | Metric name — must use controlled vocabulary below    |
| value   | float  | Numeric value only — no `$`, `,`, `%`, parentheses   |
| unit    | string | Unit of measure — must use controlled vocabulary below|
| source  | string | Source document identifier (e.g., `IR-FY2025-COPA`)  |

### Formatting rules (critical for pandas/Excel compatibility)
- **Blank values**: empty string (not `NA`, not `NULL`, not `-999`) — pandas
  reads blank as `NaN` automatically; Excel/Sheets shows a clean blank cell
- **Negative numbers**: plain negative float (e.g., `-679000`) — never
  accounting parentheses like `(679000)`, which break numeric parsing
- **Percentages**: stored as decimals (e.g., `0.04` for 4%, `0.86` for 86%)
  with `unit = decimal`
- **Column headers**: lowercase with underscores — no spaces
- **Encoding**: UTF-8, comma delimiter

### Spine consistency rule
Every `(year, quarter, metric)` combination that exists for any airline must
exist as a row in every airline file. Airlines missing that data get an empty
`value` and `source = placeholder`. This ensures pivot operations always
produce rectangular output with no missing index combinations.

---

## Metric Controlled Vocabulary

Always use these exact strings in the `metric` column:

| Metric              | Description                                     |
|---------------------|-------------------------------------------------|
| ASM                 | Available Seat Miles                            |
| ASK                 | Available Seat Kilometers                       |
| RPM                 | Revenue Passenger Miles                         |
| RPK                 | Revenue Passenger Kilometers                    |
| LOAD_FACTOR         | RPM/ASM or RPK/ASK — stored as decimal         |
| TOTAL_RASK          | Total Revenue per ASK                           |
| PAX_RASK            | Passenger Revenue per ASK                       |
| YIELD               | Revenue per RPM or RPK                          |
| CASK                | Total Cost per ASK                              |
| CASK_EX             | CASK excluding fuel                             |
| FUEL_CASK           | Fuel cost per ASK                               |
| PRASK               | Ancillary/other revenue per ASK                 |
| OPERATING_REVENUE   | Total operating revenue (absolute)              |
| OPERATING_COST      | Total operating cost (absolute)                 |
| EBITDA              | EBITDA (absolute)                               |
| EBITDA_MARGIN       | EBITDA / Operating Revenue — stored as decimal  |
| EBITDA_ASK          | EBITDA per ASK                                  |
| EBITDA_INT          | EBITDA minus Interest expense                   |
| DEPRECIATION        | Depreciation and amortization (absolute)        |
| NET_INCOME          | Net income (absolute)                           |
| INTEREST            | Interest expense — negative = expense           |
| TOTAL_DEBT          | Total financial debt (absolute)                 |
| OPERATING_CASH_FLOW | Cash from operations (absolute)                 |
| NET_CASH_FLOW       | Net change in cash (absolute)                   |
| FUEL_COST           | Total fuel cost (absolute)                      |
| MAINTENANCE_COST    | Total maintenance cost (absolute)               |
| SALARIES            | Total salaries and benefits (absolute)          |
| LANDING_FEES        | Total landing and navigation fees (absolute)    |
| AIRPLANES           | Fleet size (count of aircraft)                  |
| DEPARTURES          | Total departures (count)                        |

---

## Unit Controlled Vocabulary

Always use these exact strings in the `unit` column:

| Unit          | Used for                                                   |
|---------------|------------------------------------------------------------|
| millions      | ASM/RPM (US carriers, miles); ASK/RPK (LatAm carriers, km) |
| decimal       | LOAD_FACTOR, EBITDA_MARGIN, any percentage stored as 0-1   |
| cents_per_ask | Unit costs, US carriers: CASK, CASK_EX, FUEL_CASK,         |
|               | PRASK, TOTAL_RASK, PAX_RASK, YIELD, EBITDA_ASK             |
| usd_per_ask   | Unit costs, LatAm carriers: same metrics, USD scale        |
| thousands_USD | Absolute financials in USD (all carriers)                  |
| units         | AIRPLANES (aircraft count), DEPARTURES (flight count)      |

**Cross-carrier unit warning**: US carriers report capacity in `millions`
(miles), LatAm in `millions` (km). Unit costs also differ in scale
(`cents_per_ask` vs `usd_per_ask`). Always filter or normalize by `unit`
before cross-carrier arithmetic.

---

## Python Usage

### Load a single airline
```python
import pandas as pd

df = pd.read_csv('raw/copa.csv')
```

### Wide view for analysis (pivot)
```python
# All metrics for one airline, one year — rows=quarter, cols=metric
wide = df[df['year'] == 2025].pivot_table(
    index=['airline', 'quarter'],
    columns='metric',
    values='value'
)
```

### Load and combine all airlines
```python
import glob

all_carriers = pd.concat([
    pd.read_csv(f) for f in glob.glob('raw/*.csv')
], ignore_index=True)
```

### Compare a single metric across carriers
```python
cask = all_carriers[all_carriers['metric'] == 'CASK'].pivot_table(
    index=['year', 'quarter'],
    columns='airline',
    values='value'
)
```

### Filter to comparable unit groups before cross-carrier math
```python
# US carriers only (cents_per_ask)
us_costs = all_carriers[
    (all_carriers['metric'] == 'CASK') &
    (all_carriers['unit'] == 'cents_per_ask')
]

# LatAm carriers only (usd_per_ask)
latam_costs = all_carriers[
    (all_carriers['metric'] == 'CASK') &
    (all_carriers['unit'] == 'usd_per_ask')
]
```

### Convert to Parquet (optional, for larger datasets)
```python
all_carriers.to_parquet('processed/all_carriers.parquet', index=False)
# Query with DuckDB if desired
import duckdb
duckdb.query("""
    SELECT airline, metric, value
    FROM 'processed/all_carriers.parquet'
    WHERE year = 2025
""").df()
```

---

## Excel / Google Sheets Usage

1. Open any `raw/*.csv` directly — UTF-8, no reformatting needed
2. Insert PivotTable: rows = `year` / `quarter`, columns = `metric`,
   values = `value`
3. Add `airline` as a slicer or page filter to compare carriers
4. To combine all carriers: use Power Query (Excel) or IMPORTDATA +
   QUERY (Sheets) to append all CSVs, then pivot
5. Watch the `unit` column — filter to a single unit before charting
   cross-carrier comparisons

---

## Data Entry Rules

1. **Append only** — never overwrite an existing row in `raw/`. If a value
   needs correction, add a new row with an updated `source` noting the fix
   (e.g., `IR-FY2025-COPA-corrected`). The most recent row wins in analysis.
2. **No calculated metrics in raw/** — NEEDED_INCREASE, EBITDA-INT/ASK,
   year-over-year changes all belong in `processed/` or analysis scripts.
3. **Maintain spine consistency** — when adding a new metric for any airline,
   add placeholder rows (empty `value`, `source = placeholder`) for all
   other airlines for the same `(year, quarter, metric)` combination.
4. **Strip all formatting** — no `$`, `,`, `%`, or `()` in the `value` column.
5. **Negative numbers** as plain floats — e.g., `-558573` not `(558573)`.
6. **Percentages as decimals** — `0.86` not `86` or `86%`.
7. **Store source files** — drop the original PDF or screenshot in `sources/`
   before entering data, using the naming convention above.

---

## Expanding the Dataset

### Add a new period (quarter or year)
1. Save the IR supplement PDF to `sources/` with standard naming
2. Extract metrics using the controlled vocabulary
3. Append rows to `raw/<airline>.csv`
4. Run spine consistency check — add placeholders to other airlines as needed
5. Commit: `feat: add COPA Q2-2026 from IR supplement`

### Add a new airline
1. Create `raw/<airline_code_lowercase>.csv` with the standard header row
2. Add the IR page URL to the Data Sources section of this file
3. Note any currency, unit, or reporting quirks for that carrier
4. Add placeholder rows for all existing `(year, quarter, metric)` combos
5. Commit: `feat: add SPIRIT airline skeleton`

### Spine consistency check (Python)
```python
import pandas as pd, glob

dfs = {f.split('/')[-1].replace('.csv', ''): pd.read_csv(f)
       for f in glob.glob('raw/*.csv')}

all_combos = set()
for df in dfs.values():
    all_combos |= set(zip(df['year'], df['quarter'], df['metric']))

for airline, df in sorted(dfs.items()):
    existing = set(zip(df['year'], df['quarter'], df['metric']))
    missing = all_combos - existing
    if missing:
        print(f"{airline}: {len(missing)} missing combos")
    else:
        print(f"{airline}: spine OK")
```
