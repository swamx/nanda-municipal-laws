from mcp_server.server import (
    find_penalties,
    find_permits,
    get_related_sections,
    get_section,
    is_action_allowed,
    search_municipal_law,
)


def test_is_action_allowed_tool():
    result = is_action_allowed("Keep backyard chickens")

    assert result["allowed"] is True
    assert result["citations"][0]["section_number"] == "161.19"
    assert result["provenance"]["algorithm"] == "ed25519"


def test_search_municipal_law_tool():
    result = search_municipal_law("rooster keeping poultry", document_type="NYC Health Code")

    assert result["results"][0]["section_number"] == "161.19"


def test_get_section_tool():
    result = get_section("161.19")

    assert result["section_title"] == "Keeping of livestock, live poultry and rabbits"
    assert "161.01" in result["cross_references"]


def test_get_related_sections_tool():
    result = get_related_sections("161.19")

    resolved = [r for r in result["related"] if r["section_number"] == "161.01"]
    assert resolved and resolved[0]["resolved"] is True


def test_find_permits_tool():
    result = find_permits(query="keep certain animals")

    assert any(r["section_number"] == "161.09" for r in result["results"])


def test_find_penalties_tool_returns_shape_even_when_empty():
    result = find_penalties(topic="ANIMALS")

    assert "results" in result
    assert "reasoning" in result
