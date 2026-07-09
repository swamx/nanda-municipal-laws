def test_is_action_allowed_against_the_real_app(api_client):
    result = api_client.is_action_allowed("Keep backyard chickens")

    assert result["allowed"] is True
    assert result["citations"][0]["section_number"] == "161.19"


def test_search_against_the_real_app(api_client):
    result = api_client.search("rooster keeping poultry", document_type="NYC Health Code")

    assert result["results"][0]["section_number"] == "161.19"


def test_get_section_against_the_real_app(api_client):
    result = api_client.get_section("161.19")

    assert result["section_title"] == "Keeping of livestock, live poultry and rabbits"
    assert "161.01" in result["cross_references"]


def test_get_related_against_the_real_app(api_client):
    result = api_client.get_related("161.19")

    resolved = [r for r in result["related"] if r["section_number"] == "161.01"]
    assert resolved and resolved[0]["resolved"] is True


def test_permits_against_the_real_app(api_client):
    result = api_client.permits(query="keep certain animals")

    assert any(r["section_number"] == "161.09" for r in result["results"])


def test_penalties_against_the_real_app_returns_shape_even_when_empty(api_client):
    result = api_client.penalties(topic="ANIMALS")

    assert "results" in result
    assert "reasoning" in result
