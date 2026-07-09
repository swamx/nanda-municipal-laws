import re
from typing import Literal

Classification = Literal["prohibition", "permission", "neutral"]

# Word-boundary matched, same approach as app/ingestion/enrich.py's
# mentions_penalty/mentions_permit heuristics (and for the same reason: naive
# substring matching produces false positives, e.g. "fine" inside "defined").
PROHIBITION_MARKERS = (
    "shall not",
    "shall be unlawful",
    "no person shall",
    "prohibited",
    "unlawful",
    "may not",
    "is banned",
)

PERMISSION_MARKERS = (
    "shall be lawful",
    "is permitted",
    "are permitted",
    "shall be permitted",
    "may be kept",
    "is authorized",
    "are authorized",
)


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(marker)}\b", lowered) for marker in markers)


def classify_subsection(text: str) -> Classification:
    """Deterministic keyword classification of one subsection's stance -
    NOT legal analysis. A subsection can contain both a prohibition and an
    exception clause in the same sentence (e.g. "no person shall ... except
    ..."); this only flags whether prohibitive language is *present*, it
    doesn't resolve exceptions - callers should read the actual text.
    """
    has_prohibition = _contains_any(text, PROHIBITION_MARKERS)
    has_permission = _contains_any(text, PERMISSION_MARKERS)

    if has_prohibition:
        return "prohibition"
    if has_permission:
        return "permission"
    return "neutral"


def shares_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in keywords)


# Generic regulatory verbs ("keep," "operate," "use"...) appear in nearly
# every subsection of nearly every section, so treating them as a qualifying
# keyword match produces false positives (e.g. "keep backyard chickens"
# matching an unrelated "Record Keeping" section purely on the word "keep").
# Excluded from shares_keyword() matching so a match requires a genuinely
# specific/topical word, not just a common verb.
GENERIC_ACTION_WORDS = frozenset(
    {
        "keep",
        "keeping",
        "operate",
        "operating",
        "use",
        "using",
        "maintain",
        "maintaining",
        "conduct",
        "conducting",
        "engage",
        "engaging",
        "perform",
        "performing",
        "action",
    }
)


def filter_specific_keywords(keywords: list[str]) -> list[str]:
    return [kw for kw in keywords if kw not in GENERIC_ACTION_WORDS]


# A small, explicitly curated list bridging a handful of common colloquial
# terms to the statutory vocabulary actually used in the ingested text - NOT
# a general thesaurus or NLU capability. Confirmed necessary empirically: the
# real §161.19 text never uses the word "chicken" (only "rooster," "duck,"
# "goose," "turkey," and "poultry" in the section title), so a literal query
# for "keep backyard chickens" fails to surface it at all via plain keyword
# search - it matches unrelated "Record Keeping" sections on the word "keep"
# instead. This list is intentionally tiny and topic-specific to what's been
# verified against real ingested text, not a stand-in for semantic search.
ACTION_QUERY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "chicken": ("poultry", "hen"),
    "chickens": ("poultry", "hens"),
    "hen": ("poultry",),
    "hens": ("poultry",),
    "rooster": ("poultry",),
    "roosters": ("poultry",),
}


def expand_query_with_synonyms(action: str) -> str:
    words = re.findall(r"\w+", action.lower())
    extra_terms: list[str] = []
    for word in words:
        for synonym in ACTION_QUERY_SYNONYMS.get(word, ()):
            if synonym not in extra_terms:
                extra_terms.append(synonym)
    if not extra_terms:
        return action
    return f"{action} {' '.join(extra_terms)}"
