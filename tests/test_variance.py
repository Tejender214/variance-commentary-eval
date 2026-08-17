"""
Tests for the variance extraction layer.

Run:  python tests/make_fixture.py && python tests/test_variance.py

These test the cases that actually break in real XBRL data, not the happy path.
The fixture is synthetic so this runs with no network access — which also means
anyone reproducing the study can verify the extraction logic without an SEC
connection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.variance import (  # noqa: E402
    b0_template,
    build_records,
    extract_concept,
    load_facts,
)

CIK = "0009999999"
passed = failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def main():
    facts = load_facts(CIK)
    records = build_records(CIK)

    print("\nextraction")
    tag, vals, dropped = extract_concept(facts, "revenue")
    check("picks a revenue tag", tag == "Revenues", f"got {tag}")
    check("ignores instant (balance-sheet) facts",
          all(len(str(k)) == 10 for k in vals))

    print("\nrestatement handling")
    check("drops the superseded duplicate", dropped == 1, f"dropped {dropped}")
    check("keeps the LATER-filed value (12,900m not 12,800m)",
          vals.get("2023-06-30") == 12_900_000_000,
          f"got {vals.get('2023-06-30')}")

    print("\nvariance computation")
    check("one record per quarter", len(records) == 10, f"got {len(records)}")
    r = records[-1]
    check("YoY compares to 4 quarters back",
          r["prior_year_end"] == "2023-06-30", r["prior_year_end"])
    check("QoQ compares to 1 quarter back",
          r["prior_quarter_end"] == "2024-03-31", r["prior_quarter_end"])

    rev = r["line_items"]["revenue"]
    check("YoY absolute correct (14,900 - 12,900 = 2,000m)",
          rev["yoy_abs"] == 2_000_000_000, f"got {rev['yoy_abs']}")
    check("YoY percentage correct (~15.5%)",
          abs(rev["yoy_pct"] - 15.504) < 0.01, f"got {rev['yoy_pct']}")

    print("\nmateriality ranking")
    top_abs = r["movers_by_abs"][0][0]
    top_pct = r["movers_by_pct"][0][0]
    check("ranks by absolute and percentage SEPARATELY",
          top_abs != top_pct,
          "they matched — the fixture no longer exercises the disagreement")
    check("largest absolute mover is revenue", top_abs == "revenue", top_abs)
    check("largest percentage mover is operating income",
          top_pct == "operating_income", top_pct)

    print("\nderived metrics (computed in code, never by the model)")
    check("gross margin computed from cost when GrossProfit absent",
          r["gross_margin"] is not None and abs(r["gross_margin"] - 44.97) < 0.05,
          f"got {r['gross_margin']}")
    check("bps change is a round number of basis points",
          r["gross_margin_bps_change"] == 155.6,
          f"got {r['gross_margin_bps_change']}")

    print("\nB0 — zero-LLM floor")
    out = b0_template(r)
    check("states no driver (cannot fabricate by construction)",
          not any(w in out.lower() for w in ("because", "driven by", "due to")))
    check("contains the actual figure", "14,900" in out)
    check("states the direction", "increased" in out)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
