import re

_WORD_RE = re.compile(r"\w+")
# Same stopword list as app/ingestion/enrich.py::extract_keywords - duplicated
# rather than cross-imported, matching this codebase's existing convention
# (_WORD_RE is already duplicated between search_scoring.py and enrich.py).
_STOPWORDS = {"the", "of", "a", "an", "and", "or", "in", "to", "for", "on", "by", "this", "such", "with"}


def extract_query_terms(query: str) -> list[str]:
    """Deterministic tokenization of a search query into distinct terms worth
    highlighting, in first-appearance order. Stopwords are dropped so a term
    map isn't cluttered with dozens of "the"/"of" hits in a legal text.
    """
    words = _WORD_RE.findall(query.lower())
    terms: list[str] = []
    for word in words:
        if word not in _STOPWORDS and word not in terms:
            terms.append(word)
    return terms


def _find_occurrences(text: str, term: str, context_chars: int) -> list[dict]:
    """Every word-boundary occurrence of `term` in `text`, each with a
    highlighted, context-bounded snippet. Word-boundary (not substring)
    matching - the same class of bug this project has fixed multiple times
    elsewhere (e.g. "fine" inside "defined") would otherwise flag irrelevant
    highlights here too.
    """
    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    occurrences = []
    for match in pattern.finditer(text):
        start, end = match.start(), match.end()
        ctx_start = max(0, start - context_chars)
        ctx_end = min(len(text), end + context_chars)
        prefix = "…" if ctx_start > 0 else ""
        suffix = "…" if ctx_end < len(text) else ""
        snippet = f"{prefix}{text[ctx_start:start]}<mark>{text[start:end]}</mark>{text[end:ctx_end]}{suffix}"
        occurrences.append({"start": start, "end": end, "snippet": snippet})
    return occurrences


def build_term_map(text: str, query: str, context_chars: int = 80) -> tuple[dict[str, list[dict]], int]:
    """Maps each distinct term in `query` to every place it occurs in `text`,
    each with an HTML `<mark>`-highlighted, context-bounded snippet - for
    rendering search-hit highlights on a demo/results page. Deterministic:
    the same text+query always produces the same map in the same order (the
    query's own word order), no ranking/scoring involved - this is a display
    aid, not another retrieval mode.
    """
    term_map: dict[str, list[dict]] = {}
    total = 0
    for term in extract_query_terms(query):
        occurrences = _find_occurrences(text, term, context_chars)
        if occurrences:
            term_map[term] = occurrences
            total += len(occurrences)
    return term_map, total
