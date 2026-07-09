from app.action_rules import (
    classify_subsection,
    expand_query_with_synonyms,
    filter_specific_keywords,
    shares_keyword,
)


def test_classify_subsection_prohibition():
    text = "(a) No person shall keep a live rooster, duck, goose or turkey in the City of New York."
    assert classify_subsection(text) == "prohibition"


def test_classify_subsection_permission():
    text = "(b) A person who is authorized by applicable law to keep livestock shall keep the premises clean."
    assert classify_subsection(text) == "permission"


def test_classify_subsection_neutral():
    text = "(c) Definitions used in this section shall have the meanings set forth below."
    assert classify_subsection(text) == "neutral"


def test_shares_keyword_word_boundary_not_substring():
    # "fine" must not match inside "defined" - same class of bug fixed in
    # app/ingestion/enrich.py's mentions_penalty/mentions_permit.
    assert shares_keyword("as defined in the code", ["fine"]) is False
    assert shares_keyword("subject to a fine", ["fine"]) is True


def test_filter_specific_keywords_drops_generic_verbs():
    keywords = ["keep", "backyard", "chickens", "operate"]
    assert filter_specific_keywords(keywords) == ["backyard", "chickens"]


def test_expand_query_with_synonyms_bridges_chicken_to_poultry():
    expanded = expand_query_with_synonyms("Keep backyard chickens")
    assert expanded.startswith("Keep backyard chickens")
    assert "poultry" in expanded


def test_expand_query_with_synonyms_no_op_when_no_match():
    assert expand_query_with_synonyms("operate a food truck") == "operate a food truck"
