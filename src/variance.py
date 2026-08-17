"""
Variance extraction and computation from cached SEC XBRL companyfacts.

Turns a companyfacts JSON blob into a clean structured record per
company-quarter. That record is:
  - the ONLY input to B0 (deterministic template)
  - the numeric half of the input to B1 and B2

DESIGN DECISION, deliberate and worth defending in interview:
All derived metrics (margins, bps changes, growth rates) are computed HERE,
in code, deterministically. The model is never asked to do arithmetic.
"Arithmetic error in a derived metric" is a named category in the failure
taxonomy, and it can be eliminated architecturally rather than measured.

XBRL REALITIES THIS MODULE HANDLES (each one bit me in testing):
  1. Companies use different tags for the same economic concept. Microsoft
     reports revenue under RevenueFromContractWithCustomerExcludingAssessedTax;
     others use Revenues or SalesRevenueNet. Handled via CONCEPTS below:
     an ordered list of candidate tags per concept, first hit wins.
  2. Restatements appear as DUPLICATE facts for the same period from a later
     accession number. Dedup rule: keep the fact with the latest `filed` date,
     and log how many duplicates were dropped.
  3. Some companies only file year-to-date figures. Q2 must then be derived as
     (6-month YTD - Q1). Handled by derive_quarters_from_ytd().
  4. Q4 is NEVER filed as a standalone quarter — the 10-K reports the full year.
     Q4 = FY - (9-month YTD). Same function handles it.
  5. Duration facts have start+end; instant facts (balance sheet) have end only.
     We only want duration facts of ~one quarter for the income statement.
"""

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# ---------------------------------------------------------------------------
# Concept -> candidate us-gaap tags, in priority order. First tag with usable
# data wins. Extend this as you hit companies that use something else; log
# every extension, because "which tag did you use for revenue" is a fair
# interview question and the honest answer is "it varied, here's the mapping".
# ---------------------------------------------------------------------------
CONCEPTS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
    ],
    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSold",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_expenses": ["OperatingExpenses", "CostsAndExpenses"],
    "rd_expense": ["ResearchAndDevelopmentExpense"],
    "sga_expense": [
        "SellingGeneralAndAdministrativeExpense",
        "GeneralAndAdministrativeExpense",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
}

# A duration fact counts as "one quarter" if its span falls in this window.
QUARTER_DAYS = (80, 100)
YTD_WINDOWS = {
    "H1": (170, 195),
    "9M": (260, 290),
    "FY": (350, 380),
}


# ---------------------------------------------------------------------------
# Loading and fact extraction
# ---------------------------------------------------------------------------
def load_facts(cik) -> dict:
    """Read a cached companyfacts JSON. Never hits the network."""
    c = str(cik).strip().lstrip("CIK").zfill(10)
    path = RAW_DIR / f"companyfacts_{c}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not cached. Run src/edgar.py to pull it first — "
            "eval runs must never hit the SEC API."
        )
    return json.loads(path.read_text())


def _days(fact: dict) -> int | None:
    """Span of a duration fact in days. None for instant facts."""
    if "start" not in fact or "end" not in fact:
        return None
    s = date.fromisoformat(fact["start"])
    e = date.fromisoformat(fact["end"])
    return (e - s).days


def _dedup(facts: list) -> tuple[list, int]:
    """
    Restatements produce duplicate facts for the same (start, end) from a later
    accession. Keep the one with the latest `filed` date.

    Returns (deduped facts, count dropped). The count goes in the report —
    silently dropping data is exactly the kind of thing you should be able to
    quantify when asked.
    """
    by_period = defaultdict(list)
    for f in facts:
        by_period[(f.get("start"), f["end"])].append(f)

    kept, dropped = [], 0
    for group in by_period.values():
        group.sort(key=lambda f: f.get("filed", ""))
        kept.append(group[-1])
        dropped += len(group) - 1
    kept.sort(key=lambda f: f["end"])
    return kept, dropped


def extract_concept(facts_json: dict, concept: str) -> tuple[str | None, dict, int]:
    """
    Pull one economic concept as {period_end: value} of quarterly duration facts.

    Returns (tag_used, {end_date: value}, duplicates_dropped).
    tag_used is None if no candidate tag had usable quarterly data.
    """
    us_gaap = facts_json.get("facts", {}).get("us-gaap", {})

    for tag in CONCEPTS[concept]:
        if tag not in us_gaap:
            continue
        usd = us_gaap[tag].get("units", {}).get("USD", [])
        quarterly = [
            f for f in usd
            if (d := _days(f)) is not None and QUARTER_DAYS[0] <= d <= QUARTER_DAYS[1]
        ]
        if not quarterly:
            continue
        deduped, dropped = _dedup(quarterly)
        return tag, {f["end"]: f["val"] for f in deduped}, dropped

    return None, {}, 0


def derive_quarters_from_ytd(facts_json: dict, concept: str) -> dict:
    """
    Some filers report only year-to-date. Derive discrete quarters by
    subtraction: Q2 = H1 - Q1, Q3 = 9M - H1, Q4 = FY - 9M.

    Q4 ALWAYS needs this — a 10-K reports the full year, never Q4 alone. If you
    skip this you will silently have no Q4 anywhere in your sample, which would
    be a hole in the dataset that a reader could find and you couldn't explain.

    Returns {end_date: derived_value}. Documented as a limitation: derived
    quarters inherit rounding from two reported figures.
    """
    us_gaap = facts_json.get("facts", {}).get("us-gaap", {})
    derived = {}

    for tag in CONCEPTS[concept]:
        if tag not in us_gaap:
            continue
        usd = us_gaap[tag].get("units", {}).get("USD", [])

        # bucket every duration fact by fiscal year and cumulative window
        buckets = defaultdict(dict)
        for f in usd:
            d = _days(f)
            if d is None or "start" not in f:
                continue
            fy = f.get("fy")
            if fy is None:
                continue
            if QUARTER_DAYS[0] <= d <= QUARTER_DAYS[1]:
                buckets[fy].setdefault("Q", []).append(f)
            else:
                for name, (lo, hi) in YTD_WINDOWS.items():
                    if lo <= d <= hi:
                        buckets[fy][name] = f

        for fy, b in buckets.items():
            quarters = sorted(b.get("Q", []), key=lambda f: f["end"])
            # Q4 = FY - 9M
            if "FY" in b and "9M" in b:
                derived[b["FY"]["end"]] = b["FY"]["val"] - b["9M"]["val"]
            # Q3 = 9M - H1
            if "9M" in b and "H1" in b and not any(
                q["end"] == b["9M"]["end"] for q in quarters
            ):
                derived[b["9M"]["end"]] = b["9M"]["val"] - b["H1"]["val"]
            # Q2 = H1 - Q1
            if "H1" in b and quarters:
                q1 = quarters[0]
                if q1["end"] != b["H1"]["end"]:
                    derived[b["H1"]["end"]] = b["H1"]["val"] - q1["val"]
        if derived:
            break

    return derived


# ---------------------------------------------------------------------------
# Variance computation
# ---------------------------------------------------------------------------
def _pct(curr, prior):
    if prior in (None, 0):
        return None
    return (curr - prior) / abs(prior) * 100


def _prior_quarter_end(ends: list, i: int) -> str | None:
    return ends[i - 1] if i >= 1 else None


def _prior_year_end(ends: list, i: int) -> str | None:
    """Same quarter, prior year — four quarters back in a consecutive series."""
    return ends[i - 4] if i >= 4 else None


def build_records(cik, include_derived: bool = True) -> list:
    """
    One structured record per company-quarter.

    Each record contains:
      company, cik, period_end
      line_items: {concept: {value, qoq_abs, qoq_pct, yoy_abs, yoy_pct}}
      movers_by_abs / movers_by_pct: concepts ranked by YoY move
      gross_margin, gross_margin_bps_change
      operating_margin, operating_margin_bps_change
      provenance: which tag was used per concept, duplicates dropped

    movers_by_abs and movers_by_pct are ranked SEPARATELY and on purpose. They
    disagree — a small line that doubled vs a huge line that moved 3% — and that
    disagreement is precisely what materiality judgments turn on. Collapsing
    them into one ranking would hide the thing the rubric is testing.
    """
    facts_json = load_facts(cik)
    company = facts_json.get("entityName", "UNKNOWN")

    series, provenance = {}, {}
    for concept in CONCEPTS:
        tag, vals, dropped = extract_concept(facts_json, concept)
        if include_derived:
            for end, v in derive_quarters_from_ytd(facts_json, concept).items():
                vals.setdefault(end, v)
        if vals:
            series[concept] = vals
            provenance[concept] = {"tag_used": tag, "duplicates_dropped": dropped}

    if "revenue" not in series:
        raise ValueError(
            f"No revenue series found for {company}. Add its tag to "
            f"CONCEPTS['revenue'] and log the addition."
        )

    ends = sorted(series["revenue"])
    records = []

    for i, end in enumerate(ends):
        pq = _prior_quarter_end(ends, i)
        py = _prior_year_end(ends, i)

        line_items = {}
        for concept, vals in series.items():
            if end not in vals:
                continue
            curr = vals[end]
            prior_q = vals.get(pq) if pq else None
            prior_y = vals.get(py) if py else None
            line_items[concept] = {
                "value": curr,
                "qoq_abs": (curr - prior_q) if prior_q is not None else None,
                "qoq_pct": _pct(curr, prior_q) if prior_q is not None else None,
                "yoy_abs": (curr - prior_y) if prior_y is not None else None,
                "yoy_pct": _pct(curr, prior_y) if prior_y is not None else None,
            }

        by_abs = sorted(
            [(c, v["yoy_abs"]) for c, v in line_items.items() if v["yoy_abs"] is not None],
            key=lambda t: abs(t[1]),
            reverse=True,
        )
        by_pct = sorted(
            [(c, v["yoy_pct"]) for c, v in line_items.items() if v["yoy_pct"] is not None],
            key=lambda t: abs(t[1]),
            reverse=True,
        )

        rec = {
            "company": company,
            "cik": str(cik).zfill(10),
            "period_end": end,
            "prior_quarter_end": pq,
            "prior_year_end": py,
            "line_items": line_items,
            "movers_by_abs": by_abs,
            "movers_by_pct": by_pct,
            "provenance": provenance,
        }
        rec.update(_margins(series, end, py))
        records.append(rec)

    return records


def _margins(series: dict, end: str, prior_year_end: str | None) -> dict:
    """Margins and bps changes — computed in code, never by the model."""
    out = {
        "gross_margin": None,
        "gross_margin_bps_change": None,
        "operating_margin": None,
        "operating_margin_bps_change": None,
    }
    rev = series.get("revenue", {}).get(end)
    if not rev:
        return out

    def margin(numerator_concept, period):
        n = series.get(numerator_concept, {}).get(period)
        r = series.get("revenue", {}).get(period)
        if n is None or not r:
            return None
        return n / r * 100

    gm = margin("gross_profit", end)
    if gm is None and series.get("cost_of_revenue", {}).get(end) is not None:
        gm = (rev - series["cost_of_revenue"][end]) / rev * 100
    out["gross_margin"] = gm

    om = margin("operating_income", end)
    out["operating_margin"] = om

    if prior_year_end:
        gm_prior = margin("gross_profit", prior_year_end)
        if gm_prior is None:
            cr = series.get("cost_of_revenue", {}).get(prior_year_end)
            rp = series.get("revenue", {}).get(prior_year_end)
            gm_prior = (rp - cr) / rp * 100 if cr is not None and rp else None
        if gm is not None and gm_prior is not None:
            out["gross_margin_bps_change"] = round((gm - gm_prior) * 100, 1)

        om_prior = margin("operating_income", prior_year_end)
        if om is not None and om_prior is not None:
            out["operating_margin_bps_change"] = round((om - om_prior) * 100, 1)

    return out


# ---------------------------------------------------------------------------
# B0 — the zero-LLM floor. No API call anywhere in this function.
# ---------------------------------------------------------------------------
def b0_template(record: dict, top_n: int = 3) -> str:
    """
    Deterministic template. THERE IS NO MODEL HERE.

    Passes numerical accuracy and non-fabrication BY CONSTRUCTION — it cannot
    invent, and its arithmetic is the same arithmetic the grader checks against.
    Whether it clears the acceptance gate depends entirely on whether the
    materiality ranking above is good enough.

    This is the floor. If it scores high, the honest headline of the report
    changes: most of the acceptance rate is available with no LLM at all.
    """
    parts = []
    for concept, delta in record["movers_by_abs"][:top_n]:
        li = record["line_items"][concept]
        direction = "increased" if delta > 0 else "decreased"
        pct = li["yoy_pct"]
        label = concept.replace("_", " ").capitalize()
        parts.append(
            f"{label} {direction} {abs(pct):.1f}% year-over-year to "
            f"${li['value']/1e6:,.0f}m."
            if pct is not None
            else f"{label} was ${li['value']/1e6:,.0f}m."
        )

    if record.get("gross_margin") is not None:
        gm = f"Gross margin was {record['gross_margin']:.1f}%"
        bps = record.get("gross_margin_bps_change")
        if bps is not None:
            move = "expanded" if bps > 0 else "compressed"
            gm += f", having {move} {abs(bps):.0f}bps year-over-year"
        parts.append(gm + ".")

    return " ".join(parts)


if __name__ == "__main__":
    import sys

    cik = sys.argv[1] if len(sys.argv) > 1 else "0000789019"
    records = build_records(cik)
    print(f"{records[0]['company']}: {len(records)} company-quarters\n")

    r = records[-1]
    print(f"--- {r['period_end']} ---")
    print("top movers by absolute YoY:")
    for c, d in r["movers_by_abs"][:4]:
        print(f"   {c:<20} {d/1e6:>12,.0f}m")
    print("top movers by percentage YoY:")
    for c, d in r["movers_by_pct"][:4]:
        print(f"   {c:<20} {d:>11.1f}%")
    print(f"\ngross margin: {r['gross_margin']}")
    print(f"gm bps change: {r['gross_margin_bps_change']}")
    print(f"\nB0 output:\n{b0_template(r)}")
    print("\nprovenance:")
    for c, p in r["provenance"].items():
        print(f"   {c:<20} {p['tag_used']}  (dropped {p['duplicates_dropped']} dupes)")
