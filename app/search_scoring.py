import re

_WORD_RE = re.compile(r"\w+")


def score_chunk(section_title: str, text: str, query: str) -> float:
    """Naive TF-based keyword score, weighting title matches above body matches.

    Used instead of MongoDB's native $text/textScore because the deployed
    Atlas user's role does not grant createIndex, so a server-side text index
    cannot be created. Fine at this dataset's scale (a few hundred chunks at
    most) to score candidates in Python after a plain equality find().
    """
    words = _WORD_RE.findall(query.lower())
    title = section_title.lower()
    body = text.lower()
    score = 0.0
    for word in words:
        score += title.count(word) * 5
        score += body.count(word)
    return score
