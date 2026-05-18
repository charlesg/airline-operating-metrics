# Airline Operating Metrics

Structured dataset of airline operating metrics for eight carriers (five US, three LatAm), sourced from BTS Form 41, the MIT Airline Data Project, and company IR supplements.

## Carriers

|Code|Airline|Geography|
|---|---|---|
|AMERICAN|American Airlines|US|
|DELTA|Delta Air Lines|US|
|JETBLUE|JetBlue Airways|US|
|SOUTHWEST|Southwest Airlines|US|
|UNITED|United Airlines|US|
|AVIANCA|Avianca|LatAm|
|COPA|Copa Airlines|LatAm|
|LATAM|LATAM Airlines|LatAm|

## Layout

```text
raw/          # One CSV per airline — append-only, source-reported metrics only
processed/    # Derived and calculated metrics
sources/      # Original source documents (PDFs, IR supplements, BTS downloads)
scripts/      # Validation and crosscheck scripts
```

See [CLAUDE.md](CLAUDE.md) for the full schema, metric vocabulary, unit conventions, and data entry rules.

## BTS Source Files

The smaller BTS schedules are versioned under `sources/<year>/`:

|File|Schedule|Direct link|
|---|---|---|
|`T_F41SCHEDULE_P12.csv`|P-1.2 (P&L)|[Fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMI)|
|`T_F41SCHEDULE_P12A.csv`|P-12(a) (Fuel)|[Fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMH)|
|`T_F41SCHEDULE_P52.csv`|P-5.2 (Aircraft)|[Fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=FMK)|

**T-100 Segment files are not in the repo** — at ~150MB each they exceed GitHub's file size limit. To reproduce the BTS crosscheck:

1. Download **T-100 Segment (US Carriers Only)** from [BTS TranStats](https://www.transtats.bts.gov/) ([Fields](https://www.transtats.bts.gov/Fields.asp?gnoyr_VQ=GDM)) for each year you need
2. Place files at `sources/<year>/T_T100_SEGMENT_US_CARRIER_ONLY.csv`
3. Run `python scripts/bts_crosscheck.py`

## Quick Start

```python
import pandas as pd, glob

# Load all carriers
df = pd.concat([pd.read_csv(f) for f in glob.glob("raw/*.csv")], ignore_index=True)

# Compare a metric across carriers
df[df["metric"] == "CASK"].pivot_table(
    index=["year", "quarter"], columns="airline", values="value"
)
```
