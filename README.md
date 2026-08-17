# Evaluating LLM-Generated Financial Variance Commentary

**An evaluation methodology study.** How do you define, measure, and defend quality for
a generative system where there is no single right answer?

> **Status: design complete, extraction layer implemented and tested. Full results due
> 13 Sep 2026.**
> Predicted pass rates for every condition were pre-registered in
> [`hypothesis.md`](hypothesis.md) and committed **before any generation code existed** —
> see the first commit in `git log`. That ordering is the point: it means the acceptance
> criteria could not be fitted to the results after the fact.

---

## What this is

Financial variance commentary — the paragraph an FP&A analyst writes explaining *why*
line items moved — is a task where **quality is genuinely contestable**. Two competent
analysts can disagree about whether a given commentary is good. That makes it a useful
substrate for the actual question this repo is about: *what does it take to measure a
probabilistic system honestly?*

The measurement is the deliverable. The system is the substrate.

## Method

- **Frozen rubric.** Five binary dimensions; acceptance rule fixed before generation.
- **Blinded grading.** All conditions shuffled into one queue, condition labels stripped.
- **Two independent human labelers.** Inter-rater agreement reported as Cohen's κ, both
  before and after rubric revision.
- **Named baselines**, including a zero-LLM deterministic template — so every pass rate
  has something to be compared against.
- **Published failure taxonomy.** Every failing output categorised, with percentages.
- **Cost per *accepted* output** across two model tiers — not cost per call. A cheaper
  model that fails more often costs more per unit of usable work.
- **p50 and p95 latency**, not the mean. The mean hides the tail, and the tail is what
  makes a tool feel unusable during a close cycle.

## Conditions

| ID | Input | Purpose |
|---|---|---|
| B0 | Numbers → template. **Zero LLM.** | The floor. What you get for free. |
| B1 | Numbers → LLM. No filing text. | What the model *knows* vs. what it's *told*. |
| B2 | Numbers + retrieved MD&A → LLM. | The main system. |

**B1 → B2 is the headline:** the quantified answer to "what did retrieval actually buy?"

Why retrieval is architecturally necessary rather than decorative: the *numbers* come
from structured XBRL, but the *reasons* a line item moved exist only in filing prose. The
causes of a variance are effectively unbounded and cannot be inferred from the figures —
so a system without retrieval must either fabricate a driver or hedge into vagueness.
Distinguishing those two failure modes is one of the things this study measures.

## What is implemented

| Module | Status |
|---|---|
| `src/edgar.py` | Fetch + cache from SEC EDGAR. Working. |
| `src/variance.py` | Extraction, variance computation, B0 template. Working, 17 tests. |
| `src/kappa.py` | Cohen's κ per dimension and on the accept decision. Working. |
| `src/labeling.py` | Blinded queue construction. Working. |
| `src/mdna.py` | MD&A location, extraction, chunking. In progress. |
| `src/systems.py` | B1 / B2 generation. In progress. |

## Real XBRL problems the extraction layer handles

Each of these silently corrupts a dataset if ignored:

1. **Tag heterogeneity.** Companies report the same economic concept under different
   us-gaap tags. Handled by an ordered candidate list per concept, with the tag actually
   used recorded in each record's provenance.
2. **Restatements as duplicate facts.** The same period appears more than once from
   different accession numbers. Resolved by keeping the latest-filed value, and the
   number of superseded facts dropped is counted rather than silently discarded.
3. **Year-to-date-only filers.** Discrete quarters derived by subtraction.
4. **Q4 never exists as a standalone filing.** A 10-K reports the full year, so Q4 must
   be derived as FY − 9M. Skipping this leaves a hole in the dataset.
5. **Instant vs duration facts.** Balance-sheet facts have no start date and must be
   excluded from income-statement variance.

Derived metrics — margins, basis-point changes, growth rates — are computed
**deterministically in code, never by the model.** "Arithmetic error in a derived metric"
is a named failure category, and it can be eliminated architecturally rather than
measured.

## Tests

```bash
python tests/make_fixture.py    # synthetic companyfacts, no network needed
python tests/test_variance.py   # 17 assertions
python src/kappa.py             # κ demo on synthetic labels
```

The fixture deliberately contains a restatement, a year-to-date-only concept, and an
instant fact, so the messy paths are exercised rather than assumed.

## Data

SEC EDGAR — public XBRL company facts and MD&A prose from 10-Q/10-K filings. No
authentication, no scraping. Requests carry a descriptive User-Agent per SEC policy and
are cached locally; **eval runs never touch the network**, so results are reproducible
and immune to rate limits or API changes mid-study.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo 'SEC_USER_AGENT="Your Name (your@email.com)"' > .env   # SEC requires a contact
python src/edgar.py                                          # smoke test
```

## Repo layout

```
CONTEXT.md          standing project brief
hypothesis.md       pre-registered predictions (committed before any generation)
rubric.md           rubric, frozen acceptance rule, κ log
config/             sample definition
src/                extraction, generation, labeling, statistics
tests/              synthetic fixture + assertions
report/             the eval report — the primary deliverable
data/labels/        anonymised labels (committed — they are the evidence)
```

## Limitations

Reported in full in the eval report. Known in advance: modest sample size, a single
labeler pair, MD&A-as-reference carries management's framing bias, sector coverage
limited to three, and derived quarters inherit rounding from two reported figures.

## Author

Tejender Reddy Kolla — MBA 2025–27, DoMS IIT Madras. Software and product engineering
background, moving into AI product management.

Second labeler: Manasa.
