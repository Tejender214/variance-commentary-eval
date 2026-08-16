"""
MD&A location, extraction, chunking. Days 19-20 Aug.

The fiddliest part of the project. Budget a full day and accept "good enough" —
you need the right paragraphs retrievable, not perfect section boundaries.
Section headers vary, filing HTML varies by filer, some companies bury it.

CHUNK GRANULARITY IS AN EXPLICIT VARIABLE. Record whatever you pick. It is the
leading candidate for the week-3 targeted intervention (paragraph-level vs
larger sections), where you measure the delta it produces.
"""


def locate_mdna(submissions_json: dict, period: str) -> str:
    """TODO: find the 10-Q/10-K for the period, return the filing document URL."""
    raise NotImplementedError


def extract_mdna_text(filing_html: str) -> str:
    """TODO: strip to the MD&A section text."""
    raise NotImplementedError


def chunk(text: str, granularity: str = "paragraph") -> list:
    """TODO: split into retrievable chunks. Record granularity in run metadata."""
    raise NotImplementedError
