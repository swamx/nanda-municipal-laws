from pymongo.database import Database

from app.action_rules import (
    classify_subsection,
    expand_query_with_synonyms,
    filter_specific_keywords,
    shares_keyword,
)
from app.ingestion.enrich import extract_keywords
from app.models import ActionCheckResponse, ActionCitation, SearchResultItem
from app.retrieval import search_chunks
from app.section_lookup import get_section_chunks
from app.text_structure import split_subsections


def _relative_confidence(results: list[SearchResultItem]) -> str:
    """Confidence in *which section is the right one to check*, based on how
    decisively the top result outscored the runner-up - mode-agnostic, since
    text_index (MongoDB relevance units) and in_app (TF*5) scores aren't on
    comparable absolute scales, but "clearly ahead of the next-best match" is.
    """
    if len(results) == 1:
        return "high"
    top_score, second_score = results[0].score, results[1].score
    if second_score <= 0 or top_score >= second_score * 1.5:
        return "high"
    return "medium"


def evaluate_action(db: Database, action: str, limit: int = 5) -> ActionCheckResponse:
    """Deterministic, rule-based (not LLM) determination of whether the
    ingested corpus contains an explicit statement about `action`.

    Never forces a true/false guess from silence: `allowed` is only true or
    false when a keyword-matched prohibition or permission statement was
    actually found in the closest-matching section's text. Otherwise it's
    `null` ("unclear") or a lower-confidence absence-of-restriction inference
    - the corpus not mentioning something is not proof it's legal.
    """
    action_keywords = filter_specific_keywords(extract_keywords(action))
    # Search on the specific keywords only, not the raw sentence: generic
    # regulatory verbs ("keep," "operate"...) are common enough across the
    # corpus that including them in the query let a "Permits to keep certain
    # animals" section outrank the actually-relevant one for "keep a rooster"
    # purely on the word "keep" - a real ranking failure caught while testing.
    search_query = " ".join(action_keywords) if action_keywords else action
    expanded_query = expand_query_with_synonyms(search_query)
    results, _ = search_chunks(db, query=expanded_query, limit=limit)

    if not results or results[0].score <= 0:
        return ActionCheckResponse(
            action=action,
            allowed=None,
            conditions=[],
            citations=[],
            reasoning=(
                f"No section in the ingested corpus matched the terms in {action!r}. This does "
                "not mean the action is legal - it means no relevant provision was found to "
                "check it against."
            ),
            confidence="low",
        )

    top = results[0]
    chunks = get_section_chunks(db, top.section_number)
    full_text = " ".join(c["text"] for c in chunks)
    subsections = split_subsections(full_text)

    matched_prohibitions: list[str] = []
    matched_permissions: list[str] = []
    unrelated_prohibitions: list[str] = []

    for sub in subsections:
        classification = classify_subsection(sub)
        matches_action = shares_keyword(sub, action_keywords)
        if classification == "prohibition":
            (matched_prohibitions if matches_action else unrelated_prohibitions).append(sub)
        elif classification == "permission" and matches_action:
            matched_permissions.append(sub)

    citation = ActionCitation(
        section_number=top.section_number,
        section_title=top.section_title,
        url=top.url,
        document_type=top.document_type,
        matched_text=top.snippet,
    )

    if matched_prohibitions:
        return ActionCheckResponse(
            action=action,
            allowed=False,
            conditions=unrelated_prohibitions,
            citations=[citation],
            reasoning=(
                f"§{top.section_number} contains an explicit prohibition matching keywords in "
                f"the requested action: {matched_prohibitions[0]!r}"
            ),
            confidence=_relative_confidence(results),
        )

    if matched_permissions:
        return ActionCheckResponse(
            action=action,
            allowed=True,
            conditions=unrelated_prohibitions,
            citations=[citation],
            reasoning=(
                f"§{top.section_number} contains an explicit permission matching keywords in "
                f"the requested action: {matched_permissions[0]!r}"
            ),
            confidence=_relative_confidence(results),
        )

    # No explicit statement either way for the action's own subject in the
    # closest-matching section. Absence of a prohibition is a materially
    # weaker signal than an affirmative permission, so this is capped at
    # "medium" regardless of how decisive the search match was, and any
    # unrelated prohibitions found in the same section are surfaced as
    # conditions worth reading rather than silently dropped.
    return ActionCheckResponse(
        action=action,
        allowed=True,
        conditions=unrelated_prohibitions,
        citations=[citation],
        reasoning=(
            f"§{top.section_number} is the closest-matching provision, but contains no explicit "
            "prohibition or permission statement matching keywords in the requested action - "
            "this is an absence-of-restriction inference, not an affirmative statement. Read the "
            "full section text before relying on it."
        ),
        confidence="medium",
    )
