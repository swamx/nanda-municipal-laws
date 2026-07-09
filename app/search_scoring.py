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
