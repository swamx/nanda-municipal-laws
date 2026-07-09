from typing import Literal

from pydantic import BaseModel, Field

Endpoint = Literal["is_action_allowed", "search", "sections", "sections_related", "penalties", "permits"]


class RoutingDecision(BaseModel):
    """What the routing step decided to call, before any API request is made."""

    endpoint: Endpoint = Field(description="Which Municipal Law Skill endpoint to call.")
    query_or_action: str = Field(
        description=(
            "The action text (for is_action_allowed), the search query (for "
            "search/penalties/permits), or the exact section_number (for "
            "sections/sections_related) to use as the call's primary parameter."
        )
    )
    document_type: Literal["NYC Administrative Code", "NYC Health Code"] | None = Field(
        default=None,
        description="Optional document_type filter, only meaningful for the search endpoint.",
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
