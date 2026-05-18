# Airlines Data — TODO

## Data Validation

- [x] Build BTS cross-check script for US carriers → `scripts/bts_crosscheck.py`; uses T-100 Segment + P-1.2 + P-12(a) from `sources/<year>/`
- [x] Fix ASM/RPM unit label: corrected `thousands` → `millions` in all five US carrier CSVs and CLAUDE.md
- [x] Fix 2024 financial data (OPERATING_REVENUE, OPERATING_COST, NET_INCOME, DEPRECIATION): original "FY" rows were Q1-Q3 only; correct FY 2024 totals appended from BTS P-1.2 (`source: bts-p12-fy2024`)
- [x] Fix 2025 financial data: BTS Q4 2025 filed; correct FY 2025 totals appended from BTS P-1.2 (`source: bts-p12-fy2025`) for all five US carriers; crosscheck passes at +0.0% for OPERATING_REVENUE, OPERATING_COST, NET_INCOME, DEPRECIATION
- [ ] Investigate fuel cost discrepancies: JetBlue 2024 (+41.7% vs BTS) and American 2025 (+32.3%) — check against original source documents
- [ ] Build IR supplement cross-check for LatAm carriers (Copa, LATAM, Avianca): compare ASK, RPK, LOAD_FACTOR, TOTAL_RASK, CASK against published PDFs in `sources/`
- [ ] Add a validation notebook section (or standalone script) that flags rows where our value deviates >2% from the source-verified figure and outputs a discrepancy report

## Recalculation of Derived Metrics

- [ ] Write a recalc script in `processed/` that derives: LOAD_FACTOR (RPK/ASK, RPM/ASM), CASK_EX ((OPERATING_COST − FUEL_COST)/ASK), FUEL_CASK (FUEL_COST/ASK), TOTAL_RASK (OPERATING_REVENUE/ASK), PAX_RASK, YIELD, EBITDA_MARGIN (EBITDA/OPERATING_REVENUE), EBITDA_ASK (EBITDA/ASK), EBITDA_INT (EBITDA − INTEREST)
- [ ] Compare recalculated values against imported values already in `raw/` and flag discrepancies — helps identify import errors or rounding differences

## Historical Extension (back to 2020)

- [ ] Download BTS Form 41 (P-12 + P-5.2) for US carriers 2020–2023 and append to `raw/` CSVs (American, Delta, United, Southwest, JetBlue)
- [ ] Collect Copa IR supplement historical data 2020–2023 from investors.copa.com and append to `raw/copa.csv` (Copa had no bankruptcy — data should be clean)
- [ ] Collect LATAM and Avianca historical data 2022–2023 (post-bankruptcy) from their IR pages; add placeholder rows with notes for 2020–2021 bankruptcy gap years
- [ ] Run spine consistency check after all historical rows are added; fill missing (year, quarter, metric) combinations with placeholder rows across all carriers

## Analysis

- [ ] RASK vs CASK spread: revenue-over-cost margin trend per carrier over time — identifies who is widening or compressing their operating margin
- [ ] Load factor efficiency: LOAD_FACTOR vs YIELD scatter — who fills planes vs who charges more per seat
- [ ] Cost structure breakdown: FUEL_CASK, CASK_EX, SALARIES/ASK, MAINTENANCE_COST/ASK stacked comparison — shows who has structural cost advantages
- [ ] COVID recovery trajectory: 2020–2025 ASK/ASM and LOAD_FACTOR indexed to 2019 baseline — pace of recovery by carrier and region (US vs LatAm)
- [ ] Colombia market share evolution: Avianca domestic share loss vs LATAM/Copa gains using `processed/colombia_market_share.csv` extended over time
- [ ] EBITDA margin benchmarking: LatAm vs US carriers side-by-side, controlling for fuel price environment — who is structurally more profitable
