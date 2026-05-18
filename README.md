# Airline Operating Metrics

Structured dataset of airline operating metrics for eight carriers (five US, three LatAm), sourced from BTS Form 41, the MIT Airline Data Project, and company IR supplements.

## Carriers

| Code | Airline | Geography |
|------|---------|-----------|
| AMERICAN | American Airlines | US |
| DELTA | Delta Air Lines | US |
| JETBLUE | JetBlue Airways | US |
| SOUTHWEST | Southwest Airlines | US |
| UNITED | United Airlines | US |
| AVIANCA | Avianca | LatAm |
| COPA | Copa Airlines | LatAm |
| LATAM | LATAM Airlines | LatAm |

## Layout

```
raw/          # One CSV per airline — append-only, source-reported metrics only
processed/    # Derived and calculated metrics
sources/      # Original source documents (PDFs, IR supplements, BTS downloads)
scripts/      # Validation and crosscheck scripts
```

See [CLAUDE.md](CLAUDE.md) for the full schema, metric vocabulary, unit conventions, and data entry rules.

## Large BTS Source Files (not in repo)

The T-100 Segment files (`T_T100_SEGMENT_US_CARRIER_ONLY.csv`) are ~150MB each and exceed GitHub's file size limit. They are not versioned here. To reproduce the BTS crosscheck:

1. Go to [BTS TranStats](https://www.transtats.bts.gov/)
2. Download **T-100 Segment (US Carriers Only)** for each year you need
3. Place files at `sources/<year>/T_T100_SEGMENT_US_CARRIER_ONLY.csv`
4. Run `python scripts/bts_crosscheck.py`

The smaller BTS schedules (P-1.2, P-12(a), P-5.2) are included in the repo under `sources/<year>/`.

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
