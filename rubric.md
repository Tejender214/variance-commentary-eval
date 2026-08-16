# Rubric v0 — DRAFT

**Status:** v0, drafted 16 Aug 2026. **Must be tightened and frozen by 21 Aug**, then
sent to labeler #2 to read cold before the 22 Aug pilot.

**Test to apply to every criterion below:** *could two reasonable people read this and
disagree?* If yes, it is not specific enough yet. "Did it surface what matters?" fails
this test. "Both the largest absolute mover and the largest percentage mover are
addressed" passes it.

---

## Acceptance rule (FROZEN — do not change after generation begins)

An output is **ACCEPTED** only if:

- **Numerical accuracy = PASS**, AND
- **Non-fabrication = PASS**, AND
- at least **2 of 3** of {Materiality, Driver attribution, Specificity} = PASS

Frozen 16 Aug 2026. Changing this mid-run requires re-labeling from scratch and
disclosing it in the report.

---

## The five dimensions — score 0 or 1 only

### 1. Numerical accuracy

**Question:** Are the figures, percentages, and directions correct?

**FAIL if any of:**
- A stated figure contradicts the cached XBRL fact for that company-period
- A direction is inverted (says "increased" where the data shows a decrease)
- A derived metric (margin %, bps change, growth rate) is arithmetically wrong
- A figure is stated for the wrong period

**Tolerance:** figures rounded consistently with the source are a PASS.
*TODO before freeze: state the exact rounding tolerance, e.g. ±0.1pp on percentages.*

---

### 2. Materiality

**Question:** Did it surface the variances that actually matter?

**FAIL if:**
- *TODO — this is the vaguest criterion and the most likely to tank κ. Tighten to
  something testable, e.g.: "FAIL if the largest absolute mover is not addressed, OR
  if the output leads with a line item outside the top 3 by absolute move."*

---

### 3. Driver attribution

**Question:** Is each stated cause supported by the source documents?

**FAIL if:**
- A stated cause does not appear in the filing text for that company-period
- A cause is attached to the wrong line item
- A prior-period driver is attributed to the current period (stale context)

**Note:** this differs from Non-fabrication. Attribution is about *linking* a real
cause to the right movement. Fabrication is about *inventing* an entity or event.

---

### 4. Non-fabrication

**Question:** Is every claim traceable to a source?

**FAIL if:**
- Names a segment, product, customer, or event that does not appear in the filings
- States a driver that is true in the world but not present in any source document
  (**decided:** "true but untraceable" = FAIL, since traceability is what is being
  measured; note this is a defensible call an interviewer may probe)

---

### 5. Specificity

**Question:** Would an analyst act on this, or is it restatement?

**FAIL if:**
- Restates the movement without adding information ("revenue increased due to higher
  sales")
- Uses only unfalsifiable generic causes ("macroeconomic conditions", "favourable
  mix") with no specific referent
- *TODO: decide whether hedged vagueness gets its own failure category in the
  taxonomy — hypothesis.md flags this as the most likely way H1 is wrong.*

---

## Labeling instructions for both labelers

1. You will not know which system produced any output. Do not try to guess.
2. Score all five dimensions 0/1 before moving to the next item.
3. Do not message the other labeler during a session. Disagreement is the signal being
   measured — contaminating it destroys κ.
4. If a criterion feels unapplicable, flag the item rather than guessing. Flagged items
   are discussed *after* the session, and the rubric fix applies to the next round.
5. Log your start and end time for each session.

## κ log

| Date | Round | n | κ | Rubric version | Note |
|---|---|---|---|---|---|
| 22 Aug | Pilot | 20 | | v0 | |
| | Re-pilot (if needed) | 10 | | v1 | |
| 28–30 Aug | Main | 25–30 | | frozen | |
