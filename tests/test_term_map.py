from app.term_map import build_term_map, extract_query_terms


def test_extract_query_terms_drops_stopwords_and_dedupes_in_order():
    terms = extract_query_terms("The Rooster and the Poultry of the Rooster")
    assert terms == ["rooster", "poultry"]


def test_extract_query_terms_lowercases():
    assert extract_query_terms("ROOSTER") == ["rooster"]


def test_build_term_map_finds_word_boundary_matches_only():
    # "fine" must not match inside "defined" - the same class of bug this
    # project has fixed multiple times elsewhere (enrich.py, search_scoring.py).
    text = "As defined in section 4, a fine may be imposed."
    term_map, total = build_term_map(text, "fine")

    assert total == 1
    assert len(term_map["fine"]) == 1
    assert "<mark>fine</mark>" in term_map["fine"][0]["snippet"]


def test_build_term_map_finds_multiple_occurrences_of_the_same_term():
    text = "A rooster is a rooster. No rooster shall be kept."
    term_map, total = build_term_map(text, "rooster")

    assert total == 3
    assert len(term_map["rooster"]) == 3


def test_build_term_map_is_case_insensitive():
    text = "ROOSTER keeping is prohibited. A Rooster may not be kept."
    term_map, total = build_term_map(text, "rooster")

    assert total == 2


def test_build_term_map_returns_multiple_terms_in_query_order():
    text = "Keeping of livestock, live poultry and rabbits. No person shall keep a live rooster."
    term_map, total = build_term_map(text, "rooster poultry")

    assert list(term_map.keys()) == ["rooster", "poultry"]
    assert total == 2


def test_build_term_map_omits_terms_with_no_matches():
    text = "This section is about poultry."
    term_map, total = build_term_map(text, "poultry zebra")

    assert "zebra" not in term_map
    assert "poultry" in term_map
    assert total == 1


def test_build_term_map_returns_empty_map_when_nothing_matches():
    term_map, total = build_term_map("Some unrelated text.", "zebra")

    assert term_map == {}
    assert total == 0


def test_build_term_map_context_chars_bounds_the_snippet_and_adds_ellipsis():
    text = "x" * 200 + " rooster " + "y" * 200
    term_map, _ = build_term_map(text, "rooster", context_chars=10)

    snippet = term_map["rooster"][0]["snippet"]
    assert snippet.startswith("…")
    assert snippet.endswith("…")
    assert "<mark>rooster</mark>" in snippet
    # Bounded by context_chars on each side, not by the surrounding 400 x/y
    # characters - well under the unbounded length the full text would give.
    assert len(snippet) < 50


def test_build_term_map_no_ellipsis_when_match_is_near_text_boundaries():
    text = "rooster is prohibited"
    term_map, _ = build_term_map(text, "rooster", context_chars=80)

    snippet = term_map["rooster"][0]["snippet"]
    assert not snippet.startswith("…")


def test_build_term_map_start_end_offsets_are_correct():
    text = "No person shall keep a live rooster in the city."
    term_map, _ = build_term_map(text, "rooster")

    occ = term_map["rooster"][0]
    assert text[occ["start"] : occ["end"]] == "rooster"
