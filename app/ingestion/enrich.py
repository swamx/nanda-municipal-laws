import re

_WORD_RE = re.compile(r"\w+")
_STOPWORDS = {"the", "of", "a", "an", "and", "or", "in", "to", "for", "on", "by", "this", "such", "with"}

_CROSS_REF_RE = re.compile(r"§\s*(\d+[\-.]\d+)")

PENALTY_KEYWORDS = (
    "penalty",
    "penalties",
    "fine",
    "fined",
    "violation",
    "unlawful",
    "misdemeanor",
    "civil penalty",
    "punishable",
)

PERMIT_KEYWORDS = (
    "permit",
    "permits",
    "permitted",
    "license",
    "licensed",
    "authorization",
    "authorized",
)


def extract_keywords(section_title: str) -> list[str]:
    """Deterministic tokenization of the section title - no invented terms."""
    words = _WORD_RE.findall(section_title.lower())
    return [w for w in words if w not in _STOPWORDS]


def extract_cross_references(text: str, section_number: str) -> list[str]:
    """Section numbers mentioned within the body text via the '§' glyph, self-excluded.

    Deliberately requires '§' (not the word "section") to avoid false positives
    from prose referencing external, differently-numbered statutes (e.g. "section
    4 of the Multiple Dwelling Law") - a documented, honest limitation, not
    exhaustive cross-reference detection.
    """
    refs = []
    for match in _CROSS_REF_RE.finditer(text):
        ref = match.group(1)
        if ref != section_number and ref not in refs:
            refs.append(ref)
    return refs


def mentions_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Word-boundary keyword match - plain substring matching would flag e.g.
    "fine" as present inside "defined", a false positive that would undermine
    the whole point of a heuristic meant to be trustworthy.
    """
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(keyword)}\b", lowered) for keyword in keywords)


def enrich_chunk(section_number: str, section_title: str, text: str) -> dict:
    """Deterministic per-chunk metadata, purely a function of chunk content -
    independent of which loader (HTML admin code, PDF health code) produced it.
    """
    return {
        "jurisdiction": "New York City",
        "keywords": extract_keywords(section_title),
        "cross_references": extract_cross_references(text, section_number),
        "mentions_penalty": mentions_any(text, PENALTY_KEYWORDS),
        "mentions_permit": mentions_any(text, PERMIT_KEYWORDS),
        "effective_date": None,
        "repealed": False,
    }
