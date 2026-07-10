from .claude_cli import ask_structured
from .models import RoutingDecision
from .skill_context import load_skill_md

_ROUTING_SCHEMA = RoutingDecision.model_json_schema()

_SYSTEM_PROMPT_TEMPLATE = """You are the routing layer for an autonomous agent that uses the \
Municipal Law Skill described below. Given the user's question, decide exactly ONE API call \
to make and its parameters, following the skill's own "How to use this service" rules exactly \
(e.g. a yes/no legality question about a described action goes to is_action_allowed; a general \
lookup goes to search; a specific citation goes to sections; penalty/permit-specific questions \
go to penalties/permits). Do not answer the user's question yourself here - only decide the call.

IMPORTANT - keep `query_or_action` to the core action/search terms only. This is a KEYWORD \
search against real statute text, not natural language understanding, so words that don't \
appear in the corpus (borough names, addresses, "in my apartment", etc.) can coincidentally \
match an unrelated section and produce a misleading result (SKILL.md's own Rules section \
warns about exactly this). Put anything else the user mentioned into `context` instead.
Example: "Can I keep backyard chickens in Queens?" -> \
query_or_action="keep backyard chickens", context={{"borough": "Queens"}} \
(NOT query_or_action="keep backyard chickens in Queens").

IMPORTANT - set `needs_full_text=true` whenever the user asks for the exact penalty amount/fine, \
the precise statutory wording, or an explicit document snippet/quote - search/penalties/permits \
results are ranked snippets and can be truncated, so this triggers an automatic full-text \
follow-up lookup instead of quoting a cut-off snippet. Example: "what is the penalty for garbage \
not disposed correctly, give me document snippet as well" -> endpoint="penalties", \
needs_full_text=true.

--- SKILL.md ---
{skill_md}
"""


def decide_route(user_prompt: str, *, model: str | None = None) -> RoutingDecision:
    """Asks Claude Code (via the CLI, no separate API key) to pick which
    Municipal Law Skill endpoint answers `user_prompt`, following SKILL.md's
    own routing rules. Returns a pydantic-validated RoutingDecision - the CLI
    already validates its output against `_ROUTING_SCHEMA` via --json-schema,
    and this re-validates with pydantic as a second, independent check.
    """
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(skill_md=load_skill_md())
    raw = ask_structured(
        user_prompt,
        system_prompt=system_prompt,
        json_schema=_ROUTING_SCHEMA,
        model=model,
    )
    return RoutingDecision.model_validate(raw)
