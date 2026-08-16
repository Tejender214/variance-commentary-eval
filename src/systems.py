"""
The four systems. Days 24-26 Aug (week 2).

DO NOT WRITE THESE UNTIL hypothesis.md IS COMMITTED AND THE RUBRIC IS FROZEN.
The git ordering is the evidence that predictions preceded results.

  B0  numbers -> f-string template.  ZERO LLM. NO API CALL.
  B1  numbers -> LLM. No filing text.
  B2  numbers + retrieved MD&A -> LLM.   <- the main system
  B3  optional: B2 + self-critique.      <- first thing cut if time slips

Deltas are the product. B0->B1 = value of the LLM. B1->B2 = value of retrieval,
and that is the headline number.
"""


def b0_template(variance_record: dict) -> str:
    """
    Deterministic template. No model anywhere in this function.

    Passes numerical accuracy and non-fabrication BY CONSTRUCTION. Whether it
    clears the acceptance gate depends entirely on whether line-item ranking is
    good enough to pass materiality.

    If B0 scores above 40%, the honest headline of the report changes.
    """
    raise NotImplementedError


def b1_numbers_only(variance_record: dict, model: str) -> str:
    """LLM given ONLY the figures. No filing text. Isolates what the model
    knows vs what it is told."""
    raise NotImplementedError


def b2_rag(variance_record: dict, mdna_chunks: list, model: str) -> str:
    """LLM given figures + retrieved MD&A. The main system."""
    raise NotImplementedError


def instrument(fn):
    """
    TODO: wrap generation to record tokens in/out and wall-clock latency.

    The metric that matters is COST PER ACCEPTED OUTPUT, not cost per call —
    a cheap model that fails more often costs more per unit of usable work.
    Also record p50 and p95 latency.
    """
    raise NotImplementedError
