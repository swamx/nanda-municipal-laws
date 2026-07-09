from app.ingestion.enrich import (
    enrich_chunk,
    extract_cross_references,
    extract_keywords,
    mentions_any,
)


def test_extract_keywords_tokenizes_and_drops_stopwords():
    keywords = extract_keywords("After hours and weekend limits on construction work")
    assert keywords == ["after", "hours", "weekend", "limits", "construction", "work"]


def test_extract_cross_references_finds_section_symbol_mentions_and_excludes_self():
    text = "As authorized by §161.01 (a) of this Article, and per §24-244 of the code."
    refs = extract_cross_references(text, section_number="161.19")
    assert refs == ["161.01", "24-244"]


def test_extract_cross_references_ignores_prose_without_section_symbol():
    text = "as defined in section 4 of the Multiple Dwelling Law, or other residence."
    refs = extract_cross_references(text, section_number="161.19")
    assert refs == []


def test_extract_cross_references_excludes_self_reference():
    text = "Nothing in §24-222 shall be construed to permit otherwise."
    refs = extract_cross_references(text, section_number="24-222")
    assert refs == []


def test_mentions_any_true_and_false():
    assert mentions_any("A violation of this code is punishable by a fine.", ("fine", "penalty")) is True
    assert mentions_any("No person shall keep a live rooster.", ("fine", "penalty")) is False


def test_mentions_any_requires_word_boundary_not_substring():
    # "fine" is a substring of "defined" - a real false positive caught when
    # ingesting the actual §161.19 text ("...as defined in section 4 of the
    # Multiple Dwelling Law..."), which must NOT count as mentioning a fine.
    text = "such dwelling as defined in section 4 of the Multiple Dwelling Law"
    assert mentions_any(text, ("fine", "fined")) is False


def test_enrich_chunk_shape():
    result = enrich_chunk("161.19", "Keeping of livestock, live poultry and rabbits.", "No person shall keep a live rooster.")
    assert result["jurisdiction"] == "New York City"
    assert "livestock" in result["keywords"]
    assert result["cross_references"] == []
    assert result["mentions_penalty"] is False
    assert result["mentions_permit"] is False
    assert result["effective_date"] is None
    assert result["repealed"] is False
