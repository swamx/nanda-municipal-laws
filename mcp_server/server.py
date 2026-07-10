"""MCP transport for the Municipal Law Skill.

A thin MCP wrapper over the same public HTTP contract documented in SKILL.md
- it does not reimplement any retrieval/action-evaluation logic, only calls
the deployed REST API (default: the live Vercel deployment; override with
MCP_API_BASE_URL for a local dev server). Local-only, like local_agent/: not
part of the deployed FastAPI app, excluded from the Vercel deployment via
.vercelignore.

Run with `python -m mcp_server.server` (stdio transport) and point an MCP
client (Claude Desktop, Claude Code, etc.) at it - see mcp_server/README.md.
"""

from mcp.server.fastmcp import FastMCP

from local_agent.api_client import ApiClient
from mcp_server.config import settings

mcp = FastMCP(
    name="municipal-law-skill",
    instructions=(
        "Deterministic, citation-backed NYC municipal law lookup (NYC Administrative Code + "
        "NYC Health Code, full corpus). This service never generates legal text - every tool "
        "returns real citations, verbatim snippets, and mechanical reasoning; you compose the "
        "final natural-language answer yourself. Call is_action_allowed first for any yes/no "
        "legality question ('can I...', 'is it legal to...'); fall back to search_municipal_law "
        "for anything else. Never repeat `allowed` as a legal conclusion without reading "
        "`reasoning` - it can be a weaker absence-of-restriction inference, not an explicit rule."
    ),
)

# Module-level so tests can monkeypatch it to an in-process TestClient-backed
# ApiClient instead of hitting the network - see mcp_server/tests/conftest.py.
_client = ApiClient(base_url=settings.api_base_url)


@mcp.tool()
def is_action_allowed(action: str, context: dict | None = None) -> dict:
    """Determine whether a described action is legal in NYC.

    Returns {allowed, conditions, citations, reasoning, confidence, provenance}.
    `allowed` is true/false only when an explicit prohibition/permission was
    found in the corpus; null ("unclear") when nothing relevant was found -
    never a guess from silence. Always read `reasoning` before repeating
    `allowed` as a legal conclusion.
    """
    return _client.is_action_allowed(action, context=context)


@mcp.tool()
def search_municipal_law(
    query: str,
    document_type: str | None = None,
    topic: str | None = None,
    agency: str | None = None,
    limit: int = 10,
) -> dict:
    """Deterministic keyword search over the entire ingested corpus (32 titles /
    4,781 sections of the Admin Code, plus all 36 articles / 501 sections of
    the Health Code). Use literal key terms, not a full sentence - this ranks
    by term frequency, not phrase meaning. Optionally restrict `document_type`
    to 'NYC Administrative Code' or 'NYC Health Code'.
    """
    filters: dict = {"limit": limit}
    if document_type:
        filters["document_type"] = document_type
    if topic:
        filters["topic"] = topic
    if agency:
        filters["agency"] = agency
    return _client.search(query, **filters)


@mcp.tool()
def get_section(section_number: str) -> dict:
    """Exact lookup by section number (e.g. '161.19' or '24-222') - full,
    untruncated text, metadata, and a deterministic structural_summary."""
    return _client.get_section(section_number)


@mcp.tool()
def get_related_sections(section_number: str) -> dict:
    """Resolve a section's own cross-references into their citations - a
    one-hop citation graph. A reference outside the ingested corpus is still
    listed, with resolved=false, not silently dropped."""
    return _client.get_related(section_number)


@mcp.tool()
def find_penalties(query: str | None = None, topic: str | None = None) -> dict:
    """Find sections flagged as mentioning a penalty/fine/violation - a
    keyword heuristic, not a legal certainty. Use for penalty-specific
    questions instead of a general search_municipal_law call."""
    params: dict = {}
    if query:
        params["query"] = query
    if topic:
        params["topic"] = topic
    return _client.penalties(**params)


@mcp.tool()
def find_permits(query: str | None = None, topic: str | None = None) -> dict:
    """Find sections flagged as mentioning a permit/license requirement - a
    keyword heuristic, not a legal certainty. Use for permit-specific
    questions instead of a general search_municipal_law call."""
    params: dict = {}
    if query:
        params["query"] = query
    if topic:
        params["topic"] = topic
    return _client.permits(**params)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
