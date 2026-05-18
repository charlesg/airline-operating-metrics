#!/usr/bin/env python3
"""
bts_crosscheck.py — Cross-check raw/ US carrier data against downloaded BTS files.

Files used (auto-discovered from sources/<year>/ subdirectories)
----------------------------------------------------------------
  T_T100_SEGMENT_US_CARRIER_ONLY.csv  → ASM, RPM, LOAD_FACTOR
      ASM = sum(SEATS × DISTANCE) for scheduled passenger service (CLASS='F')
      RPM = sum(PASSENGERS × DISTANCE)
      LOAD_FACTOR = RPM / ASM

  T_F41SCHEDULE_P12.csv               → OPERATING_REVENUE, OPERATING_COST,
                                         NET_INCOME, DEPRECIATION, INTEREST
      NOTE: BTS files this by carrier entity AND geographic region
      (Domestic / Atlantic / Latin / Pacific). Summing all entities gives
      totals consistent with the full airline system P&L.

  T_F41SCHEDULE_P12A.csv              → FUEL_COST (absolute)
      TOTAL_COST is in raw dollars — divided by 1,000 to match thousands_USD.

Derived metrics (computed from above)
--------------------------------------
  CASK      = OP_EXPENSES_thousands × 0.1 / ASM_millions   [cents/mile]
  CASK_EX   = (OP_EXPENSES − FUEL_COST)_thousands × 0.1 / ASM_millions
  FUEL_CASK = FUEL_COST_thousands × 0.1 / ASM_millions

  T_F41SCHEDULE_P52.csv is downloaded but reserved for future aircraft-level
  cost breakdowns; it is not used in the current cross-check.

Usage
-----
  python scripts/bts_crosscheck.py                      # auto-discover all years
  python scripts/bts_crosscheck.py --year 2024          # single year
  python scripts/bts_crosscheck.py --tolerance 0.05     # wider tolerance
  python scripts/bts_crosscheck.py --sources path/to/   # alternate sources dir

Output
------
  Console:  PASS / WARN / FAIL summary per metric per carrier
  File:     processed/bts_crosscheck_report.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent
RAW_DIR   = ROOT / "raw"
PROCESSED = ROOT / "processed"

# ── BTS carrier code → our airline code ────────────────────────────────────
CARRIER_MAP = {
    "AA": "AMERICAN",
    "DL": "DELTA",
    "UA": "UNITED",
    "WN": "SOUTHWEST",
    "B6": "JETBLUE",
}

DEFAULT_TOLERANCE = 0.02  # 2 %


# ── File discovery ─────────────────────────────────────────────────────────

def find_bts_files(sources_dir: Path) -> dict[str, list[Path]]:
    """
    Scan sources/<year>/ subdirectories and return a dict mapping
    BTS file stem → sorted list of paths (one per year subfolder).
    """
    stems = {
        "t100":  "T_T100_SEGMENT_US_CARRIER_ONLY",
        "p12":   "T_F41SCHEDULE_P12",
        "p12a":  "T_F41SCHEDULE_P12A",
    }
    found: dict[str, list[Path]] = {k: [] for k in stems}
    for year_dir in sorted(sources_dir.iterdir()):
        if not year_dir.is_dir():
            continue
        for key, stem in stems.items():
            f = year_dir / f"{stem}.csv"
            if f.exists():
                found[key].append(f)
    return found


# ── Loaders ────────────────────────────────────────────────────────────────

def load_t100(paths: list[Path], years: list[int]) -> pd.DataFrame | None:
    """
    Compute ASM, RPM, LOAD_FACTOR from T-100 Segment files.

    Filters to CLASS='F' (scheduled passenger service) which is what airlines
    use in their published traffic statistics.  ASM/RPM are returned in
    thousands of miles to match our raw/ convention.
    """
    if not paths:
        return None
    print(f"  T-100 Segment: reading {len(paths)} file(s)")
    df = pd.concat([pd.read_csv(p, low_memory=False) for p in paths], ignore_index=True)

    df["YEAR"]       = pd.to_numeric(df["YEAR"],       errors="coerce")
    df["SEATS"]      = pd.to_numeric(df["SEATS"],      errors="coerce")
    df["PASSENGERS"] = pd.to_numeric(df["PASSENGERS"], errors="coerce")
    df["DISTANCE"]   = pd.to_numeric(df["DISTANCE"],   errors="coerce")

    df = df[
        df["UNIQUE_CARRIER"].isin(CARRIER_MAP) &
        df["YEAR"].isin(years) &
        df["CLASS"].eq("F")          # scheduled passenger only
    ].copy()

    df["airline"] = df["UNIQUE_CARRIER"].map(CARRIER_MAP)
    df["_asm"]    = df["SEATS"]      * df["DISTANCE"]
    df["_rpm"]    = df["PASSENGERS"] * df["DISTANCE"]

    agg = (
        df.groupby(["airline", "YEAR"])[["_asm", "_rpm"]]
          .sum()
          .reset_index()
          .rename(columns={"YEAR": "year"})
    )
    # BTS raw miles → millions to match raw/ convention (unit = millions)
    agg["asm_bts"] = agg["_asm"] / 1_000_000
    agg["rpm_bts"] = agg["_rpm"] / 1_000_000
    agg["lf_bts"]  = agg["_rpm"] / agg["_asm"]

    return agg[["airline", "year", "asm_bts", "rpm_bts", "lf_bts"]]


def load_p12(paths: list[Path], years: list[int]) -> pd.DataFrame | None:
    """
    Load P-1.2 quarterly P&L data.

    BTS files by carrier entity AND geographic region (D/A/L/P). Summing all
    entities for a carrier+year gives the consolidated system total, which
    aligns with what airlines report in their 10-K and IR supplements.

    All P-1.2 values are in thousands of USD (same as our raw/ convention).
    """
    if not paths:
        return None
    print(f"  P-1.2 (P&L): reading {len(paths)} file(s)")
    df = pd.concat([pd.read_csv(p, low_memory=False) for p in paths], ignore_index=True)

    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df = df[df["UNIQUE_CARRIER"].isin(CARRIER_MAP) & df["YEAR"].isin(years)].copy()
    df["airline"] = df["UNIQUE_CARRIER"].map(CARRIER_MAP)

    for col in ["OP_REVENUES", "OP_EXPENSES", "NET_INCOME", "DEPREC_AMORT",
                "INTEREST_LONG_DEBT"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    agg = (
        df.groupby(["airline", "YEAR"])
          .agg(
              op_rev_bts   =("OP_REVENUES",        "sum"),
              op_exp_bts   =("OP_EXPENSES",         "sum"),
              net_inc_bts  =("NET_INCOME",           "sum"),
              deprec_bts   =("DEPREC_AMORT",         "sum"),
              interest_bts =("INTEREST_LONG_DEBT",   "sum"),
          )
          .reset_index()
          .rename(columns={"YEAR": "year"})
    )
    return agg


def load_p12a(paths: list[Path], years: list[int]) -> pd.DataFrame | None:
    """
    Load P-12(a) monthly fuel cost data.

    TOTAL_COST is in raw dollars; divided by 1,000 here to yield thousands_USD
    matching our raw/ convention.
    """
    if not paths:
        return None
    print(f"  P-12(a) (Fuel): reading {len(paths)} file(s)")
    df = pd.concat([pd.read_csv(p, low_memory=False) for p in paths], ignore_index=True)

    df["YEAR"]       = pd.to_numeric(df["YEAR"],       errors="coerce")
    df["TOTAL_COST"] = pd.to_numeric(df["TOTAL_COST"], errors="coerce")

    df = df[df["UNIQUE_CARRIER"].isin(CARRIER_MAP) & df["YEAR"].isin(years)].copy()
    df["airline"] = df["UNIQUE_CARRIER"].map(CARRIER_MAP)

    agg = (
        df.groupby(["airline", "YEAR"])["TOTAL_COST"]
          .sum()
          .reset_index()
          .rename(columns={"YEAR": "year", "TOTAL_COST": "fuel_cost_bts_raw"})
    )
    # Convert dollars → thousands_USD
    agg["fuel_cost_bts"] = agg["fuel_cost_bts_raw"] / 1_000
    return agg[["airline", "year", "fuel_cost_bts"]]


# ── Load our raw/ data ─────────────────────────────────────────────────────

def load_our_data(years: list[int]) -> pd.DataFrame:
    metrics = [
        "ASM", "RPM", "LOAD_FACTOR",
        "CASK", "CASK_EX", "FUEL_CASK",
        "OPERATING_REVENUE", "OPERATING_COST",
        "NET_INCOME", "DEPRECIATION", "INTEREST", "FUEL_COST",
    ]
    dfs = []
    for airline in CARRIER_MAP.values():
        p = RAW_DIR / f"{airline.lower()}.csv"
        if p.exists():
            dfs.append(pd.read_csv(p))
    if not dfs:
        sys.exit("No raw/ US carrier files found.")

    df = pd.concat(dfs, ignore_index=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"]  = pd.to_numeric(df["year"],  errors="coerce")

    df = df[
        df["metric"].isin(metrics) &
        df["quarter"].eq("FY") &
        df["year"].isin(years) &
        df["value"].notna()
    ]
    df = df.sort_values("source").drop_duplicates(
        subset=["airline", "year", "metric"], keep="last"
    )
    return df.pivot_table(
        index=["airline", "year"],
        columns="metric",
        values="value",
        aggfunc="last",
    ).reset_index()


# ── Build BTS reference table ──────────────────────────────────────────────

def build_bts_reference(t100: pd.DataFrame | None,
                         p12:  pd.DataFrame | None,
                         p12a: pd.DataFrame | None) -> pd.DataFrame:
    """
    Merge T-100, P-1.2, and P-12(a) into one reference DataFrame and
    compute derived metrics (CASK, CASK_EX, FUEL_CASK).
    """
    # Start from carrier × year grid of carriers we care about
    all_keys = set()
    for src in [t100, p12, p12a]:
        if src is not None:
            all_keys |= set(zip(src["airline"], src["year"]))

    if not all_keys:
        return pd.DataFrame(columns=["airline", "year"])

    ref = pd.DataFrame(list(all_keys), columns=["airline", "year"])
    if t100  is not None: ref = ref.merge(t100,  on=["airline", "year"], how="left")
    if p12   is not None: ref = ref.merge(p12,   on=["airline", "year"], how="left")
    if p12a  is not None: ref = ref.merge(p12a,  on=["airline", "year"], how="left")

    # Derived unit-cost metrics (cents per available seat mile)
    # Formula: (cost_thousands × 1000 USD × 100 ¢/$) / (asm_millions × 1e6 miles)
    #        = cost_thousands × 0.1 / asm_millions
    if "op_exp_bts" in ref.columns and "asm_bts" in ref.columns:
        ref["cask_bts"] = ref["op_exp_bts"] * 0.1 / ref["asm_bts"]

    if all(c in ref.columns for c in ["op_exp_bts", "fuel_cost_bts", "asm_bts"]):
        ref["cask_ex_bts"] = (ref["op_exp_bts"] - ref["fuel_cost_bts"]) * 0.1 / ref["asm_bts"]

    if "fuel_cost_bts" in ref.columns and "asm_bts" in ref.columns:
        ref["fuel_cask_bts"] = ref["fuel_cost_bts"] * 0.1 / ref["asm_bts"]

    return ref


# ── Compare ────────────────────────────────────────────────────────────────

# (our_col, bts_col, note)
# note flags metrics where BTS methodology may differ from IR supplement reporting
CHECKS = [
    ("ASM",              "asm_bts",         ""),
    ("RPM",              "rpm_bts",         ""),
    ("LOAD_FACTOR",      "lf_bts",          ""),
    ("FUEL_COST",        "fuel_cost_bts",   ""),
    ("CASK",             "cask_bts",        "derived"),
    ("CASK_EX",          "cask_ex_bts",     "derived"),
    ("FUEL_CASK",        "fuel_cask_bts",   "derived"),
    ("OPERATING_REVENUE","op_rev_bts",      "p12_sum"),
    ("OPERATING_COST",   "op_exp_bts",      "p12_sum"),
    ("NET_INCOME",       "net_inc_bts",     "p12_sum"),
    ("DEPRECIATION",     "deprec_bts",      "p12_sum"),
]


def compare(our: pd.DataFrame, ref: pd.DataFrame, tolerance: float) -> pd.DataFrame:
    base = our.merge(ref, on=["airline", "year"], how="left")
    rows = []

    for our_col, bts_col, note in CHECKS:
        for _, row in base.iterrows():
            our_val = row.get(our_col)
            bts_val = row.get(bts_col) if bts_col in base.columns else None

            if pd.isna(our_val) if our_val is not None else True:
                status, delta_pct = "NO_DATA", None
            elif bts_val is None or (isinstance(bts_val, float) and pd.isna(bts_val)):
                status, delta_pct = "BTS_MISSING", None
            else:
                delta_pct = (our_val - bts_val) / bts_val if bts_val != 0 else None
                if delta_pct is None:
                    status = "DIV_ZERO"
                elif abs(delta_pct) <= tolerance:
                    status = "PASS"
                elif abs(delta_pct) <= tolerance * 2:
                    status = "WARN"
                else:
                    status = "FAIL"

            rows.append({
                "airline":   row["airline"],
                "year":      int(row["year"]),
                "metric":    our_col,
                "note":      note,
                "our_value": our_val,
                "bts_value": bts_val,
                "delta_pct": round(delta_pct * 100, 2) if delta_pct is not None else None,
                "status":    status,
            })

    return pd.DataFrame(rows)


# ── Print summary ──────────────────────────────────────────────────────────

def print_summary(report: pd.DataFrame, tolerance: float) -> None:
    print(f"\n{'='*80}")
    print(f"BTS Form 41 Cross-Check  (tolerance ±{tolerance*100:.0f}%)")
    print(f"  derived = computed from P-1.2 costs ÷ T-100 ASM")
    print(f"  p12_sum = sum of all BTS regional entities; may differ from consolidated IR figures")
    print(f"{'='*80}")

    order = {"FAIL": 0, "WARN": 1, "PASS": 2, "BTS_MISSING": 3, "NO_DATA": 4, "DIV_ZERO": 5}
    report["_ord"] = report["status"].map(order)
    report = report.sort_values(["_ord", "airline", "year", "metric"])

    for status in ["FAIL", "WARN", "PASS", "BTS_MISSING", "NO_DATA"]:
        sub = report[report["status"] == status]
        if sub.empty:
            continue
        print(f"\n── {status} ({len(sub)}) {'─'*(55 - len(status))}")
        for _, r in sub.iterrows():
            delta  = f"  Δ {r['delta_pct']:+.1f}%" if r["delta_pct"] is not None else ""
            our    = f"{r['our_value']:>14,.2f}" if pd.notna(r["our_value"]) else "           n/a"
            bts    = f"{r['bts_value']:>14,.2f}" if pd.notna(r["bts_value"]) else "           n/a"
            flag   = f"  [{r['note']}]" if r["note"] else ""
            print(f"  {r['airline']:<12} {r['year']}  {r['metric']:<18}"
                  f"  ours={our}  bts={bts}{delta}{flag}")

    counts = report["status"].value_counts()
    print(f"\n{'─'*80}")
    print(f"  PASS={counts.get('PASS',0)}  WARN={counts.get('WARN',0)}  "
          f"FAIL={counts.get('FAIL',0)}  BTS_MISSING={counts.get('BTS_MISSING',0)}  "
          f"NO_DATA={counts.get('NO_DATA',0)}")
    print(f"{'='*80}\n")


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--year",      type=int, nargs="+", default=None,
                        help="Year(s) to check. Default: all years in raw/delta.csv")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                        help="Acceptable deviation fraction (default 0.02 = 2%%)")
    parser.add_argument("--sources",   type=Path, default=ROOT / "sources",
                        help="Root of BTS sources directory (default: sources/)")
    args = parser.parse_args()

    if args.year:
        years = args.year
    else:
        sample = pd.read_csv(RAW_DIR / "delta.csv")
        years = sorted(sample["year"].dropna().unique().astype(int).tolist())
    print(f"Checking years: {years}")

    # Discover BTS files
    files = find_bts_files(args.sources)
    missing = [k for k, v in files.items() if not v]
    if missing:
        print(f"\n  ⚠  No files found for: {missing}")
        print(f"  Expected in {args.sources}/<year>/ subdirectories")

    # Load BTS sources
    print("\nLoading BTS sources …")
    t100 = load_t100(files["t100"], years)
    p12  = load_p12(files["p12"],   years)
    p12a = load_p12a(files["p12a"], years)

    # Build reference
    ref = build_bts_reference(t100, p12, p12a)
    print(f"  BTS reference: {len(ref)} airline×year rows")

    # Load our data
    print("\nLoading raw/ US carrier data …")
    our = load_our_data(years)
    print(f"  {len(our)} airline×year rows")

    # Compare and report
    print("\nRunning comparison …")
    report = compare(our, ref, args.tolerance)
    print_summary(report, args.tolerance)

    PROCESSED.mkdir(exist_ok=True)
    out = PROCESSED / "bts_crosscheck_report.csv"
    report.drop(columns=["_ord"], errors="ignore").to_csv(out, index=False)
    print(f"Full report saved to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
