"""
Variance computation. Days 18-19 Aug.

Turns cached XBRL facts into a clean structured record per company-quarter.
This record is the ONLY input to B0, and the numeric input to B1 and B2.

CRITICAL: all derived metrics (margin %, bps change, growth rate) are computed
HERE, deterministically, in code. Never let the model do this arithmetic —
"arithmetic error in a derived metric" is a named failure category and you can
eliminate it architecturally.

XBRL traps to expect (hand-verify one company against its 10-Q on day 2):
  - different companies use different tags for the same concept
  - restatements appear as duplicate facts for the same period
  - quarterly figures sometimes must be derived from year-to-date by subtraction
"""


def extract_line_items(facts: dict, cik: str) -> list:
    """
    TODO: pull the material line items per period from cached companyfacts JSON.
    Handle duplicate facts (restatements) — decide a rule and document it.
    Returns: list of {period, tag, label, value, unit, form, filed}
    """
    raise NotImplementedError


def compute_variance(line_items: list) -> list:
    """
    TODO: for each company-quarter compute QoQ and YoY, absolute and percentage.

    Rank by absolute move AND by percentage move SEPARATELY — they disagree
    (a small line that doubled vs a huge line that moved 3%), and that
    disagreement is exactly what materiality judgments turn on.

    Returns: list of {company, period, movers_by_abs, movers_by_pct,
                      gross_margin, gross_margin_bps_change,
                      operating_margin, operating_margin_bps_change}
    """
    raise NotImplementedError
