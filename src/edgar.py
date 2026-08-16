"""
SEC EDGAR fetch + cache.

Rules baked in here on purpose:
  - Descriptive User-Agent with contact email on EVERY request (SEC policy;
    requests without it get blocked).
  - Rate limit <= 10 req/sec. We are deliberately slower.
  - Cache to disk on first pull. NOTHING downstream may hit the network.
    If an eval run depends on a live API call, a rate limit or outage in week 3
    kills reproducibility.

VERIFY THE ENDPOINTS BEFORE TRUSTING THIS FILE:
  https://www.sec.gov/search-filings/edgar-application-programming-interfaces
SEC has changed API surfaces before. This module is written from the documented
shape as of the project brief and has NOT been tested against the live API.
"""

import json
import os
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# CONFIG — set your real email here or in a .env file. SEC blocks requests
# without a contact address.
# ---------------------------------------------------------------------------
USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "Tejender Reddy Kolla (ms25a072@smail.iitm.ac.in)",  # <-- REPLACE
)

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MIN_INTERVAL = 0.15  # seconds between requests (~6.7 req/s, under the 10/s cap)
_last_request = 0.0


def _throttle():
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_request = time.time()


def pad_cik(cik) -> str:
    """SEC wants CIK zero-padded to 10 digits."""
    return str(cik).strip().lstrip("CIK").zfill(10)


def _get(url: str) -> dict:
    _throttle()
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _cached(name: str, url: str, force: bool = False) -> dict:
    """Fetch once, then always read from disk."""
    path = CACHE_DIR / f"{name}.json"
    if path.exists() and not force:
        return json.loads(path.read_text())
    data = _get(url)
    path.write_text(json.dumps(data))
    print(f"cached -> {path}")
    return data


def company_facts(cik, force: bool = False) -> dict:
    """Every reported XBRL fact, all periods, for one company."""
    c = pad_cik(cik)
    return _cached(
        f"companyfacts_{c}",
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c}.json",
        force,
    )


def submissions(cik, force: bool = False) -> dict:
    """Filing index — accession numbers needed to locate the actual 10-Q/10-K."""
    c = pad_cik(cik)
    return _cached(
        f"submissions_{c}",
        f"https://data.sec.gov/submissions/CIK{c}.json",
        force,
    )


def company_concept(cik, tag: str, taxonomy: str = "us-gaap", force: bool = False) -> dict:
    """One concept across time — useful for building a single line-item series."""
    c = pad_cik(cik)
    return _cached(
        f"concept_{c}_{taxonomy}_{tag}",
        f"https://data.sec.gov/api/xbrl/companyconcept/CIK{c}/{taxonomy}/{tag}.json",
        force,
    )


if __name__ == "__main__":
    # Day-1 smoke test. Microsoft = CIK 0000789019.
    # If this returns an entityName, the endpoint shape is still correct.
    facts = company_facts("0000789019")
    print("entityName:", facts.get("entityName"))
    print("taxonomies:", list(facts.get("facts", {}).keys()))
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    print("n us-gaap tags:", len(us_gaap))
    print("sample tags:", list(us_gaap)[:10])
