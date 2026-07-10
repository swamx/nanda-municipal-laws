from typing import Literal

from pydantic import BaseModel, Field

Endpoint = Literal["is_action_allowed", "search", "sections", "sections_related", "penalties", "permits"]


class RoutingDecision(BaseModel):
    """What the routing step decided to call, before any API request is made."""

    endpoint: Endpoint = Field(description="Which Municipal Law Skill endpoint to call.")
    query_or_action: str = Field(
        description=(
            "The CORE action or search terms only - e.g. 'keep backyard chickens', not "
            "'keep backyard chickens in Queens'. This text is used for literal keyword "
            "matching against statute text, so location names, addresses, and boroughs "
            "must NOT be included here: they don't appear in the corpus and can coincidentally "
            "match an unrelated section (e.g. 'Queens' matching a cemetery-law section that has "
            "nothing to do with the actual question). Put any such context in `context` instead."
        )
    )
    context: dict[str, str] | None = Field(
        default=None,
        description=(
            "Non-search-relevant context from the question (e.g. {'borough': 'Queens'}) - "
            "passed through to is_action_allowed's context field for the caller's own "
            "record-keeping. Per SKILL.md, this does not currently narrow the API's own "
            "determination, but keeping it out of query_or_action avoids polluting the "
            "keyword search with words that don't appear in the ingested statute text."
        ),
    )
    document_type: Literal["NYC Administrative Code", "NYC Health Code"] | None = Field(
        default=None,
        description="Optional document_type filter, only meaningful for the search endpoint.",
    )
    needs_full_text: bool = Field(
        default=False,
        description=(
            "Set true when the user is asking for the exact penalty amount/fine, the precise "
            "statutory wording, or an explicit 'document snippet'/quote - not just a general "
            "informational answer. Only meaningful for the search/penalties/permits endpoints, "
            "whose results are ranked snippets that can be truncated. When true, the agent will "
            "automatically follow up with a full-text lookup (GET /sections/{section_number}) "
            "on the top result before composing, instead of quoting a possibly-truncated snippet. "
            "is_action_allowed/sections/sections_related already return full text, so this has no "
            "effect for those endpoints."
        ),
    )
    reasoning: str = Field(description="Why this endpoint (and not another) was chosen.")


class SourceCitation(BaseModel):
    section: str
    url: str
    score: float | None = None


class AgentAnswer(BaseModel):
    """The final, agent-composed response - matches SKILL.md's documented
    '{answer, sources, reasoning}' contract exactly. Never has an `allowed`
    or `confidence` field of its own; those come from the API response and
    are folded into `answer`/`reasoning` by the composing step, per SKILL.md.
    """

    answer: str
    sources: list[SourceCitation]
    reasoning: str
