import math
import re

_WORD_RE = re.compile(r"\w+")


def score_chunk(section_title: str, text: str, query: str) -> float:
    """Naive TF-based keyword score, weighting title matches above body matches.

    Used instead of MongoDB's native $text/textScore because the deployed
    Atlas user's role does not grant createIndex, so a server-side text index
    cannot be created. Fine at this dataset's scale (a few hundred chunks at
    most) to score candidates in Python after a plain equality find().

    Matches on word boundaries, not plain substrings - a real bug caught
    while ingesting the full corpus: naive `str.count()` matches "dance"
    inside "accordance" and "fine" inside "defined" (the same class of bug
    fixed in app/ingestion/enrich.py's mentions_penalty/mentions_permit).
    """
    words = _WORD_RE.findall(query.lower())
    title = section_title.lower()
    body = text.lower()
    score = 0.0
    for word in words:
        pattern = rf"\b{re.escape(word)}\b"
        score += len(re.findall(pattern, title)) * 5
        score += len(re.findall(pattern, body))
    return score


def score_chunks_idf(candidates: list[dict], query: str) -> list[tuple[float, dict]]:
    """IDF-weighted keyword scoring over one candidate set - a classical,
    deterministic information-retrieval technique (not a neural embedding or
    an LLM), used as an opt-in `search_mode="idf"` to reduce a documented
    false-positive class in score_chunk(): a query term that's generic enough
    to appear in nearly every candidate (e.g. "party" as in "a party to an
    action") contributes a flat +1 per hit there regardless of how common it
    is, letting a single shared common word rank an off-topic section highly.

    Here, each query term's weight is its inverse document frequency *within
    this candidate set*: a term present in most candidates approaches zero
    weight (it can't discriminate between them), while a term present in only
    one or two candidates gets a high weight, since it's the one actually
    distinguishing the true match from the crowd. Recomputed per query/filter
    combination (not a corpus-wide static index), so it stays deterministic
    and requires no offline model or training step.
    """
    words = _WORD_RE.findall(query.lower())
    if not words or not candidates:
        return [(0.0, doc) for doc in candidates]

    n = len(candidates)
    lowered = [(doc["section_title"].lower(), doc["text"].lower()) for doc in candidates]
    doc_freq = {word: 0 for word in set(words)}
    for title, body in lowered:
        for word in doc_freq:
            if re.search(rf"\b{re.escape(word)}\b", title) or re.search(rf"\b{re.escape(word)}\b", body):
                doc_freq[word] += 1

    # +1 smoothing avoids a divide-by-zero for an unmatched term; the small
    # +0.01 floor keeps a term found in literally every candidate from
    # contributing exactly zero (still ranked, just heavily discounted).
    idf = {word: math.log((n + 1) / (doc_freq[word] + 1)) + 0.01 for word in doc_freq}

    scored = []
    for doc, (title, body) in zip(candidates, lowered):
        score = 0.0
        for word in words:
            pattern = rf"\b{re.escape(word)}\b"
            hits = len(re.findall(pattern, title)) * 5 + len(re.findall(pattern, body))
            score += hits * idf[word]
        scored.append((score, doc))
    return scored
