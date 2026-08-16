# CONTEXT — standing project brief

Read this first. It is the full context needed to resume work in a fresh session.

---

## What this project is, in one paragraph

A program reads a US-listed company's public financial data and writes a paragraph
explaining *why* the material line items moved versus prior quarter and prior year —
the commentary an FP&A analyst writes for a CFO. **The program is not the deliverable.
The honest evaluation of it is the deliverable.** Frozen rubric, blinded grading, two
independent human labelers, named baselines, and a published failure taxonomy.

## Why it exists

A resume audit scored AI PM (the target role) at 53 — lowest of the technical PM
variants. Two causes:

1. "Retrieval-Augmented Generation" and "LLM evaluation" appear only in the skills
   bar. No bullet contains *retrieval*, *eval*, *labeled*, or *pass rate*. Claiming
   without evidencing is worse than omitting.
2. The only AI quality number on the resume is "90% accuracy on live SKUs" — no
   denominator, no baseline, no labeling protocol, no account of the failing 10%.

The 2026 AI PM hiring bar is roughly: run an eval in code, 50+ labeled examples, a
measured pass rate, a written failure analysis. This project is a purpose-built
answer to that bar.

## Framing risk — hold onto this

Finance is the **substrate**, not the subject. If a reader comes away thinking "he
built an FP&A tool," the project failed. Title, abstract, README, and section order
must all enforce: *this is about evaluation methodology.*

---

## The four systems

| ID | Input | Purpose |
|---|---|---|
| **B0** | Numbers → f-string template. **Zero LLM. No API call.** | The floor. What you get for free. |
| **B1** | Numbers → LLM. No filing text. | Isolates what the model *knows* vs. what it's *told*. |
| **B2** | Numbers + retrieved MD&A → LLM. | The main system (RAG). |
| **B3** *(optional)* | B2 + self-critique pass. | Cut first if time slips. |

**Deltas are the product.** B0→B1 = value of the LLM. **B1→B2 = value of retrieval.
That is the headline.**

If retrieval buys *less* than expected, that is a better interview story than a clean
win.

## Why the task is the right substrate

- **Quality is genuinely contestable.** Two competent analysts can disagree about
  whether a commentary is good. So the rubric has to do real work.
- **A reference exists but is not gold truth.** Companies publish MD&A — written with
  full internal information *and* an incentive to spin.
- **Retrieval is load-bearing, not decorative.** Numbers come from structured XBRL;
  drivers exist only in filing prose. Causes of a variance are effectively unbounded
  and cannot be inferred from the figures. That is *why* RAG is architecturally
  necessary here.

---

## The rubric (5 binary dimensions)

| Dimension | Fails when |
|---|---|
| Numerical accuracy | A stated number contradicts XBRL, or a direction is inverted |
| Materiality | Leads with an immaterial line while ignoring the largest mover |
| Driver attribution | Asserts a cause the source documents don't support |
| Non-fabrication | Contains a segment, product, or event absent from the filings |
| Specificity | Restatement, not analysis ("revenue rose due to higher sales") |

**Acceptance rule (FROZEN):** accepted only if Numerical accuracy AND Non-fabrication
both pass, plus ≥2 of the remaining 3. Changing this mid-run means re-labeling from
scratch and saying so in the report.

Binary, not Likert — kappa behaves better and two people converge faster.

## Labeling protocol

- **Blinded.** All conditions shuffled into one randomized queue, condition labels
  stripped. Non-negotiable.
- **Second labeler (Manasa — confirmed 16 Aug)** on 25–30 items. Compute **Cohen's κ**.
  >0.60 substantial, >0.80 near-perfect, <0.40 means the rubric is too vague.
- **A low κ is a finding, not a failure.** Report pre- and post-revision κ. "κ was
  0.41, I tightened the materiality criterion, κ rose to 0.73" is one of the most
  credible sentences available.
- **Never use an LLM as sole grader.** Acceptable as a *third* signal benchmarked
  against human labels.
- **Log labeling hours.** "110 examples, 9.5 hours, 2 labelers" proves work.
- **n = 100–120. Budget 8–12 hours.** Below 50 the project is noise. Cut B3 and the
  optional intervention before ever cutting n.

## Grading decision (settled)

**Rubric-primary. MD&A used only as the source corpus for the non-fabrication check.**

Reasoning: grading against MD&A as ground truth adopts management's framing as the
definition of correct. Companies spin. A commentary correctly identifying a driver
management downplayed would score as wrong. You'd be measuring "does it sound like
IR" rather than "is it accurate and grounded."

So: numerical accuracy checked against XBRL; non-fabrication checked against filing
text; materiality, attribution, specificity judged against the rubric by a human.

## Failure taxonomy (refine from observation — do not force)

- Fabricated driver (cause absent from all sources)
- Correct figure, inverted direction
- Arithmetic error in a derived metric (margin, growth rate)
- Immateriality (led with a trivial line item)
- Generic restatement (numerically correct, analytically empty)
- Stale context (prior-period driver attributed to current period)
- Over-attribution (single cause asserted for a multi-cause move)

## Cost and latency

Tokens in/out per commentary; **cost per *accepted* output** (not per call — a cheap
model that fails more often costs more per unit of usable work); p50 and p95 latency.
Two model tiers through B2, chosen on price-per-token spread not brand.

Target sentence: *"Model X at N× cost per call delivered only M points of pass rate
over model Y; at the volume an FP&A team runs this, Y is correct below a quality bar
of Z."* That is the most PM-shaped output of the project.

---

## Data

**SEC EDGAR.** Free, no auth, no scraping. Descriptive `User-Agent` with contact email
required on every request. Rate limit 10 req/sec. **Cache everything on first pull;
never hit the API during eval runs.**

| What | Endpoint |
|---|---|
| Structured facts | `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` |
| Single concept over time | `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/{Tag}.json` |
| Filing index | `https://data.sec.gov/submissions/CIK##########.json` |

CIK zero-padded to 10 digits. **Verify against
`https://www.sec.gov/search-filings/edgar-application-programming-interfaces` on day 1
— SEC has changed API surfaces before.**

### Sample

12–15 companies, 2–3 sectors, 6–8 consecutive quarters each → 100–120 company-quarters.

Sectors: enterprise software (deferred revenue, segment mix), retail (seasonality,
comps), industrials (input costs, backlog, FX). Different causal vocabularies stress
the rubric.

Selection criteria in priority order: clean consistent XBRL tagging; substantial MD&A
(boilerplate MD&A starves B2 and contaminates the headline delta); visible variance;
**2–3 deliberately boring quarters** (a system writing confident narrative about a
flat quarter is a failure mode worth capturing).

Exclude: banks and insurers (different statement structure), major restatements,
mid-period acquisitions large enough to break YoY comparability.

### Known XBRL traps

- Different companies use different tags for the same concept
- Restatements appear as duplicate facts for the same period
- Quarterly figures sometimes must be derived from year-to-date by subtraction
- **Hand-verify one company against its actual 10-Q on day 2**

---

## Out of scope (decided in advance)

| Excluded | Why |
|---|---|
| Fine-tuning | Weeks of time, zero marginal eval evidence. **No model training anywhere in this project.** |
| Agent framework (CrewAI, LangGraph) | Adds failure surface, no eval value. A CrewAI project already exists on the resume. |
| Polished UI / dashboard | The deliverable is a report. Streamlit is where this project goes to die. |
| >3 sectors | Labeling depth is the constraint, not sample breadth. |
| Real-time data / alerts | Product features, not evidence. |
| **Any Trimble data, tooling, or product name** | Hard confidentiality constraint. Public data only. |

Minimal UI permitted only in week 4, only if everything else is complete.

---

## Timeline (no slack)

**Week 1 — 17–23 Aug:** verify EDGAR; pull and cache; variance computation; MD&A
extraction and chunking; rubric v0; **20-item pilot label + κ on 22 Aug** (highest-
leverage day in the schedule).

**Week 2 — 24–30 Aug:** implement B0/B1/B2; generate all outputs; **full blinded run,
n=100–120**; second labeler on 25–30; final κ.

**Week 3 — 31 Aug–6 Sep:** pass rates per system per dimension; failure taxonomy;
cost/latency across two model tiers; one targeted intervention measured (chunk
granularity is the leading candidate).

**Week 4 — 7–13 Sep:** report (6–10pp), repo cleanup, publish, resume bullets,
rehearse 10-min walkthrough.

If week 2 slips: cut B3, cut the optional intervention. **Never cut n.**

---

## Deliverables

1. **Eval report (primary), public.** Structure: problem → why quality is hard to
   define here → rubric → labeling protocol and κ → baselines → results → failure
   taxonomy → cost/quality trade-off and the decision made → **limitations
   (mandatory)** → what I'd do next.
2. **Repo.** Harness, rubric, anonymized labels, reproduction instructions. README
   leads with methodology, not pipeline.
3. **Three resume bullets**, 102–110 characters of text each (DoMS template band).
4. **A rehearsed 10-minute walkthrough.** Assume a hostile former engineer.

## Interview defense — design so these are clean

- *Where did labels come from?* → Two human labelers, blinded, κ = X.
- *Before or after seeing output?* → Rubric and acceptance rule frozen before
  generation; grading blinded. **Contamination here is fatal.**
- *Baseline?* → Three named, including a zero-LLM template.
- *What's your n?* → n = X, with the claims it does and doesn't support.
- *What broke?* → Failure taxonomy, by percentage.
- *What did you cut?* → Scope table, with reasons.
- *What would you do differently?* → Specific, not "more data."

## Success criteria

- [ ] n ≥ 100 labeled, blinded, logged protocol
- [ ] κ computed and reported, pre/post rubric revision
- [ ] ≥3 named baselines on the same sample
- [ ] Failure taxonomy, ≥4 named categories, percentages
- [ ] Cost per accepted output across ≥2 model tiers
- [ ] One decision documented with the data that decided it and the alternative rejected
- [ ] Report published and linked from the resume
- [ ] RAG and LLM evaluation restorable to the skills line with a bullet behind each

**Fails regardless of system quality if:** n < 50, no baseline, or the artifact reads
as a product demo rather than an evaluation.

---

## Open decisions status

| # | Decision | Status |
|---|---|---|
| 1 | Reference-based vs rubric-only grading | **Settled** — rubric-primary |
| 2 | Labeler #2 | **Settled** — Manasa, confirmed 16 Aug |
| 3 | Companies and sectors | OPEN — fix before any pulling |
| 4 | Two model tiers | OPEN — pick on price spread, verify current pricing |
| 5 | Show output to a real FP&A analyst? | OPEN — cheap, high leverage, easy to skip |
