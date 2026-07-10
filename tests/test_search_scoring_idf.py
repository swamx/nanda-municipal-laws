from app.search_scoring import score_chunk, score_chunks_idf

# Three candidate sections all coincidentally mention the generic word
# "party" (as in "a party to an action"), but only one is actually about the
# topic the query means - the same class of false positive documented in
# tests/test_is_action_allowed.py::test_known_limitation_coincidental_common_word_can_still_match.
_ON_TOPIC = {
    "section_number": "161.19",
    "section_title": "Keeping of livestock, live poultry and rabbits",
    "text": "No person shall keep a live rooster, duck, goose or turkey. A party to a dispute under this section may appeal.",
}
_OFF_TOPIC_A = {
    "section_number": "10-01",
    "section_title": "General provisions",
    "text": "Any party to an action under this code shall be given notice.",
}
_OFF_TOPIC_B = {
    "section_number": "10-02",
    "section_title": "Definitions",
    "text": "For purposes of this title, 'party' means a person named in a proceeding.",
}
_CANDIDATES = [_ON_TOPIC, _OFF_TOPIC_A, _OFF_TOPIC_B]


def test_flat_scorer_lets_a_shared_generic_word_score_comparably_to_the_real_match():
    scores = {doc["section_number"]: score_chunk(doc["section_title"], doc["text"], "party poultry") for doc in _CANDIDATES}
    # The on-topic section wins outright (it also matches "poultry"), but an
    # off-topic section scores non-trivially close purely on "party" - this is
    # the known, documented flat-scoring limitation, not a bug in score_chunk.
    assert scores["161.19"] > scores["10-01"] > 0


def test_idf_scorer_downweights_the_shared_generic_term():
    scored = score_chunks_idf(_CANDIDATES, "party poultry")
    by_section = {doc["section_number"]: score for score, doc in scored}

    # "party" appears in all three candidates, so its IDF weight collapses
    # toward zero - the on-topic section's real margin now comes almost
    # entirely from "poultry", which appears nowhere else in the set.
    assert by_section["161.19"] > by_section["10-01"]
    assert by_section["161.19"] > by_section["10-02"]

    flat_margin = score_chunk(_ON_TOPIC["section_title"], _ON_TOPIC["text"], "party poultry") - score_chunk(
        _OFF_TOPIC_A["section_title"], _OFF_TOPIC_A["text"], "party poultry"
    )
    idf_margin = by_section["161.19"] - by_section["10-01"]
    # The relative margin (as a fraction of the on-topic score) widens under
    # IDF weighting - "party" contributes less noise to the gap.
    assert (idf_margin / by_section["161.19"]) > (flat_margin / score_chunk(_ON_TOPIC["section_title"], _ON_TOPIC["text"], "party poultry"))


def test_idf_scorer_returns_zero_scores_unchanged_for_no_query_terms():
    assert score_chunks_idf(_CANDIDATES, "") == [(0.0, doc) for doc in _CANDIDATES]


def test_idf_scorer_handles_empty_candidate_list():
    assert score_chunks_idf([], "party poultry") == []
