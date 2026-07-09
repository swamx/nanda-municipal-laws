import re

# Splits body text into one bullet per top-level lettered/numbered subsection
# (e.g. "(a)", "(b)", "(1)"), requiring the marker to follow a sentence
# boundary so mid-sentence parenthetical cross-references like "as authorized
# by §161.01 (a) of this Article" aren't mistaken for a new subsection.
_SUBSECTION_SPLIT_RE = re.compile(r"(?<=[.;]\s)(?=\([a-z0-9]+\)\s)")


def split_subsections(text: str) -> list[str]:
    parts = [p.strip() for p in _SUBSECTION_SPLIT_RE.split(text)]
    return [p for p in parts if p]
