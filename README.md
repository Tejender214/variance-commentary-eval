# Evaluating LLM-Generated Financial Variance Commentary

**An evaluation methodology study.** How do you define, measure, and defend quality
for a generative system where there is no single right answer?

> Status: in progress. Started 17 Aug 2026. Target publication 13 Sep 2026.

---

## What this is

Financial variance commentary — the paragraph an FP&A analyst writes explaining *why*
line items moved — is a task where **quality is genuinely contestable**. Two competent
analysts can disagree about whether a given commentary is good. That makes it a useful
substrate for the actual question this repo is about: *what does it take to measure a
probabilistic system honestly?*

The measurement is the deliverable. The system is the substrate.

## Method

- **Frozen rubric.** Five binary dimensions, acceptance rule fixed before generation.
- **Blinded grading.** All conditions shuffled into one queue, condition labels stripped.
- **Two independent human labelers.** Inter-rater agreement reported as Cohen's κ, both
  before and after rubric revision.
- **Named baselines**, including a zero-LLM deterministic template — so every pass rate
  has something to be compared against.
- **Published failure taxonomy.** Every failing output categorized, with percentages.
- **Cost per *accepted* output** across two model tiers — not cost per call.

## Conditions

| ID | Input | Purpose |
|---|---|---|
| B0 | Numbers → template. Zero LLM. | The floor. What you get for free. |
| B1 | Numbers → LLM. No filing text. | What the model knows vs. what it's told. |
| B2 | Numbers + retrieved MD&A → LLM. | The main system. |

**B1 → B2 is the headline:** the quantified answer to "what did retrieval actually buy?"

## Pre-registration

`hypothesis.md` records predicted pass rates for every condition, committed before any
generation code was written. The git timestamp is the evidence of ordering.

## Data

SEC EDGAR — public XBRL company facts and MD&A prose from 10-Q/10-K filings. No
authentication, no scraping. All requests carry a descriptive User-Agent per SEC policy
and are cached locally; eval runs never touch the network.

## Repo layout

```
CONTEXT.md          standing project brief
hypothesis.md       pre-registered predictions (committed before any generation)
rubric.md           rubric + frozen acceptance rule + κ log
config/             sample definition
src/edgar.py        fetch + cache
src/variance.py     variance computation (also = B0's entire input)
src/mdna.py         MD&A location, extraction, chunking
src/systems.py      B0 / B1 / B2
src/labeling.py     blinded queue construction
src/kappa.py        Cohen's κ, per dimension and on the accept decision
report/             the eval report — the primary deliverable
data/labels/        anonymized labels (committed — they are the evidence)
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SEC_USER_AGENT="Your Name (your@email.com)"   # SEC blocks requests without this
python src/edgar.py                                   # smoke test
```

## Limitations

Reported in full in the eval report. Known in advance: modest sample size, a single
labeler pair, MD&A-as-reference carries management's framing bias, and sector coverage
is limited to three.

## Author

Tejender Reddy Kolla — MBA 2025–27, DoMS IIT Madras. Software/product engineering
background, moving into AI product management.

Second labeler: Manasa.
