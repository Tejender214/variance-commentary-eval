"""
Synthetic companyfacts fixture. Lets you test extraction logic without hitting
the SEC API — and lets anyone reproduce the tests without network access.

Deliberately includes the messy cases:
  - a restatement (duplicate fact for one period, two accession numbers)
  - year-to-date-only reporting for one concept, forcing derivation
  - an instant (balance sheet) fact that must be ignored
"""
import json
from datetime import date, timedelta
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

def q_ends(start_year=2022, n=10):
    out, d = [], date(start_year, 3, 31)
    for _ in range(n):
        out.append(d)
        m = d.month + 3
        y = d.year + (m > 12)
        m = m - 12 if m > 12 else m
        d = date(y, m, [31,30,30,31,31,30,30,31][ (m//3-1)%8 ] if False else 30 if m in (6,9) else 31)
    return out

ENDS = [date(2022,3,31), date(2022,6,30), date(2022,9,30), date(2022,12,31),
        date(2023,3,31), date(2023,6,30), date(2023,9,30), date(2023,12,31),
        date(2024,3,31), date(2024,6,30)]

def dur(end, val, fy, fp, accn, filed, days=91):
    return {"start": str(end - timedelta(days=days)), "end": str(end), "val": val,
            "accn": accn, "fy": fy, "fp": fp, "form": "10-Q", "filed": filed}

rev_vals  = [10_000, 11_000, 10_500, 13_000, 11_500, 12_800, 12_200, 15_100, 13_400, 14_900]
cost_vals = [ 6_000,  6_500,  6_400,  7_600,  6_700,  7_300,  7_400,  8_600,  7_500,  8_200]
opinc_vals= [ 2_000,  2_300,  1_900,  3_100,  2_400,  2_800,  2_100,  3_600,  2_900,  3_300]

def series(vals, tag_days=91):
    out = []
    for i, e in enumerate(ENDS):
        fy = e.year
        fp = f"Q{((e.month-1)//3)+1}"
        out.append(dur(e, vals[i]*1_000_000, fy, fp, f"acc-{i}", str(e + timedelta(days=25)), tag_days))
    return out

revenue = series(rev_vals)
# RESTATEMENT: 2023-06-30 revenue refiled later with a different value.
revenue.append(dur(ENDS[5], 12_900*1_000_000, 2023, "Q2", "acc-restated",
                   "2024-02-01", 91))

facts = {
    "cik": 9999999,
    "entityName": "SYNTHETIC TEST CORP",
    "facts": {
        "us-gaap": {
            "Revenues": {"units": {"USD": revenue}},
            "CostOfRevenue": {"units": {"USD": series(cost_vals)}},
            "OperatingIncomeLoss": {"units": {"USD": series(opinc_vals)}},
            # instant fact that must be ignored (no start key)
            "Assets": {"units": {"USD": [
                {"end": "2024-06-30", "val": 500_000_000_000, "fy": 2024,
                 "fp": "Q2", "form": "10-Q", "filed": "2024-07-25"}]}},
        }
    },
}

path = RAW / "companyfacts_0009999999.json"
path.write_text(json.dumps(facts))
print(f"wrote {path}")
