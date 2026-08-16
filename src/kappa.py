"""
Cohen's kappa — inter-rater agreement.

Measures how much two labelers agree BEYOND what chance would produce. If you
both mark 90% of items PASS, you agree 81% of the time by luck alone; kappa
strips that out.

Reading:  >0.80 near-perfect | >0.60 substantial | 0.40-0.60 moderate
          <0.40 the rubric is too vague for two people to apply consistently

A low kappa is a FINDING, not a failure. Report it, fix the rubric, re-label,
report both numbers. "kappa was 0.41, I tightened the materiality criterion,
kappa rose to 0.73" is one of the most credible sentences in the report.

This file is fully implemented and tested. Run it directly to see the demo.
"""

from collections import Counter

DIMENSIONS = [
    "numerical_accuracy",
    "materiality",
    "driver_attribution",
    "non_fabrication",
    "specificity",
]


def cohens_kappa(a, b):
    """Two equal-length sequences of labels. Returns kappa."""
    if len(a) != len(b):
        raise ValueError("label sequences must be the same length")
    n = len(a)
    if n == 0:
        raise ValueError("no items")

    observed = sum(x == y for x, y in zip(a, b)) / n

    ca, cb = Counter(a), Counter(b)
    categories = set(ca) | set(cb)
    expected = sum((ca[k] / n) * (cb[k] / n) for k in categories)

    if expected == 1.0:
        # Both labelers used exactly one category for everything. Kappa is
        # undefined here, and that itself is worth reporting.
        return float("nan")
    return (observed - expected) / (1 - expected)


def interpret(k):
    if k != k:  # NaN
        return "undefined (no label variance)"
    if k > 0.80:
        return "near-perfect"
    if k > 0.60:
        return "substantial"
    if k >= 0.40:
        return "moderate — tighten the weak dimensions"
    return "POOR — rubric too vague, revise before the main run"


def accepted(scores: dict) -> bool:
    """
    The FROZEN acceptance rule.

    Accepted only if numerical_accuracy AND non_fabrication both pass,
    plus at least 2 of {materiality, driver_attribution, specificity}.
    """
    if not (scores["numerical_accuracy"] and scores["non_fabrication"]):
        return False
    others = (
        scores["materiality"]
        + scores["driver_attribution"]
        + scores["specificity"]
    )
    return others >= 2


def kappa_by_dimension(labels_a: list, labels_b: list) -> dict:
    """
    labels_a / labels_b: lists of dicts, one per item, keyed by dimension.
    Returns kappa per dimension plus kappa on the overall accept decision.
    """
    out = {}
    for dim in DIMENSIONS:
        out[dim] = cohens_kappa(
            [x[dim] for x in labels_a],
            [x[dim] for x in labels_b],
        )
    out["OVERALL_ACCEPT"] = cohens_kappa(
        [accepted(x) for x in labels_a],
        [accepted(x) for x in labels_b],
    )
    return out


if __name__ == "__main__":
    # Demo with fake labels so you can see the shape of the output.
    import random

    random.seed(7)

    def fake(n, agreement):
        a, b = [], []
        for _ in range(n):
            item_a = {d: random.randint(0, 1) for d in DIMENSIONS}
            item_b = {
                d: item_a[d] if random.random() < agreement else 1 - item_a[d]
                for d in DIMENSIONS
            }
            a.append(item_a)
            b.append(item_b)
        return a, b

    A, B = fake(20, 0.85)
    print(f"{'dimension':<22} {'kappa':>7}   interpretation")
    print("-" * 62)
    for dim, k in kappa_by_dimension(A, B).items():
        print(f"{dim:<22} {k:>7.3f}   {interpret(k)}")
